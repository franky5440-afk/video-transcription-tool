#!/usr/bin/env python3
"""
Test script for P1 fixes verification
"""

import os
import sys
import subprocess
import io
from contextlib import redirect_stdout

# Add project root to path
sys.path.insert(0, '/home/lintzuyang/Opencode/project/website')

from main import process_single_video

def test_p1_3_failure_handling():
    """Test P1-3: Failure case should not print success message (main.py display logic)"""
    print("\n=== Testing P1-3: Failure handling (main.py display logic) ===")
    
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
    
    # Mock the process_video_with_subtitles to return (None, None) to simulate failure
    from video_processor import process_video_with_subtitles as original_process
    
    def mock_process(*args, **kwargs):
        return (None, None)
    
    # Temporarily replace the function
    import video_processor
    video_processor.process_video_with_subtitles = mock_process
    
    # Capture stdout to check for success messages
    f = io.StringIO()
    with redirect_stdout(f):
        # Simulate user input 'y' for the interactive loop
        # We'll test the display logic by calling process_single_video
        # Since it's interactive, we need to mock input
        original_input = __builtins__.input
        def mock_input(prompt):
            if "Continue with video processing" in prompt:
                return 'y'
            return ''
        
        __builtins__.input = mock_input
        
        try:
            # This will call our mock process_video_with_subtitles which returns (None, None)
            process_single_video(video_path, srt_path, test_dir)
        finally:
            __builtins__.input = original_input
    
    output = f.getvalue()
    
    # Restore original function
    video_processor.process_video_with_subtitles = original_process
    
    print(f"Captured output: '{output}'")
    
    # Check that no success messages with checkmark were printed
    if "✓" in output:
        print("❌ Failure case should not print success messages with checkmark")
        return False
    
    # Check that failure message was printed
    if "✗" not in output:
        print("❌ Failure case should print failure message with cross mark")
        return False
    
    print("✅ P1-3 failure handling test passed")
    return True

def test_p1_3_success_case():
    """Test P1-3: Success case should still print success messages (main.py display logic)"""
    print("\n=== Testing P1-3: Success case (main.py display logic) ===")
    
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
    
    # Mock the process_video_with_subtitles to return valid paths to simulate success
    from video_processor import process_video_with_subtitles as original_process
    
    def mock_process(*args, **kwargs):
        # Return valid paths to simulate success
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        subtitled_video = os.path.join(test_dir, f"{base_name}_subtitled.mp4")
        return (subtitled_video, subtitled_video)
    
    # Temporarily replace the function
    import video_processor
    video_processor.process_video_with_subtitles = mock_process
    
    # Capture stdout to check for success messages
    f = io.StringIO()
    with redirect_stdout(f):
        # Simulate user input 'y' for the interactive loop
        original_input = __builtins__.input
        def mock_input(prompt):
            if "Continue with video processing" in prompt:
                return 'y'
            return ''
        
        __builtins__.input = mock_input
        
        try:
            # This will call our mock process_video_with_subtitles which returns valid paths
            process_single_video(video_path, srt_path, test_dir)
        finally:
            __builtins__.input = original_input
    
    output = f.getvalue()
    
    # Restore original function
    video_processor.process_video_with_subtitles = original_process
    
    print(f"Captured output: '{output}'")
    
    # Check that success message with checkmark was printed
    if "✓ Video with embedded TRANSLATED subtitles:" not in output:
        print("❌ Success case should print subtitled video success message with checkmark")
        return False
    
    # Check that no failure messages were printed
    if "✗" in output:
        print("❌ Success case should not print failure messages")
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
    
    passed = []
    failed = []
    not_tested = []
    
    for test in tests:
        try:
            result = test()
            if result == "NOT_TESTED":
                not_tested.append(test.__name__)
            elif result:
                passed.append(test.__name__)
            else:
                failed.append(test.__name__)
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            failed.append(test.__name__)
    
    print(f"\n=== Test Results ===")
    print(f"PASSED: {len(passed)}/{len(tests)}")
    if passed:
        for test_name in passed:
            print(f"  ✅ {test_name}")
    
    print(f"FAILED: {len(failed)}/{len(tests)}")
    if failed:
        for test_name in failed:
            print(f"  ❌ {test_name}")
    
    print(f"NOT TESTED: {len(not_tested)}/{len(tests)}")
    if not_tested:
        for test_name in not_tested:
            print(f"  ⚠️  {test_name}")
    
    if failed:
        print("❌ Some tests failed")
        return 1
    else:
        print("✅ All executed tests passed!")
        return 0

if __name__ == "__main__":
    sys.exit(main())
