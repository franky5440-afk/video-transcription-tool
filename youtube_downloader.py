#!/usr/bin/env python3
"""
YouTube Downloader Module

This module handles the downloading of YouTube videos given a URL.
"""

import os
import subprocess
from typing import Optional

# Prefer the best decodable video stream on this machine.
# yt-dlp's default preference ranks AV1 first, but AV1 is consistently the
# lowest-bitrate stream at a given resolution on YouTube (and decodes slower
# than VP9 here). Exclude AV1 via regex (vcodec is like "av01.0.09M.08"), then
# fall back to the unconstrained best video+audio / combined format so that
# videos offering only AV1 still download successfully.
FORMAT_SELECTION = "bestvideo[vcodec!*=av01]+bestaudio/bestvideo+bestaudio/best"


def download_youtube_video(url: str, output_path: str = "./downloads") -> Optional[str]:
    """
    Downloads a YouTube video given its URL and returns the path to the downloaded file.
    
    Args:
        url (str): The YouTube video URL.
        output_path (str): The directory to save the downloaded video. Defaults to "./downloads".
    
    Returns:
        Optional[str]: The path to the downloaded video file, or None if the download failed.
    """
    try:
        # Ensure the output directory exists
        os.makedirs(output_path, exist_ok=True)
        
        # Use yt-dlp to download the video with audio
        command = [
            "yt-dlp",
            "-f", FORMAT_SELECTION,          # Download best video and audio
            "--merge-output-format", "mp4",    # Merge into MP4 format
            "-o",
            os.path.join(output_path, "%(title)s.%(ext)s"),
            url
        ]
        
        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"Failed to download video: {result.stderr}")
            return None

        # Get the downloaded file path using yt-dlp's --print with after_move stage
        # This ensures we get the actual final path after download and file operations
        command = [
            "yt-dlp",
            "-f", FORMAT_SELECTION,          # Download best video and audio
            "--merge-output-format", "mp4",    # Merge into MP4 format
            "--print", "after_move:filename",  # Print final filename after file is moved
            "-o",
            os.path.join(output_path, "%(title)s.%(ext)s"),
            url
        ]
        
        result = subprocess.run(command, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Failed to download video: {result.stderr}")
            return None
        
        # Extract the filename from the last line of stdout (after_move prints after download)
        lines = result.stdout.strip().split('\n')
        if not lines:
            print("No output from yt-dlp.")
            return None
        
        # The last line contains the final filename
        filename = lines[-1].strip()
        if not filename:
            print("No filename returned from yt-dlp.")
            return None
        
        # filename from --print after_move is the full path, no need to join again
        downloaded_file = filename
        
        # Verify the file exists
        if not os.path.exists(downloaded_file):
            print(f"Downloaded file not found: {downloaded_file}")
            return None
        
        print(f"Video downloaded successfully: {downloaded_file}")
        return downloaded_file
        
    except Exception as e:
        print(f"An error occurred while downloading the video: {e}")
        return None


def download_batch_youtube_videos(urls: list[str], output_path: str = "./downloads") -> list[Optional[str]]:
    """
    Downloads multiple YouTube videos given a list of URLs and returns the paths to the downloaded files.
    
    Args:
        urls (list[str]): A list of YouTube video URLs.
        output_path (str): The directory to save the downloaded videos. Defaults to "./downloads".
    
    Returns:
        list[Optional[str]]: A list of paths to the downloaded video files, or None for failed downloads.
    """
    return [download_youtube_video(url, output_path) for url in urls]


if __name__ == "__main__":
    # Example usage
    video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    downloaded_file = download_youtube_video(video_url)
    if downloaded_file:
        print(f"Downloaded file: {downloaded_file}")