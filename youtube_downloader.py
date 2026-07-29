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
        
        # Use yt-dlp to download the video
        command = [
            "yt-dlp",
            "-o",
            os.path.join(output_path, "%(title)s.%(ext)s"),
            url
        ]
        
        result = subprocess.run(command, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Failed to download video: {result.stderr}")
            return None
        
        # Get the downloaded file path
        downloaded_files = [f for f in os.listdir(output_path) if f.endswith(".mp4") or f.endswith(".webm")]
        if not downloaded_files:
            print("No video file found after download.")
            return None
        
        downloaded_file = os.path.join(output_path, downloaded_files[0])
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