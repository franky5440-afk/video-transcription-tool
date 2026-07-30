#!/usr/bin/env python3
"""
Main CLI Application

This module provides the command-line interface for the YouTube transcription application.
"""

import argparse
import os
from youtube_downloader import download_youtube_video, download_batch_youtube_videos
from transcription_service import transcribe_video, parse_srt_to_text
from translation_service import translate_transcription
from output_formatter import format_to_markdown, save_to_markdown_file
from video_processor import embed_subtitles_in_video, convert_to_mp4, process_video_with_subtitles


def process_single_video(url: str, output_path: str = "./output") -> None:
    """
    Processes a single video: downloads (if URL), transcribes, translates, and saves the result.
    
    Args:
        url (str): The YouTube video URL or local video file path.
        output_path (str): The directory to save the output files. Defaults to "./output".
    """
    print(f"Processing video: {url}")
    
    # Check if input is a URL or local file
    if url.startswith(('http://', 'https://')):
        # Download the video
        video_file = download_youtube_video(url, output_path)
        if not video_file:
            print("Failed to download the video.")
            return
    else:
        # Use the local file directly
        video_file = url
        if not os.path.exists(video_file):
            print(f"Local video file not found: {video_file}")
            return
    
    # Transcribe the video
    transcription_file = transcribe_video(video_file)
    if not transcription_file:
        print("Failed to transcribe the video.")
        return
    
    # Parse the transcription
    original_transcription = parse_srt_to_text(transcription_file)
    if not original_transcription:
        print("Failed to parse the transcription.")
        return
    
    # Translate the transcription
    translated_transcription = translate_transcription(original_transcription)
    if not translated_transcription:
        print("Failed to translate the transcription.")
        return
    
    # Format and save the result
    translated_markdown, original_markdown = format_to_markdown(translated_transcription, original_transcription, os.path.basename(video_file))
    if not translated_markdown or not original_markdown:
        print("Failed to format the transcription.")
        return
    
    saved_files = save_to_markdown_file(translated_markdown, original_markdown, output_path)
    if saved_files[0] and saved_files[1]:
        print(f"Successfully saved transcriptions to: {saved_files[0]}, {saved_files[1]}")
    
    # Generate SRT file with translated subtitles for potential video processing
    translated_srt_file = os.path.join(output_path, "transcription_translated.srt")
    if create_srt_from_transcription(translated_transcription, translated_srt_file):
        print(f"Generated translated SRT file: {translated_srt_file}")
    else:
        print("Note: Could not generate translated SRT file for video processing.")
    
    # Ask user if they want to continue with video processing
    print("\nWould you like to continue with additional video processing?")
    print("This will:")
    print("1. Embed the TRANSLATED Traditional Chinese subtitles into the video")
    print("2. Convert the video to MP4 format (if not already MP4)")
    
    while True:
        user_input = input("Continue with video processing? (y/n): ").strip().lower()
        if user_input in ['y', 'yes']:
            if os.path.exists(translated_srt_file):
                # Process the video with translated subtitles
                subtitled_video, mp4_video = process_video_with_subtitles(video_file, translated_srt_file, output_path)
                if subtitled_video:
                    print(f"✓ Video with embedded TRANSLATED subtitles: {subtitled_video}")
                    if mp4_video and mp4_video != subtitled_video:
                        print(f"✓ MP4 converted video: {mp4_video}")
                else:
                    print("✗ Video processing failed: Could not embed subtitles")
            else:
                print("✗ Cannot proceed: Translated SRT file not found.")
                print(f"Expected file: {translated_srt_file}")
                break
        elif user_input in ['n', 'no']:
            print("Skipping video processing. You can manually process later using:")
            print(f"  ./ffmpeg_subtitles_general.sh {os.path.basename(video_file)} {os.path.basename(translated_srt_file)} output.mp4")
            break
        else:
            print("Please enter 'y' or 'n'.")


def process_batch_videos(urls: list[str], output_path: str = "./output") -> None:
    """
    Processes multiple YouTube videos: downloads, transcribes, translates, and saves the results.
    
    Args:
        urls (list[str]): A list of YouTube video URLs.
        output_path (str): The directory to save the output files. Defaults to "./output".
    """
    for url in urls:
        process_single_video(url, output_path)


def main() -> None:
    """
    Main function to handle command-line arguments and execute the application.
    """
    parser = argparse.ArgumentParser(description="Video Transcription Tool")
    parser.add_argument("url", nargs="*", help="YouTube video URL(s) or local video file path(s)")
    parser.add_argument("--output", default="./output", help="Output directory for files")
    
    args = parser.parse_args()
    
    if not args.url:
        print("Please provide at least one video URL or local file path.")
        return
    
    if len(args.url) == 1:
        process_single_video(args.url[0], args.output)
    else:
        process_batch_videos(args.url, args.output)


def create_srt_from_transcription(transcription_text: str, output_srt_path: str) -> bool:
    """
    Creates an SRT file from transcription text with timestamps.
    
    Handles both formats:
    - Markdown format: [HH:MM:SS,mmm --> HH:MM:SS,mmm] Text
    - SRT format: HH:MM:SS,mmm --> HH:MM:SS,mmm
    
    Args:
        transcription_text (str): Transcription text with timestamps
        output_srt_path (str): Path to save the SRT file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with open(output_srt_path, 'w', encoding='utf-8') as f:
            lines = transcription_text.strip().split('\n')
            segment_number = 1
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Handle Markdown format: [timestamp] text
                if line.startswith('[') and ']' in line:
                    # Extract timestamp and text from Markdown format
                    timestamp_part = line.split(']')[0].replace('[', '').strip()
                    text_part = line.split(']')[1].strip()
                    
                    # Only write if we have actual text content
                    if text_part:
                        # Write SRT format: number, timestamp, text, blank line
                        f.write(f"{segment_number}\n")
                        f.write(f"{timestamp_part}\n")
                        f.write(f"{text_part}\n\n")
                        segment_number += 1
                
                # Handle SRT format: timestamp line followed by text
                elif '-->' in line and '[' not in line:
                    # This is a timestamp line, next line should be text
                    timestamp_part = line.strip()
                    text_part = ""
                    
                    # Write SRT format
                    f.write(f"{segment_number}\n")
                    f.write(f"{timestamp_part}\n")
                    f.write(f"{text_part}\n\n")
                    segment_number += 1
        
        # Check if we created any content
        if segment_number > 1:
            print(f"Successfully created SRT file with {segment_number-1} subtitle segments")
            return True
        else:
            print("Warning: No valid subtitle segments found in transcription")
            return False
            
    except Exception as e:
        print(f"Error creating SRT file: {e}")
        return False


if __name__ == "__main__":
    main()