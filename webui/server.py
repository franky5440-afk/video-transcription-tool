#!/usr/bin/env python3
"""
Local Web UI Server

A thin Flask layer on top of the existing feature modules. It exposes the two
workflows the tool is actually used for:

    video : download -> transcribe -> translate -> format -> embed
    text  : download -> transcribe -> translate -> format   (no embed)

Design constraints implemented here:

    C1: POST /api/jobs returns immediately; the work runs in a background thread
    C2: only one job at a time; a second request while one runs gets 409
    C3: no percentage progress is reported (whisper has no progress callback),
        only per-step status
    C4: every job writes into output/webui/<job_id>/ so the fixed filenames the
        feature modules use cannot collide between jobs
    C5: a failing step is marked "error", the job is marked "error", and the
        steps after it stay "pending"

    S1: the server only ever binds 127.0.0.1; this service reads local file
        paths given by the client, so it must not be reachable from the LAN
    S2: /api/files/ resolves the requested path with os.path.realpath and
        serves it only when it really is inside that job's output directory
    S3: no debug mode, no reloader
"""

import os
import threading
import time
import uuid
import webbrowser
from urllib.parse import quote
from urllib.request import urlopen

from flask import Flask, jsonify, request, send_file
from werkzeug.serving import make_server

from youtube_downloader import download_youtube_video
from transcription_service import transcribe_video, parse_srt_to_text
from translation_service import translate_transcription
from language_detect import is_traditional_chinese
from output_formatter import format_to_markdown, save_to_markdown_file
from video_processor import process_video_with_subtitles
from main import create_srt_from_transcription

HOST = "127.0.0.1"  # S1: localhost only, never configurable

WORKFLOW_STEPS = {
    "video": ["download", "transcribe", "translate", "format", "embed"],
    "text": ["download", "transcribe", "translate", "format"],
}

app = Flask(__name__)

# Module constant: the test suite references it, so it must not be a bare
# string literal embedded only inside _is_our_server().
OUR_TITLE_MARKER = "<title>影片轉錄工具</title>"

_lock = threading.Lock()
_jobs = {}
_active_job_id = None

# Base directory for job output, matching the --output default of the other
# subcommands. serve() replaces it with whatever --output was given.
_output_base = "./output"


def _output_root() -> str:
    return os.path.abspath(os.path.join(_output_base, "webui"))


def _set_step(job: dict, name: str, status: str, detail: str = "") -> None:
    with _lock:
        for step in job["steps"]:
            if step["name"] == name:
                step["status"] = status
                step["detail"] = detail
                return


def _add_output(job: dict, label: str, path: str) -> None:
    filename = os.path.basename(path)
    with _lock:
        job["outputs"].append({
            "label": label,
            "filename": filename,
            "url": f"/api/files/{job['job_id']}/{quote(filename)}",
            "bytes": os.path.getsize(path),
        })


def _fail(job: dict, step_name: str, message: str) -> None:
    """C5: mark the failing step, mark the job, leave later steps pending."""
    _set_step(job, step_name, "error", message)
    with _lock:
        job["status"] = "error"
        job["error"] = message
        job["finished_at"] = time.time()


def _public(job: dict) -> dict:
    """Serialise exactly the keys the interface contract lists."""
    with _lock:
        return {
            "job_id": job["job_id"],
            "workflow": job["workflow"],
            "source": job["source"],
            "status": job["status"],
            "started_at": job["started_at"],
            "finished_at": job["finished_at"],
            "steps": [dict(step) for step in job["steps"]],
            "outputs": [dict(item) for item in job["outputs"]],
            "error": job["error"],
            "source_removed": job["source_removed"],
        }


