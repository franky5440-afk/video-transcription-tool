#!/usr/bin/env python3
"""
CLI wrapper for the video-transcription-tool (AppImage entry point).

This layer exposes the six independent features as subcommands and adds the
packaging contract on top of the existing feature modules without modifying
them:

    C1: success -> exit 0, any failure -> exit != 0
    C2: on success the last stdout line is "OUTPUT: <absolute path>"
    C3: on failure the error message is written to stderr
    C4: fully non-interactive (no input() prompt anywhere)
    C5: every subcommand supports --output DIR (default ./output, created if missing)
    C6: --help and <subcommand> --help list usage
"""

import argparse
import os
import shutil
import sys

from youtube_downloader import download_youtube_video
from transcription_service import transcribe_video, parse_srt_to_text
from translation_service import translate_transcription
from output_formatter import format_to_markdown, save_to_markdown_file
from video_processor import embed_subtitles_in_video, convert_to_mp4, process_video_with_subtitles
from main import create_srt_from_transcription


def fail(msg: str) -> int:
    print(f"ERROR: {msg}", file=sys.stderr)
    return 1


def cmd_all(args) -> int:
    source = args.input
    out_dir = os.path.abspath(args.output)
    os.makedirs(out_dir, exist_ok=True)

    if source.startswith(("http://", "https://")):
        video_file = download_youtube_video(source, out_dir)
        if not video_file:
            return fail(f"failed to download video: {source}")
    else:
        video_file = source
        if not os.path.exists(video_file):
            return fail(f"local video file not found: {video_file}")

    transcription_file = transcribe_video(video_file)
    if not transcription_file:
        return fail("transcription failed")
    original_transcription = parse_srt_to_text(transcription_file)
    if not original_transcription:
        return fail("could not parse transcription")
    translated_transcription = translate_transcription(original_transcription)
    if not translated_transcription:
        return fail("translation failed")
    translated_markdown, original_markdown = format_to_markdown(
        translated_transcription, original_transcription, os.path.basename(video_file))
    if not translated_markdown or not original_markdown:
        return fail("could not format transcription")
    saved_files = save_to_markdown_file(translated_markdown, original_markdown, out_dir)
    if not saved_files[0] or not saved_files[1]:
        return fail("could not save markdown files")
    translated_srt_file = os.path.join(out_dir, "transcription_translated.srt")
    if not create_srt_from_transcription(translated_transcription, translated_srt_file):
        return fail("could not generate translated SRT file")
    subtitled_video, mp4_video = process_video_with_subtitles(video_file, translated_srt_file, out_dir)
    if not subtitled_video:
        return fail("could not embed subtitles")

    print(f"OUTPUT: {os.path.abspath(subtitled_video)}")
    return 0


def cmd_download(args) -> int:
    out_dir = os.path.abspath(args.output)
    os.makedirs(out_dir, exist_ok=True)
    result = download_youtube_video(args.input, out_dir)
    if not result:
        return fail(f"failed to download video: {args.input}")
    print(f"OUTPUT: {os.path.abspath(result)}")
    return 0


def cmd_transcribe(args) -> int:
    out_dir = os.path.abspath(args.output)
    os.makedirs(out_dir, exist_ok=True)
    result = transcribe_video(args.input)
    if not result:
        return fail(f"failed to transcribe: {args.input}")
    dest = os.path.join(out_dir, os.path.basename(result))
    if os.path.abspath(dest) != os.path.abspath(result):
        shutil.move(result, dest)
    print(f"OUTPUT: {os.path.abspath(dest)}")
    return 0


def cmd_translate(args) -> int:
    out_dir = os.path.abspath(args.output)
    os.makedirs(out_dir, exist_ok=True)
    original_text = parse_srt_to_text(args.input)
    if not original_text:
        return fail(f"could not parse SRT file: {args.input}")
    translated_text = translate_transcription(original_text)
    if not translated_text:
        return fail("translation failed")
    translated_srt = os.path.join(out_dir, "transcription_translated.srt")
    if not create_srt_from_transcription(translated_text, translated_srt):
        return fail("could not generate translated SRT file")
    translated_markdown, original_markdown = format_to_markdown(
        translated_text, original_text, os.path.basename(args.input))
    saved = save_to_markdown_file(translated_markdown, original_markdown, out_dir)
    if not saved[0] or not saved[1]:
        return fail("could not save markdown files")
    print(f"OUTPUT: {os.path.abspath(translated_srt)}")
    return 0


def cmd_embed(args) -> int:
    out_dir = os.path.abspath(args.output)
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(args.video))[0]
    dest = os.path.join(out_dir, f"{base}_subtitled.mp4")
    result = embed_subtitles_in_video(args.video, args.srt, dest)
    if not result:
        return fail("failed to embed subtitles")
    print(f"OUTPUT: {os.path.abspath(result)}")
    return 0


def cmd_mp4(args) -> int:
    out_dir = os.path.abspath(args.output)
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(args.input))[0]
    dest = os.path.join(out_dir, f"{base}.mp4")
    result = convert_to_mp4(args.input, dest)
    if not result:
        return fail(f"failed to convert to MP4: {args.input}")
    print(f"OUTPUT: {os.path.abspath(result)}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="video-transcription-tool.AppImage",
        description="YouTube / local video transcription and translation tool (AppImage).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("all", help="full pipeline until a subtitled MP4 is produced")
    p.add_argument("input", help="YouTube URL or local video file path")
    p.add_argument("--output", default="./output")
    p.set_defaults(func=cmd_all)

    p = sub.add_parser("download", help="download a YouTube video")
    p.add_argument("input", help="YouTube URL")
    p.add_argument("--output", default="./output")
    p.set_defaults(func=cmd_download)

    p = sub.add_parser("transcribe", help="produce an SRT transcription of a video")
    p.add_argument("input", help="video file path")
    p.add_argument("--output", default="./output")
    p.set_defaults(func=cmd_transcribe)

    p = sub.add_parser("translate", help="translate an SRT transcription into Traditional Chinese")
    p.add_argument("input", help="SRT file path")
    p.add_argument("--output", default="./output")
    p.set_defaults(func=cmd_translate)

    p = sub.add_parser("embed", help="embed subtitles into a video")
    p.add_argument("video", help="video file path")
    p.add_argument("srt", help="SRT subtitle file path")
    p.add_argument("--output", default="./output")
    p.set_defaults(func=cmd_embed)

    p = sub.add_parser("mp4", help="convert a video to MP4")
    p.add_argument("input", help="video file path")
    p.add_argument("--output", default="./output")
    p.set_defaults(func=cmd_mp4)

    return parser


def main() -> None:
    args = build_parser().parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
