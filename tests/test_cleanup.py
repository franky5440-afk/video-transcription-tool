#!/usr/bin/env python3
"""
Test the post-success cleanup logic in webui.server (handoff P1-3 / P1-4).

P1-3: a text workflow deletes the video we downloaded, but never the user's own
      local file (that one is a symlink and must stay).
P1-4: when a source is already Traditional Chinese, the byte-for-byte copies
      transcription_translated.{srt,md} are deleted.

Freezes every feature module so no network, whisper run, or ffmpeg embeds fire;
only webui.server._run_job + real filesystem are exercised. Each test builds a
real job dict (same shape create_job() uses) and calls _run_job() for real.
"""

import os
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import webui.server as server_mod


def _job(workflow, source, job_dir, *step_names):
    return {
        "job_id": "test-job",
        "workflow": workflow,
        "source": source,
        "status": "running",
        "started_at": 0,
        "finished_at": None,
        "steps": [{"name": n, "status": "pending", "detail": ""} for n in step_names],
        "outputs": [],
        "error": None,
        "source_removed": False,
        "dir": job_dir,
    }


def _open_ok(_text, path):
    with open(path, "w", encoding="utf-8") as f:
        f.write("x")
    return True


def _transcribe_srt(job_dir):
    """Fake transcribe_video: drop a real SRT file in the job dir so the
    server's _add_output (which stats each file) has something to see."""
    path = os.path.join(job_dir, "video.srt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("1\n00:00:00,000 --> 00:00:01,000\nx\n\n")
    return path


def _make_video(job_dir):
    path = os.path.join(job_dir, "out.mp4")
    with open(path, "w") as f:
        f.write("video")
    return path, None


def _fake_save(tmd, omd, out_dir):
    tp = os.path.join(out_dir, "transcription_translated.md")
    op = os.path.join(out_dir, "transcription_original.md")
    for p, c in ((tp, tmd), (op, omd)):
        with open(p, "w", encoding="utf-8") as f:
            f.write(c)
    return tp, op


def test_text_downloaded_chinese_deletes_video_and_fake_translation():
    """① text workflow, yt-dlp source, Chinese: downloaded video removed,
    transcription_translated.* removed, original transcripts retained."""
    print("\n=== ① text + downloaded + Chinese -> video & fake translation gone ===")
    with tempfile.TemporaryDirectory(prefix="cleanup_") as td:
        job_dir = os.path.join(td, "out")
        os.makedirs(job_dir)
        video = os.path.join(job_dir, "downloaded.webm")
        with open(video, "w") as f:
            f.write("video")
        job = _job("text", "https://youtu.be/x", job_dir, "download", "transcribe",
                   "translate", "format")
        with patch.object(server_mod, "download_youtube_video", return_value=video), \
             patch.object(server_mod, "transcribe_video", lambda _vf: _transcribe_srt(job_dir)), \
             patch.object(server_mod, "parse_srt_to_text", return_value="中文測試此處"), \
             patch.object(server_mod, "is_traditional_chinese", return_value=True), \
             patch.object(server_mod, "create_srt_from_transcription", _open_ok), \
             patch.object(server_mod, "format_to_markdown",
                          return_value=("tmd", "omd")), \
             patch.object(server_mod, "save_to_markdown_file", _fake_save):
            server_mod._run_job(job)

        print("status:", job["status"], "source_removed:", job["source_removed"])
        print("video exists:", os.path.exists(video))
        print("translated.srt:", os.path.exists(os.path.join(job_dir, "transcription_translated.srt")))
        print("translated.md:", os.path.exists(os.path.join(job_dir, "transcription_translated.md")))
        print("original.srt:", os.path.exists(os.path.join(job_dir, "video.srt")))
        print("original.md:", os.path.exists(os.path.join(job_dir, "transcription_original.md")))

        if job["status"] != "done":
            print("FAIL: job did not finish done")
            return False
        if not job["source_removed"]:
            print("FAIL: downloaded video should have been flagged source_removed")
            return False
        if os.path.exists(video):
            print("FAIL: downloaded video must be deleted")
            return False
        if os.path.exists(os.path.join(job_dir, "transcription_translated.srt")):
            print("FAIL: translated SRT copy must be deleted for Chinese source")
            return False
        if os.path.exists(os.path.join(job_dir, "transcription_translated.md")):
            print("FAIL: translated MD copy must be deleted for Chinese source")
            return False
        if not os.path.exists(os.path.join(job_dir, "video.srt")) or \
           not os.path.exists(os.path.join(job_dir, "transcription_original.md")):
            print("FAIL: original transcripts must be retained")
            return False
        print("PASS")
        return True


def test_text_local_source_keeps_symlink_and_original():
    """② text workflow, user's local file: the symlink and the real source stay."""
    print("\n=== ② text + local file -> source & symlink kept ===")
    with tempfile.TemporaryDirectory(prefix="cleanup_") as td:
        src = os.path.join(td, "my_video.mp4")
        with open(src, "w") as f:
            f.write("user video")
        job_dir = os.path.join(td, "out")
        os.makedirs(job_dir)
        job = _job("text", src, job_dir, "download", "transcribe", "translate",
                   "format")
        with patch.object(server_mod, "download_youtube_video",
                          return_value=None), \
             patch.object(server_mod, "transcribe_video", lambda _vf: _transcribe_srt(job_dir)), \
             patch.object(server_mod, "parse_srt_to_text", return_value="abc"), \
             patch.object(server_mod, "is_traditional_chinese", return_value=False), \
             patch.object(server_mod, "translate_transcription",
                          return_value="translated"), \
             patch.object(server_mod, "create_srt_from_transcription", _open_ok), \
             patch.object(server_mod, "format_to_markdown",
                          return_value=("tmd", "omd")), \
             patch.object(server_mod, "save_to_markdown_file", _fake_save):
            server_mod._run_job(job)

        link = os.path.join(job_dir, os.path.basename(src))
        print("status:", job["status"])
        print("symlink exists:", os.path.islink(link))
        print("original exists:", os.path.exists(src))
        print("source_removed:", job["source_removed"])

        if not os.path.exists(src):
            print("FAIL: user's original file must NEVER be deleted")
            return False
        if not os.path.islink(link):
            print("FAIL: the symlink in the job dir should remain untouched")
            return False
        if job["source_removed"]:
            print("FAIL: local source must not be flagged as removed")
            return False
        print("PASS")
        return True


def test_video_workflow_keeps_source():
    """③ video workflow: the source video is NOT deleted (embed already used it
    and the handoff says video workflow never deletes)."""
    print("\n=== ③ video workflow -> source video kept ===")
    with tempfile.TemporaryDirectory(prefix="cleanup_") as td:
        job_dir = os.path.join(td, "out")
        os.makedirs(job_dir)
        video = os.path.join(job_dir, "downloaded.webm")
        with open(video, "w") as f:
            f.write("video")
        job = _job("video", "https://youtu.be/x", job_dir, "download", "transcribe",
                   "translate", "format", "embed")
        with patch.object(server_mod, "download_youtube_video", return_value=video), \
             patch.object(server_mod, "transcribe_video", lambda _vf: _transcribe_srt(job_dir)), \
             patch.object(server_mod, "parse_srt_to_text", return_value="abc"), \
             patch.object(server_mod, "is_traditional_chinese", return_value=False), \
             patch.object(server_mod, "translate_transcription",
                          return_value="translated"), \
             patch.object(server_mod, "create_srt_from_transcription", _open_ok), \
             patch.object(server_mod, "format_to_markdown",
                          return_value=("tmd", "omd")), \
             patch.object(server_mod, "save_to_markdown_file", _fake_save), \
             patch.object(server_mod, "process_video_with_subtitles",
                          lambda _v, _s, _d: _make_video(job_dir)):
            server_mod._run_job(job)

        print("status:", job["status"], "source_removed:", job["source_removed"])
        print("video exists:", os.path.exists(video))
        print("labels:", [o["label"] for o in job["outputs"]])
        if not os.path.exists(video):
            print("FAIL: video workflow must not delete the source")
            return False
        if job["source_removed"]:
            print("FAIL: source_removed must be False for video workflow")
            return False
        print("PASS")
        return True


def test_non_chinese_keeps_translated_files():
    """P1-4 ② non-Chinese source: real translation must be kept and listed."""
    print("\n=== ④ non-Chinese -> translation kept & listed ===")
    with tempfile.TemporaryDirectory(prefix="cleanup_") as td:
        job_dir = os.path.join(td, "out")
        os.makedirs(job_dir)
        video = os.path.join(job_dir, "downloaded.webm")
        with open(video, "w") as f:
            f.write("video")
        job = _job("text", "https://youtu.be/x", job_dir, "download", "transcribe",
                   "translate", "format")
        with patch.object(server_mod, "download_youtube_video", return_value=video), \
             patch.object(server_mod, "transcribe_video", lambda _vf: _transcribe_srt(job_dir)), \
             patch.object(server_mod, "parse_srt_to_text", return_value="english"), \
             patch.object(server_mod, "is_traditional_chinese", return_value=False), \
             patch.object(server_mod, "translate_transcription",
                          return_value="translated"), \
             patch.object(server_mod, "create_srt_from_transcription", _open_ok), \
             patch.object(server_mod, "format_to_markdown",
                          return_value=("tmd", "omd")), \
             patch.object(server_mod, "save_to_markdown_file", _fake_save):
            server_mod._run_job(job)

        labels = [o["label"] for o in job["outputs"]]
        print("status:", job["status"])
        print("translated.srt exists:", os.path.exists(os.path.join(job_dir, "transcription_translated.srt")))
        print("translated.md exists:", os.path.exists(os.path.join(job_dir, "transcription_translated.md")))
        print("labels:", labels)
        if not os.path.exists(os.path.join(job_dir, "transcription_translated.srt")):
            print("FAIL: real translation SRT must be kept for non-Chinese source")
            return False
        if not os.path.exists(os.path.join(job_dir, "transcription_translated.md")):
            print("FAIL: real translation MD must be kept for non-Chinese source")
            return False
        if "翻譯 SRT" not in labels or "翻譯 Markdown" not in labels:
            print("FAIL: UI must list the translated outputs")
            return False
        print("PASS")
        return True


def main():
    print("Starting P1-3 / P1-4 cleanup verification...")
    tests = [
        test_text_downloaded_chinese_deletes_video_and_fake_translation,
        test_text_local_source_keeps_symlink_and_original,
        test_video_workflow_keeps_source,
        test_non_chinese_keeps_translated_files,
    ]
    passed, failed, not_tested = [], [], []
    for test in tests:
        try:
            result = test()
        except Exception as e:
            import traceback
            traceback.print_exc()
            result = False
        if result == "NOT_TESTED":
            not_tested.append(test.__name__)
        elif result:
            passed.append(test.__name__)
        else:
            failed.append(test.__name__)

    print(f"\n=== Test Results ===")
    print(f"PASSED: {len(passed)}/{len(tests)}")
    for n in passed:
        print(f"  ✅ {n}")
    print(f"FAILED: {len(failed)}/{len(tests)}")
    for n in failed:
        print(f"  ❌ {n}")
    print(f"NOT TESTED: {len(not_tested)}/{len(tests)}")
    for n in not_tested:
        print(f"  ⚠️  {n}")
    if failed:
        print("❌ Some tests failed")
        return 1
    print("✅ All executed tests passed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())