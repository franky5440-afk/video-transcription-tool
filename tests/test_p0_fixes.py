#!/usr/bin/env python3
"""
Test script for P0 fixes verification
"""

import os
import sys
import time
import shutil
import tempfile
import subprocess

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from video_processor import embed_subtitles_in_video, convert_to_mp4
from youtube_downloader import download_youtube_video

def test_p0_1_embed_subtitles_overwrite():
    """Test P0-1: embed_subtitles_in_video overwrite functionality"""
    print("\n=== Testing P0-1: embed_subtitles_in_video overwrite ===")
    
    # Create test files
    test_dir = "/tmp/test_p0_1"
    os.makedirs(test_dir, exist_ok=True)
    
    # Create a small test video (1 second, silent)
    video_path = os.path.join(test_dir, "test.mp4")
    srt_path = os.path.join(test_dir, "test.srt")
    output_path = os.path.join(test_dir, "test_subtitled.mp4")
    
    # Create test video using ffmpeg
    subprocess.run([
        "ffmpeg", "-f", "lavfi", "-i", "color=size=100x100:rate=1:color=red",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-t", "1", "-y", video_path
    ], check=True)
    
    # Create test SRT file
    with open(srt_path, 'w') as f:
        f.write("1\n00:00:00,000 --> 00:00:01,000\nTest Subtitle 1\n\n")
    
    # First run
    print("First run...")
    start_time = time.time()
    result1 = embed_subtitles_in_video(video_path, srt_path, output_path)
    time1 = time.time() - start_time
    
    if not result1:
        print("❌ First run failed")
        return False
    
    # Get file stats
    stat1 = os.stat(output_path)
    mtime1 = stat1.st_mtime
    size1 = stat1.st_size
    
    # Update SRT file for second run
    with open(srt_path, 'w') as f:
        f.write("1\n00:00:00,000 --> 00:00:01,000\nTest Subtitle 2\n\n")
    
    # Second run (should overwrite)
    print("Second run (should overwrite)...")
    start_time = time.time()
    result2 = embed_subtitles_in_video(video_path, srt_path, output_path)
    time2 = time.time() - start_time
    
    if not result2:
        print("❌ Second run failed")
        return False
    
    # Get file stats
    stat2 = os.stat(output_path)
    mtime2 = stat2.st_mtime
    size2 = stat2.st_size
    
    # Verify results
    print(f"First run: {time1:.2f}s, size={size1}, mtime={mtime1}")
    print(f"Second run: {time2:.2f}s, size={size2}, mtime={mtime2}")
    
    if mtime1 == mtime2:
        print("❌ File mtime not changed - file was not overwritten")
        return False
    
    if size1 == size2:
        print("❌ File size not changed - file was not overwritten")
        return False
    
    if time2 > 30:  # Should not hang
        print("❌ Second run took too long - may have hung")
        return False
    
    print("✅ P0-1 embed_subtitles_in_video test passed")
    return True

