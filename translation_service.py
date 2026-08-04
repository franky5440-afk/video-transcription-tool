#!/usr/bin/env python3
"""
Translation Service Module

This module handles the translation of text into Traditional Chinese.
"""

import time
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
from deep_translator import GoogleTranslator


# Every line is its own HTTP round trip, so this step is latency bound rather
# than CPU bound: a faster machine does not speed it up at all, only overlapping
# the requests does. Measured 2026-08-05, a 32 minute video spent 19 of its 38
# minutes here. Kept deliberately modest -- too many parallel requests get
# throttled and come back as error pages, which costs more than it saves.
_MAX_WORKERS = 8


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
        # Seeded with the originals so that a line which is never translated --
        # blank, no timestamp, or a failed round trip -- is already preserved.
        translated_lines = list(lines)

        # Collect the lines that need a round trip before sending any, so the
        # pool only ever sees real work and results stay bound to their line.
        pending = []
        for index, line in enumerate(lines):
            if not line:
                continue

            # Extract timestamp and text
            if '[' in line and ']' in line:
                timestamp_part = line.split(']')[0] + ']'
                text_part = line.split(']')[1].strip()
                pending.append((index, timestamp_part, text_part))

        if pending:
            # map() keeps results in submission order, so zip() below pairs each
            # translation with the line it came from regardless of finish order.
            with ThreadPoolExecutor(max_workers=min(_MAX_WORKERS, len(pending))) as pool:
                results = list(pool.map(
                    translate_to_traditional_chinese,
                    [text_part for _, _, text_part in pending]))

            for (index, timestamp_part, _), translated_text in zip(pending, results):
                if translated_text:
                    translated_lines[index] = f"{timestamp_part} {translated_text}"
                # Translation failed: the original line is already in place.

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