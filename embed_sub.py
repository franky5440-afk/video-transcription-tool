#!/usr/bin/env python3
"""
Standalone script for embedding subtitles into videos.

This script provides a clean way to embed subtitles without using complex
single-line commands that can fail with special characters in filenames.
"""

import os
from video_processor import embed_subtitles_in_video, convert_to_mp4
from transcription_service import parse_srt_to_text


def main():
    """Main function to handle subtitle embedding."""
    # Define paths using variables to avoid issues with special characters
    base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    
    # Ensure output directory exists
    os.makedirs(base_dir, exist_ok=True)
    
    # Input files - use raw strings to avoid escaping issues
    video_file = os.path.join(base_dir, r"How I'm making 20+ Divines an Hour With Breach in 3.29 - Path of Exile 1.webm")
    srt_file = os.path.join(base_dir, r"How I'm making 20+ Divines an Hour With Breach in 3.29 - Path of Exile 1.srt")
    markdown_file = os.path.join(base_dir, "transcription.md")
    
    # Output files - use simpler names to avoid special character issues
    output_srt = os.path.join(base_dir, "transcription_embedded.srt")
    output_subtitled = os.path.join(base_dir, "video_with_subtitles.mp4")
    
    print("Starting subtitle embedding process...")
    print(f"Video file: {video_file}")
    print(f"Subtitle file: {srt_file}")
    
    # Check if video file exists
    if not os.path.exists(video_file):
        print(f"Error: Video file not found at {video_file}")
        return
    
    # Check if we have an SRT file, if not try to create one from markdown
    if not os.path.exists(srt_file):
        print(f"SRT file not found, trying to create from markdown: {markdown_file}")
        if os.path.exists(markdown_file):
            srt_content = parse_srt_to_text(markdown_file)
            if srt_content:
                with open(output_srt, 'w', encoding='utf-8') as f:
                    f.write(srt_content)
                srt_file = output_srt
                print(f"Created SRT file: {srt_file}")
            else:
                print("Failed to parse markdown for SRT conversion")
                return
        else:
            print(f"Error: Neither SRT nor markdown file found")
            return
    else:
        print(f"Using existing SRT file: {srt_file}")
    
    # Embed subtitles
    print("Embedding subtitles into video...")
    print(f"Video file exists: {os.path.exists(video_file)}")
    print(f"SRT file exists: {os.path.exists(srt_file)}")
    print(f"SRT file path: {os.path.abspath(srt_file)}")
    
    # Try with absolute paths
    abs_video = os.path.abspath(video_file)
    abs_srt = os.path.abspath(srt_file)
    abs_output = os.path.abspath(output_subtitled)
    
    print(f"Using absolute paths:")
    print(f"  Video: {abs_video}")
    print(f"  SRT: {abs_srt}")
    print(f"  Output: {abs_output}")
    
    result = embed_subtitles_in_video(abs_video, abs_srt, abs_output)
    
    if result:
        print(f"Success! Subtitled video created: {result}")
        print(f"File size: {os.path.getsize(result) / (1024*1024):.2f} MB")
    else:
        print("Failed to embed subtitles")
        # Try a simpler approach with just ffmpeg command
        print("Trying direct ffmpeg command...")
        import subprocess
        cmd = [
            "ffmpeg", "-y",  # Overwrite output file if exists
            "-i", abs_video,
            "-vf", f"subtitles={abs_srt}",
            "-c:a", "copy",
            abs_output
        ]
        print(f"Command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Direct ffmpeg succeeded: {abs_output}")
        else:
            print(f"Direct ffmpeg failed: {result.stderr}")


if __name__ == "__main__":
    main()