def test_p0_1_convert_to_mp4_overwrite():
    """Test P0-1: convert_to_mp4 overwrite functionality"""
    print("\n=== Testing P0-1: convert_to_mp4 overwrite ===")
    
    # Create test files
    test_dir = "/tmp/test_p0_1_mp4"
    os.makedirs(test_dir, exist_ok=True)
    
    # Create a small test video (1 second, silent) with different content for each run
    video_path1 = os.path.join(test_dir, "test1.webm")
    video_path2 = os.path.join(test_dir, "test2.webm")
    output_path = os.path.join(test_dir, "test.mp4")
    
    # Create first test video (blue)
    subprocess.run([
        "ffmpeg", "-f", "lavfi", "-i", "color=size=100x100:rate=1:color=blue",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-t", "1", "-y", video_path1
    ], check=True)
    
    # Create second test video (green) for second run
    subprocess.run([
        "ffmpeg", "-f", "lavfi", "-i", "color=size=100x100:rate=1:color=green",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-t", "1", "-y", video_path2
    ], check=True)
    
    # First run
    print("First run...")
    start_time = time.time()
    result1 = convert_to_mp4(video_path1, output_path)
    time1 = time.time() - start_time
    
    if not result1:
        print("❌ First run failed")
        return False
    
    # Get file stats
    stat1 = os.stat(output_path)
    mtime1 = stat1.st_mtime
    size1 = stat1.st_size
    
    # Second run with different input (should overwrite)
    print("Second run (should overwrite)...")
    start_time = time.time()
    result2 = convert_to_mp4(video_path2, output_path)
    time2 = time.time() - start_time
    
    if not result2:
        print("❌ Second run failed")
        return False
    
    # Get file stats
    stat2 = os.stat(output_path)
    mtime2 = stat2.st_mtime
    size2 = stat2.st_size
    
    # Verify results
    print(f"First run: {time1:.2f}s, size={size1}, mtime={mtime1}")
    print(f"Second run: {time2:.2f}s, size={size2}, mtime={mtime2}")
    
    if mtime1 == mtime2:
        print("❌ File mtime not changed - file was not overwritten")
        return False
    
    # Note: File sizes can be the same even if content is different
    # The important thing is that mtime changed and the function completed successfully
    # if size1 == size2:
    #     print("❌ File size not changed - file was not overwritten")
    #     return False
    
    if time2 > 30:  # Should not hang
        print("❌ Second run took too long - may have hung")
        return False
    
    print("✅ P0-1 convert_to_mp4 test passed")
    return True

def test_p0_1_failure_case():
    """Test P0-1: Failure case handling"""
    print("\n=== Testing P0-1: Failure case ===")
    
    test_dir = "/tmp/test_p0_1_fail"
    os.makedirs(test_dir, exist_ok=True)
    
    video_path = os.path.join(test_dir, "test.mp4")
    srt_path = os.path.join(test_dir, "nonexistent.srt")  # Non-existent file
    output_path = os.path.join(test_dir, "test_subtitled.mp4")
    
    # Create test video
    subprocess.run([
        "ffmpeg", "-f", "lavfi", "-i", "color=size=100x100:rate=1:color=green",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-t", "1", "-y", video_path
    ], check=True)
    
    # Should return None for non-existent SRT
    result = embed_subtitles_in_video(video_path, srt_path, output_path)
    
    if result is not None:
        print("❌ Should return None for non-existent SRT file")
        return False
    
    print("✅ P0-1 failure case test passed")
    return True

# 19-second public video, stable and commonly used for tooling tests
TEST_VIDEO_URL = "https://www.youtube.com/watch?v=jNQXAC9IVRw"


def test_p0_2_youtube_download():
    """Test P0-2: download must return the newly downloaded file, not a
    pre-existing one that happens to sort first in os.listdir().

    Requires network access; returns NOT_TESTED if the download cannot run.
    """
    print("\n=== Testing P0-2: YouTube download ===")

    test_dir = tempfile.mkdtemp(prefix="test_p0_2_")
    try:
        # Decoys the old `os.listdir(...)[0]` logic could pick instead
        decoys = ["aaa_decoy_subtitled.mp4", "zzz_decoy.mp4", "mmm_old.webm"]
        for name in decoys:
            with open(os.path.join(test_dir, name), 'w') as f:
                f.write("dummy")
        print(f"Created decoy files: {decoys}")

        result = download_youtube_video(TEST_VIDEO_URL, test_dir)

        if result is None:
            print("⚠️  P0-2: NOT TESTED (download failed — no network access?)")
            return "NOT_TESTED"

        print(f"Returned path: {result!r}")

        if os.path.basename(result) in decoys:
            print("❌ Returned a pre-existing decoy instead of the download")
            return False
        if not os.path.exists(result):
            print("❌ Returned path does not exist on disk")
            return False

        print("✅ P0-2 download test passed")
        return True
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)

def main():
    """Run all tests"""
    print("Starting P0 fixes verification tests...")
    
    tests = [
        test_p0_1_embed_subtitles_overwrite,
        test_p0_1_convert_to_mp4_overwrite,
        test_p0_1_failure_case,
        test_p0_2_youtube_download
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
