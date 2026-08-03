#!/usr/bin/env python3
"""
Simplified script for embedding subtitles into videos.
Uses simple filenames to avoid issues with special characters.
"""

import os
import subprocess
import shutil
from video_processor import convert_to_mp4


def main():
    """Main function to handle subtitle embedding with simple filenames."""
    base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    
    # Ensure output directory exists
    os.makedirs(base_dir, exist_ok=True)
    
    # Use simple filenames
    input_video = os.path.join(base_dir, "input.webm")
    input_srt = os.path.join(base_dir, "subtitles.srt")
    output_video = os.path.join(base_dir, "output_with_subtitles.mp4")
    
    # Original files with special characters
    original_video = os.path.join(base_dir, "How I'm making 20+ Divines an Hour With Breach in 3.29 - Path of Exile 1.webm")
    original_srt = os.path.join(base_dir, "How I'm making 20+ Divines an Hour With Breach in 3.29 - Path of Exile 1.srt")
    
    print("Starting simplified subtitle embedding process...")
    
    # Copy original files to simple names using shutil
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
    
    # Use ffmpeg with simple filenames
    print("Embedding subtitles using simple filenames...")
    
    cmd = [
        "ffmpeg", "-y",
        "-i", input_video,
        "-vf", f"subtitles={input_srt}",
        "-c:v", "libx264",
        "-crf", "23",
        "-preset", "fast",
        "-c:a", "aac",
        "-b:a", "128k",
        output_video
    ]
    
    print(f"Command: {' '.join(cmd)}")
    
    # Show progress in real-time
    print("Processing video with ffmpeg (this may take a few minutes)...")
    result = subprocess.run(cmd, text=True)
    
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
        
        print(f"File size: {os.path.getsize(output_video) / (1024*1024):.2f} MB")
        
        # Also create a copy with original name
        final_output = os.path.join(base_dir, "How Im making 20+ Divines an Hour With Breach in 3.29 - Path of Exile 1_subtitled.mp4")
        try:
            shutil.copy2(output_video, final_output)
            print(f"Also saved as: {final_output}")
        except Exception as e:
            print(f"Failed to create copy with original name: {e}")
    else:
        print(f"Failed to embed subtitles. Return code: {result.returncode}")
        print("STDERR:", result.stderr)
        print("STDOUT:", result.stdout)
        
        print("Trying alternative approach without re-encoding...")
        
        # Try without re-encoding video (just copy streams and add subtitles)
        cmd2 = [
            "ffmpeg", "-y",
            "-i", input_video,
            "-vf", f"subtitles={input_srt}",
            "-c:v", "copy",  # Copy video stream without re-encoding
            "-c:a", "copy",  # Copy audio stream without re-encoding
            output_video
        ]
        
        print(f"Alternative command: {' '.join(cmd2)}")
        result2 = subprocess.run(cmd2, text=True)
        
        if result2.returncode == 0:
            print(f"Alternative approach succeeded: {output_video}")
            # Check duration of alternative output
            duration_result2 = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", output_video],
                capture_output=True, text=True
            )
            if duration_result2.returncode == 0:
                duration2 = float(duration_result2.stdout.strip())
                print(f"Alternative output duration: {duration2:.1f} seconds ({duration2/60:.1f} minutes)")
        else:
            print(f"Alternative approach also failed. Return code: {result2.returncode}")
            print("STDERR:", result2.stderr)


if __name__ == "__main__":
    main()