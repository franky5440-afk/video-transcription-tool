#!/usr/bin/env python3
"""
Output Formatter Module

This module handles the formatting of the transcription output into Markdown format.
"""

import os
from typing import Optional


def format_to_markdown(translated_transcription: str, original_transcription: str, video_title: str = "Video Transcription") -> tuple[Optional[str], Optional[str]]:
    """
    Formats the translated and original transcriptions into Markdown format.
    
    Args:
        translated_transcription (str): The translated transcription text.
        original_transcription (str): The original transcription text.
        video_title (str): The title of the video. Defaults to "Video Transcription".
    
    Returns:
        tuple[Optional[str], Optional[str]]: The formatted Markdown text for translated and original transcriptions, or None if the formatting failed.
    """
    try:
        if not translated_transcription or not original_transcription:
            print("No translated or original transcription provided for formatting.")
            return None, None
        
        translated_markdown = f"# {video_title} (Translated)\n\n{translated_transcription}"
        original_markdown = f"# {video_title} (Original)\n\n{original_transcription}"
        
        return translated_markdown, original_markdown
        
    except Exception as e:
        print(f"An error occurred while formatting the transcription: {e}")
        return None, None


def save_to_markdown_file(translated_markdown: str, original_markdown: str, output_path: str = "./output") -> tuple[Optional[str], Optional[str]]:
    """
    Saves the formatted Markdown text to files.
    
    Args:
        translated_markdown (str): The formatted Markdown text for translated transcription.
        original_markdown (str): The formatted Markdown text for original transcription.
        output_path (str): The directory to save the Markdown files. Defaults to "./output".
    
    Returns:
        tuple[Optional[str], Optional[str]]: The paths to the saved Markdown files, or None if the saving failed.
    """
    try:
        if not translated_markdown or not original_markdown:
            print("No Markdown text provided for saving.")
            return None, None
        
        # Ensure the output directory exists
        os.makedirs(output_path, exist_ok=True)
        
        # Save translated transcription
        translated_file = os.path.join(output_path, "transcription_translated.md")
        with open(translated_file, 'w', encoding='utf-8') as file:
            file.write(translated_markdown)
        
        # Save original transcription
        original_file = os.path.join(output_path, "transcription_original.md")
        with open(original_file, 'w', encoding='utf-8') as file:
            file.write(original_markdown)
        
        print(f"Markdown files saved successfully: {translated_file}, {original_file}")
        return translated_file, original_file
        
    except Exception as e:
        print(f"An error occurred while saving the Markdown files: {e}")
        return None, None


if __name__ == "__main__":
    # Example usage
    translated_transcription = """[00:00:01] 你好
[00:00:03] 歡迎來到我的頻道"""
    original_transcription = """[00:00:01] Hello
[00:00:03] Welcome to my channel"""
    
    translated_markdown, original_markdown = format_to_markdown(translated_transcription, original_transcription, "Example Video")
    if translated_markdown and original_markdown:
        print("Formatted Markdown (Translated):")
        print(translated_markdown)
        print("\nFormatted Markdown (Original):")
        print(original_markdown)
        
        saved_files = save_to_markdown_file(translated_markdown, original_markdown)
        if saved_files[0] and saved_files[1]:
            print(f"\nSaved to: {saved_files[0]}, {saved_files[1]}")