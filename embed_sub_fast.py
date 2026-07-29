#!/usr/bin/env python3
"""
Fast version of subtitle embedding script.
Uses ultrafast preset and lower quality for quicker processing.
"""

import os
import subprocess
import shutil


def main():
    """Main function to handle fast subtitle embedding."""
    base_dir = "/home/lintzuyang/Opencode/project/website/output"
    
    # Ensure output directory exists
    os.makedirs(base_dir, exist_ok=True)
    
    # Use simple filenames
    input_video = os.path.join(base_dir, "input.webm")
    input_srt = os.path.join(base_dir, "subtitles.srt")
    output_video = os.path.join(base_dir, "output_with_subtitles_fast.mp4")
    
    # Original files with special characters
    original_video = os.path.join(base_dir, "How I'm making 20+ Divines an Hour With Breach in 3.29 - Path of Exile 1.webm")
    original_srt = os.path.join(base_dir, "How I'm making 20+ Divines an Hour With Breach in 3.29 - Path of Exile 1.srt")
    
    print("Starting FAST subtitle embedding process...")
    print("Using ultrafast preset - lower quality but much faster")
    
    # Copy original files to simple names
    try:
        shutil.copy2(original_video, input_video)
        print(f"Copied video: {original_video} -> {input_video}")
    except Exception as e:
        print(f"Error copying video: {e}")
        return
    
    try:
        shutil.copy2(original_srt, input_srt)
        print(f"Copied subtitles: {original_srt} -> {input_srt}")
    except Exception as e:
        print(f"Error copying subtitles: {e}")
        return
    
    # Use ffmpeg with ultrafast preset
    print("Embedding subtitles using ultrafast preset...")
    
    cmd = [
        "ffmpeg", "-y",
        "-i", input_video,
        "-vf", f"subtitles={input_srt}",
        "-c:v", "libx264",
        "-crf", "28",  # Lower quality for faster encoding
        "-preset", "ultrafast",  # Fastest preset
        "-c:a", "aac",
        "-b:a", "96k",  # Lower bitrate for faster encoding
        output_video
    ]
    
    print(f"Command: {' '.join(cmd)}")
    
    # Run without capturing output to see real-time progress
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print(f"Success! Video with subtitles created: {output_video}")
        
        # Check duration
        duration_result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", output_video],
            capture_output=True, text=True
        )
        if duration_result.returncode == 0:
            duration = float(duration_result.stdout.strip())
            print(f"Video duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
            if duration > 400:  # Check if we got most of the video
                print("✓ Successfully processed most of the video!")
            else:
                print(f"⚠ Only processed {duration:.1f} seconds, expected ~440 seconds")
        
        print(f"File size: {os.path.getsize(output_video) / (1024*1024):.2f} MB")
    else:
        print(f"Failed to embed subtitles. Return code: {result.returncode}")


if __name__ == "__main__":
    main()