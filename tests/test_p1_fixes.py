#!/usr/bin/env python3
"""
Test script for P1 fixes verification
"""

import os
import sys
import subprocess

# Add project root to path
sys.path.insert(0, '/home/lintzuyang/Opencode/project/website')

from main import process_video_with_subtitles

def test_p1_3_failure_handling():
    """Test P1-3: Failure case should not print success message"""
    print("\n=== Testing P1-3: Failure handling ===")
    
    # Create test files
    test_dir = "/tmp/test_p1_3"
    os.makedirs(test_dir, exist_ok=True)
    
    # Create a small test video
    video_path = os.path.join(test_dir, "test.mp4")
    srt_path = os.path.join(test_dir, "nonexistent.srt")  # Non-existent file
    
    # Create test video using ffmpeg
    subprocess.run([
        "ffmpeg", "-f", "lavfi", "-i", "color=size=100x100:rate=1:color=red",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-t", "1", "-y", video_path
    ], check=True)
    
    print("Testing failure case (non-existent SRT file)...")
    
    # Capture stdout to check for success messages
    import io
    from contextlib import redirect_stdout
    
    f = io.StringIO()
    with redirect_stdout(f):
        subtitled_video, mp4_video = process_video_with_subtitles(video_path, srt_path, test_dir)
    
    output = f.getvalue()
    
    print(f"Captured output: '{output}'")
    
    # Check that no success messages were printed
    if "✓" in output:
        print("❌ Failure case should not print success messages with checkmark")
        return False
    
    # Check that function returned None for both values
    if subtitled_video is not None or mp4_video is not None:
        print("❌ Failure case should return (None, None)")
        return False
    
    print("✅ P1-3 failure handling test passed")
    return True

def test_p1_3_success_case():
    """Test P1-3: Success case should still print success messages"""
    print("\n=== Testing P1-3: Success case ===")
    
    # Create test files
    test_dir = "/tmp/test_p1_3_success"
    os.makedirs(test_dir, exist_ok=True)
    
    # Create a small test video
    video_path = os.path.join(test_dir, "test.mp4")
    srt_path = os.path.join(test_dir, "test.srt")
    
    # Create test video using ffmpeg
    subprocess.run([
        "ffmpeg", "-f", "lavfi", "-i", "color=size=100x100:rate=1:color=blue",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-t", "1", "-y", video_path
    ], check=True)
    
    # Create test SRT file
    with open(srt_path, 'w') as f:
        f.write("1\n00:00:00,000 --> 00:00:01,000\nTest Subtitle\n\n")
    
    print("Testing success case...")
    
    # Capture stdout to check for success messages
    import io
    from contextlib import redirect_stdout
    
    f = io.StringIO()
    with redirect_stdout(f):
        subtitled_video, mp4_video = process_video_with_subtitles(video_path, srt_path, test_dir)
    
    output = f.getvalue()
    
    print(f"Captured output: '{output}'")
    
    # Check that success message was printed (from video_processor.py)
    # The checkmark messages are in main.py, but we can check the function returned valid results
    if "Subtitles embedded successfully:" not in output:
        print("❌ Success case should print subtitled video success message")
        return False
    
    # Check that function returned valid paths
    if subtitled_video is None:
        print("❌ Success case should return valid subtitled video path")
        return False
    
    print("✅ P1-3 success case test passed")
    return True

def main():
    """Run all tests"""
    print("Starting P1 fixes verification tests...")
    
    tests = [
        test_p1_3_failure_handling,
        test_p1_3_success_case
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    print(f"\n=== Test Results ===")
    print(f"Passed: {sum(results)}/{len(results)}")
    
    if all(results):
        print("✅ All P1 tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
