#!/usr/bin/env python3
"""
Video Processor Module

This module handles embedding subtitles into videos and converting videos to MP4 format.
"""

import os
import subprocess
from typing import Optional, Tuple


def embed_subtitles_in_video(video_path: str, srt_path: str, output_path: str = None) -> Optional[str]:
    """
    Embeds subtitles into a video file using ffmpeg.
    
    Args:
        video_path (str): Path to the input video file.
        srt_path (str): Path to the SRT subtitle file.
        output_path (str): Path for the output video file. If None, appends '_subtitled' to input filename.
        
    Returns:
        Optional[str]: Path to the output video file with embedded subtitles, or None if failed.
    """
    try:
        if not os.path.exists(video_path):
            print(f"Video file not found: {video_path}")
            return None
            
        if not os.path.exists(srt_path):
            print(f"Subtitle file not found: {srt_path}")
            return None
            
        # Set output path if not provided
        if output_path is None:
            base_name = os.path.splitext(os.path.basename(video_path))[0]
            output_dir = os.path.dirname(video_path) or "."
            output_path = os.path.join(output_dir, f"{base_name}_subtitled.mp4")
        
        # Use ffmpeg to embed subtitles with better error handling
        command = [
            "ffmpeg",
            "-i", video_path,
            "-vf", f"subtitles={srt_path}:force_style='FontName=Arial,FontSize=24,PrimaryColour=&HFFFFFF&'",
            "-c:v", "libx264",
            "-crf", "23",
            "-preset", "fast",
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            output_path
        ]
        
        result = subprocess.run(command, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Failed to embed subtitles: {result.stderr}")
            return None
            
        print(f"Subtitles embedded successfully: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"An error occurred while embedding subtitles: {e}")
        return None


def convert_to_mp4(input_path: str, output_path: str = None) -> Optional[str]:
    """
    Converts a video file to MP4 format using ffmpeg.
    
    Args:
        input_path (str): Path to the input video file.
        output_path (str): Path for the output MP4 file. If None, replaces extension with .mp4.
        
    Returns:
        Optional[str]: Path to the output MP4 file, or None if failed.
    """
    try:
        if not os.path.exists(input_path):
            print(f"Input file not found: {input_path}")
            return None
            
        # Set output path if not provided
        if output_path is None:
            base_name = os.path.splitext(os.path.basename(input_path))[0]
            output_dir = os.path.dirname(input_path) or "."
            output_path = os.path.join(output_dir, f"{base_name}.mp4")
        
        # Use ffmpeg to convert to MP4
        command = [
            "ffmpeg",
            "-i", input_path,
            "-c:v", "libx264",
            "-crf", "23",
            "-preset", "fast",
            "-c:a", "aac",
            "-b:a", "128k",
            output_path
        ]
        
        result = subprocess.run(command, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Failed to convert to MP4: {result.stderr}")
            return None
            
        print(f"Video converted to MP4 successfully: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"An error occurred while converting to MP4: {e}")
        return None


def process_video_with_subtitles(video_file: str, srt_file: str, output_path: str = "./output") -> Tuple[Optional[str], Optional[str]]:
    """
    Processes a video by embedding subtitles and converting to MP4.
    
    Args:
        video_file (str): Path to the video file.
        srt_file (str): Path to the SRT subtitle file.
        output_path (str): Directory to save processed files. Defaults to "./output".
        
    Returns:
        Tuple[Optional[str], Optional[str]]: Paths to the subtitled video and MP4 file, or None if failed.
    """
    try:
        # Ensure output directory exists
        os.makedirs(output_path, exist_ok=True)
        
        # Embed subtitles
        base_name = os.path.splitext(os.path.basename(video_file))[0]
        subtitled_video = os.path.join(output_path, f"{base_name}_subtitled.mp4")
        
        embedded_result = embed_subtitles_in_video(video_file, srt_file, subtitled_video)
        if not embedded_result:
            print("Failed to embed subtitles.")
            return None, None
            
        # Convert to MP4 (the embedded video is already MP4, so we just return it)
        # If the input was not MP4, we would convert it first
        if not video_file.lower().endswith('.mp4'):
            mp4_output = os.path.join(output_path, f"{base_name}.mp4")
            mp4_result = convert_to_mp4(video_file, mp4_output)
            if not mp4_result:
                print("Failed to convert to MP4, but subtitled video is available.")
                return embedded_result, None
            return embedded_result, mp4_result
        else:
            # Already MP4, so return the same file for both
            return embedded_result, embedded_result
            
    except Exception as e:
        print(f"An error occurred during video processing: {e}")
        return None, None


if __name__ == "__main__":
    # Example usage
    video_file = "/path/to/video.mp4"
    srt_file = "/path/to/subtitles.srt"
    
    # Embed subtitles
    subtitled_video = embed_subtitles_in_video(video_file, srt_file)
    if subtitled_video:
        print(f"Subtitled video created: {subtitled_video}")
    
    # Convert to MP4
    mp4_video = convert_to_mp4(video_file)
    if mp4_video:
        print(f"MP4 video created: {mp4_video}")