def _run_job(job: dict) -> None:
    job_dir = job["dir"]
    source = job["source"]

    try:
        # --- download -------------------------------------------------------
        if source.startswith(("http://", "https://")):
            _set_step(job, "download", "running")
            video_file = download_youtube_video(source, job_dir)
            if not video_file:
                _fail(job, "download", f"failed to download video: {source}")
                return
            _set_step(job, "download", "done", os.path.basename(video_file))
        else:
            # transcribe_video writes its SRT next to the video file, so link
            # the local source into the job directory: everything the feature
            # modules produce then stays inside output/webui/<job_id>/ (C4)
            # and nothing is written next to the user's own file.
            video_file = os.path.join(job_dir, os.path.basename(source))
            os.symlink(os.path.abspath(source), video_file)
            _set_step(job, "download", "skipped", "本機檔案，無需下載")

        # --- transcribe -----------------------------------------------------
        _set_step(job, "transcribe", "running")
        srt_file = transcribe_video(video_file)
        if not srt_file:
            _fail(job, "transcribe", f"transcription failed: {os.path.basename(video_file)}")
            return
        _add_output(job, "原文 SRT", srt_file)
        _set_step(job, "transcribe", "done", os.path.basename(srt_file))

        # --- translate ------------------------------------------------------
        _set_step(job, "translate", "running")
        original_text = parse_srt_to_text(srt_file)
        if not original_text:
            _fail(job, "translate", "could not parse the transcription")
            return
        # A Chinese source is already transcribed as Traditional Chinese, so the
        # translator has nothing to translate and rewrites it instead: measured
        # 2026-08-05, 519 of 850 lines came back altered, including outright
        # meaning changes. Skipping also drops the slowest step of the run.
        already_chinese = is_traditional_chinese(original_text)
        if already_chinese:
            translated_text = original_text
        else:
            translated_text = translate_transcription(original_text)
            if not translated_text:
                _fail(job, "translate", "translation failed")
                return

        # Written either way: the embed step burns this file into the video, and
        # when the source is already Chinese those are the subtitles we want.
        translated_srt = os.path.join(job_dir, "transcription_translated.srt")
        if not create_srt_from_transcription(translated_text, translated_srt):
            _fail(job, "translate", "could not generate the translated SRT file")
            return

        if already_chinese:
            # Not listed as an output: it is a byte-for-byte copy of the
            # transcript, and offering it as a "translation" would be a lie.
            _set_step(job, "translate", "skipped",
                      "來源已是繁體中文，直接使用原文")
        else:
            _add_output(job, "翻譯 SRT", translated_srt)
            _set_step(job, "translate", "done", os.path.basename(translated_srt))

        # --- format ---------------------------------------------------------
        _set_step(job, "format", "running")
        translated_markdown, original_markdown = format_to_markdown(
            translated_text, original_text, os.path.basename(video_file))
        if not translated_markdown or not original_markdown:
            _fail(job, "format", "could not format the transcription")
            return
        saved = save_to_markdown_file(translated_markdown, original_markdown, job_dir)
        if not saved[0] or not saved[1]:
            _fail(job, "format", "could not save the markdown files")
            return
        if already_chinese:
            # Same reasoning as the translated SRT above: it duplicates the
            # transcript, so only the original is offered.
            _add_output(job, "原文 Markdown", saved[1])
            _set_step(job, "format", "done", os.path.basename(saved[1]))
        else:
            _add_output(job, "翻譯 Markdown", saved[0])
            _add_output(job, "原文 Markdown", saved[1])
            _set_step(job, "format", "done", f"{os.path.basename(saved[0])}, {os.path.basename(saved[1])}")

        # --- embed (video workflow only) ------------------------------------
        if job["workflow"] == "video":
            _set_step(job, "embed", "running")
            subtitled_video, _ = process_video_with_subtitles(video_file, translated_srt, job_dir)
            if not subtitled_video:
                _fail(job, "embed", "could not embed subtitles")
                return
            _add_output(job, "字幕影片", subtitled_video)
            _set_step(job, "embed", "done", os.path.basename(subtitled_video))

        # --- post-success cleanup ---------------------------------------------
        # P1-4 (handoff 2026-08-05): a Chinese source leaves byte-for-byte
        # copies of the transcript behind (transcription_translated.*). They are
        # not listed as outputs on purpose, so delete them now that nothing needs
        # them anymore (the video workflow's embed step already ran).
        if already_chinese:
            for name in ("transcription_translated.srt", "transcription_translated.md"):
                try:
                    os.remove(os.path.join(job_dir, name))
                except OSError:
                    pass

        # P1-3 (handoff 2026-08-05): a text workflow only needs the words, not
        # the video. Delete the copy we downloaded, but never the user's own
        # local file: that one lives in the job dir as a symlink (download was
        # "skipped"), and deleting it would destroy the user's source.
        if job["workflow"] == "text":
            download_step = next((s for s in job["steps"] if s["name"] == "download"), None)
            if download_step and download_step["status"] == "done" and not os.path.islink(video_file):
                try:
                    os.remove(video_file)
                except OSError:
                    pass
                else:
                    with _lock:
                        job["source_removed"] = True

        with _lock:
            job["status"] = "done"
            job["finished_at"] = time.time()

    except Exception as exc:  # keep the worker thread from dying silently
        running = [s["name"] for s in job["steps"] if s["status"] == "running"]
        _fail(job, running[0] if running else job["steps"][0]["name"], f"unexpected error: {exc}")


