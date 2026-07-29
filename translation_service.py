#!/usr/bin/env python3
"""
Translation Service Module

This module handles the translation of text into Traditional Chinese.
"""

from typing import Optional
from deep_translator import GoogleTranslator


def translate_to_traditional_chinese(text: str) -> Optional[str]:
    """
    Translates the given text into Traditional Chinese.
    
    Args:
        text (str): The text to translate.
    
    Returns:
        Optional[str]: The translated text, or None if the translation failed.
    """
    try:
        if not text:
            print("No text provided for translation.")
            return None
        
        translator = GoogleTranslator(source='auto', target='zh-TW')
        translated_text = translator.translate(text)
        
        print("Translation completed successfully.")
        return translated_text
        
    except Exception as e:
        print(f"An error occurred while translating the text: {e}")
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