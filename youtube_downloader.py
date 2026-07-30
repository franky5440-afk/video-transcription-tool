#!/usr/bin/env python3
"""
YouTube Downloader Module

This module handles the downloading of YouTube videos given a URL.
"""

import os
import subprocess
from typing import Optional


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
            "-f", "bestvideo+bestaudio/best",  # Download best video and audio
            "--merge-output-format", "mp4",    # Merge into MP4 format
            "-o",
            os.path.join(output_path, "%(title)s.%(ext)s"),
            url
        ]
        
        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"Failed to download video: {result.stderr}")
            return None

        # Get the downloaded file path using yt-dlp's output
        # Use --print to get the actual output filename from yt-dlp
        print_command = [
            "yt-dlp",
            "--print", "filename",
            "-o",
            os.path.join(output_path, "%(title)s.%(ext)s"),
            url
        ]
        
        print_result = subprocess.run(print_command, capture_output=True, text=True)
        if print_result.returncode != 0:
            print(f"Failed to get downloaded filename: {print_result.stderr}")
            return None
        
        filename = print_result.stdout.strip()
        if not filename:
            print("No filename returned from yt-dlp.")
            return None
        
        downloaded_file = os.path.join(output_path, filename)
        
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