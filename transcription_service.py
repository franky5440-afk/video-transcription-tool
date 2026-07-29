#!/usr/bin/env python3
"""
Transcription Service Module

This module handles the transcription of video content into text with timestamps.
"""

import os
import whisper
from typing import Optional


def transcribe_video(video_path: str, output_format: str = "srt") -> Optional[str]:
    """
    Transcribes the audio from a video file into text with timestamps.
    
    Args:
        video_path (str): The path to the video file.
        output_format (str): The format of the output transcription. Defaults to "srt".
    
    Returns:
        Optional[str]: The path to the transcription file, or None if the transcription failed.
    """
    try:
        if not os.path.exists(video_path):
            print(f"Video file not found: {video_path}")
            return None
        
        # Load the Whisper model
        model = whisper.load_model("base")
        
        # Transcribe the video
        result = model.transcribe(video_path)
        
        # Save the transcription to an SRT file
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        transcription_file = os.path.join(os.path.dirname(video_path), f"{base_name}.srt")
        
        with open(transcription_file, "w", encoding="utf-8") as f:
            for i, segment in enumerate(result["segments"], start=1):
                start_time = format_time(segment["start"])
                end_time = format_time(segment["end"])
                text = segment["text"].strip()
                f.write(f"{i}\n{start_time} --> {end_time}\n{text}\n\n")
        
        print(f"Transcription completed successfully: {transcription_file}")
        return transcription_file
        
    except Exception as e:
        print(f"An error occurred while transcribing the video: {e}")
        return None


def format_time(seconds: float) -> str:
    """
    Formats time in seconds to SRT time format (HH:MM:SS,mmm).
    
    Args:
        seconds (float): Time in seconds.
    
    Returns:
        str: Formatted time string.
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = seconds % 60
    milliseconds = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{int(seconds):02d},{milliseconds:03d}"


def parse_srt_to_text(srt_path: str) -> Optional[str]:
    """
    Parses an SRT file into a plain text string with timestamps.
    
    Args:
        srt_path (str): The path to the SRT file.
    
    Returns:
        Optional[str]: The parsed text with timestamps, or None if the parsing failed.
    """
    try:
        with open(srt_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        transcription_text = ""
        i = 0
        while i < len(lines):
            # Skip the sequence number
            if lines[i].strip().isdigit():
                i += 1
                continue
            
            # Add the timestamp line
            if i < len(lines) and "-->" in lines[i]:
                timestamp = lines[i].strip()
                i += 1
                
                # Add the text lines
                text_lines = []
                while i < len(lines) and lines[i].strip() != "":
                    text_lines.append(lines[i].strip())
                    i += 1
                
                if text_lines:
                    transcription_text += f"[{timestamp}] {' '.join(text_lines)}\n"
            else:
                i += 1
        
        return transcription_text if transcription_text else None
        
    except Exception as e:
        print(f"An error occurred while parsing the SRT file: {e}")
        return None


if __name__ == "__main__":
    # Example usage
    video_path = "/home/lintzuyang/Opencode/project/website/output/How I'm making 20+ Divines an Hour With Breach in 3.29 - Path of Exile 1.mp4"
    transcription_file = transcribe_video(video_path)
    if transcription_file:
        print(f"Transcription file: {transcription_file}")
        transcription_text = parse_srt_to_text(transcription_file)
        if transcription_text:
            print("Transcription text:")
            print(transcription_text)


def parse_srt_to_text(srt_path: str) -> Optional[str]:
    """
    Parses an SRT file into a plain text string with timestamps.
    
    Args:
        srt_path (str): The path to the SRT file.
    
    Returns:
        Optional[str]: The parsed text with timestamps, or None if the parsing failed.
    """
    try:
        with open(srt_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        transcription_text = ""
        i = 0
        while i < len(lines):
            # Skip the sequence number
            if lines[i].strip().isdigit():
                i += 1
                continue
            
            # Add the timestamp line
            if i < len(lines) and "-->" in lines[i]:
                timestamp = lines[i].strip()
                i += 1
                
                # Add the text lines
                text_lines = []
                while i < len(lines) and lines[i].strip() != "":
                    text_lines.append(lines[i].strip())
                    i += 1
                
                if text_lines:
                    transcription_text += f"[{timestamp}] {' '.join(text_lines)}\n"
            else:
                i += 1
        
        return transcription_text if transcription_text else None
        
    except Exception as e:
        print(f"An error occurred while parsing the SRT file: {e}")
        return None


if __name__ == "__main__":
    # Example usage
    video_path = "/home/lintzuyang/Opencode/project/website/output/How I'm making 20+ Divines an Hour With Breach in 3.29 - Path of Exile 1.mp4"
    transcription_file = transcribe_video(video_path)
    if transcription_file:
        print(f"Transcription file: {transcription_file}")
        transcription_text = parse_srt_to_text(transcription_file)
        if transcription_text:
            print("Transcription text:")
            print(transcription_text)
