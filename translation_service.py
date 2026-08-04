#!/usr/bin/env python3
"""
Translation Service Module

This module handles the translation of text into Traditional Chinese.
"""

import time
from typing import Optional
from deep_translator import GoogleTranslator


def _is_google_error_page(text: str) -> bool:
    """Check if the text is a Google Translate error page."""
    if not text:
        return False
    text_lower = text.lower()
    error_markers = [
        "that's an error",
        "that\u2019s an error",
        "that's all we know",
        "that\u2019s all we know",
        "(server error)"
    ]
    return any(marker in text_lower for marker in error_markers)


def translate_to_traditional_chinese(text: str) -> Optional[str]:
    """
    Translates the given text into Traditional Chinese.
    
    Args:
        text (str): The text to translate.
    
    Returns:
        Optional[str]: The translated text, or None if the translation failed.
    """
    if not text:
        print("No text provided for translation.")
        return None
    
    for attempt in range(2):
        try:
            translator = GoogleTranslator(source='auto', target='zh-TW')
            translated_text = translator.translate(text)
            
            if _is_google_error_page(translated_text):
                if attempt == 0:
                    print("Translation returned error page, retrying in 1 second...")
                    time.sleep(1)
                    continue
                else:
                    print("Translation failed: received error page after retry.")
                    return None
            
            print("Translation completed successfully.")
            return translated_text
            
        except Exception as e:
            if attempt == 0:
                print(f"Translation error (attempt 1): {e}, retrying in 1 second...")
                time.sleep(1)
                continue
            else:
                print(f"Translation failed after retry: {e}")
                return None
    
    return None


def translate_transcription(transcription_text: str) -> Optional[str]:
    """
    Translates a transcription text with timestamps into Traditional Chinese.
    
    Args:
        transcription_text (str): The transcription text with timestamps.
    
    Returns:
        Optional[str]: The translated transcription text, or None if the translation failed.
    """
    try:
        if not transcription_text:
            print("No transcription text provided for translation.")
            return None
        
        # Split the transcription text into lines
        lines = transcription_text.split('\n')
        translated_lines = []
        
        for line in lines:
            if not line:
                translated_lines.append(line)
                continue
            
            # Extract timestamp and text
            if '[' in line and ']' in line:
                timestamp_part = line.split(']')[0] + ']'
                text_part = line.split(']')[1].strip()
                
                # Translate the text part
                translated_text = translate_to_traditional_chinese(text_part)
                if translated_text:
                    translated_line = f"{timestamp_part} {translated_text}"
                    translated_lines.append(translated_line)
                else:
                    # Translation failed, preserve original text with timestamp
                    translated_lines.append(line)
            else:
                translated_lines.append(line)
        
        translated_transcription = '\n'.join(translated_lines)
        return translated_transcription if translated_transcription else None
        
    except Exception as e:
        print(f"An error occurred while translating the transcription: {e}")
        return None


if __name__ == "__main__":
    # Example usage
    transcription_text = """[00:00:01] Hello
[00:00:03] Welcome to my channel"""
    
    translated_transcription = translate_transcription(transcription_text)
    if translated_transcription:
        print("Translated transcription:")
        print(translated_transcription)