@app.get("/")
def index():
    index_file = os.path.join(app.static_folder, "index.html")
    if os.path.isfile(index_file):
        return send_file(index_file)
    return (
        "webui/static/index.html is not present yet.\n"
        "The backend is running; the API is available under /api/.\n",
        200,
        {"Content-Type": "text/plain; charset=utf-8"},
    )


@app.get("/api/health")
def health():
    return jsonify({"ok": True})


@app.post("/api/jobs")
def create_job():
    global _active_job_id

    # Content-Type: application/json is required on purpose: a cross-origin
    # HTML form cannot send it, so a random web page open in the same browser
    # cannot start jobs on this server.
    data = request.get_json(silent=True) or {}
    workflow = data.get("workflow")
    source = (data.get("source") or "").strip()

    if workflow not in WORKFLOW_STEPS:
        return jsonify({"error": "workflow must be 'video' or 'text'"}), 400
    if not source:
        return jsonify({"error": "source is required"}), 400
    if not source.startswith(("http://", "https://")) and not os.path.exists(source):
        return jsonify({"error": f"local video file not found: {source}"}), 400

    with _lock:
        if _active_job_id is not None and _jobs[_active_job_id]["status"] == "running":
            return jsonify({"error": "another job is already running"}), 409

        job_id = str(uuid.uuid4())
        job = {
            "job_id": job_id,
            "workflow": workflow,
            "source": source,
            "status": "running",
            "started_at": time.time(),
            "finished_at": None,
            "steps": [{"name": name, "status": "pending", "detail": ""}
                      for name in WORKFLOW_STEPS[workflow]],
            "outputs": [],
            "error": None,
            "source_removed": False,
            "dir": os.path.join(_output_root(), job_id),
        }
        _jobs[job_id] = job
        _active_job_id = job_id

    os.makedirs(job["dir"], exist_ok=True)
    threading.Thread(target=_run_job, args=(job,), daemon=True).start()
    return jsonify({"job_id": job_id}), 201


@app.get("/api/jobs/<job_id>")
def get_job(job_id):
    with _lock:
        job = _jobs.get(job_id)
    if job is None:
        return jsonify({"error": "job not found"}), 404
    return jsonify(_public(job))


@app.get("/api/files/<job_id>/<path:filename>")
def get_file(job_id, filename):
    with _lock:
        job = _jobs.get(job_id)
    if job is None:
        return jsonify({"error": "job not found"}), 404

    # S2: containment is decided by the resolved absolute path, not by
    # inspecting the request string, so symlinks and encodings cannot escape.
    job_dir = os.path.realpath(job["dir"])
    target = os.path.realpath(os.path.join(job_dir, filename))
    if target != job_dir and not target.startswith(job_dir + os.sep):
        return jsonify({"error": "file not found"}), 404
    if not os.path.isfile(target):
        return jsonify({"error": "file not found"}), 404

    return send_file(target, as_attachment=True)


def _is_our_server(port: int, timeout: float = 2.0) -> bool:
    """在 127.0.0.1:<port> 上的，是不是已經在跑的本工具 web UI。

    只有明確證實時才回 True（E4）。任何錯誤、逾時、無法判定一律回 False（E7）。
    本函式不得拋出例外。
    """
    try:
        with urlopen(f"http://{HOST}:{port}/", timeout=timeout) as resp:
            if resp.status != 200:
                return False
            body = resp.read().decode("utf-8", errors="ignore")
            return OUR_TITLE_MARKER in body
    except Exception:
        return False


def serve(port: int, open_browser: bool = True, output: str = "./output") -> None:
    """
    Run the web UI server until interrupted.

    Job output goes to <output>/webui/<job_id>/, so --output means the same
    thing here as in the other subcommands.

    When the port cannot be bound, make_server prints the reason on stderr and
    exits with status 1 (verified for both "address already in use" and
    "permission denied"); the server never falls back to another port.
    """
    global _output_base
    _output_base = output
    if _is_our_server(port):
        url = f"http://{HOST}:{port}/"
        print(f"Web UI is already running on {url}")
        if open_browser:
            webbrowser.open(url)
        return
    # S1/S3: bound to 127.0.0.1, no debug mode, no reloader.
    server = make_server(HOST, port, app, threaded=True)
    url = f"http://{HOST}:{port}/"
    print(f"Web UI listening on {url}")
    print("Press Ctrl+C to stop.")
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopping.")
        server.shutdown()
