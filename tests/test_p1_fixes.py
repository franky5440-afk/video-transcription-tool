#!/usr/bin/env python3
"""
Test script for P1 fixes verification

Covers:
- P1-3: main.py must not print a success checkmark when processing fails
- R2:   the interactive while-loop must terminate on every path
"""

import os
import sys
import io
from contextlib import redirect_stdout
from unittest.mock import patch

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main

# Guard against a non-terminating loop hanging the test run
MAX_PROMPTS = 5


class LoopDidNotTerminate(RuntimeError):
    pass


def run_interactive_loop(process_result, srt_exists=True, user_input='y'):
    """Run process_single_video with every external dependency mocked out.

    Returns (captured_stdout, prompt_count). Raises LoopDidNotTerminate if the
    loop asks for input more than MAX_PROMPTS times.
    """
    prompts = {'count': 0}

    def fake_input(prompt=''):
        prompts['count'] += 1
        if prompts['count'] > MAX_PROMPTS:
            raise LoopDidNotTerminate(
                f"loop asked for input more than {MAX_PROMPTS} times")
        return user_input

    buf = io.StringIO()
    with patch.object(main, 'download_youtube_video', return_value='/tmp/video.mp4'), \
         patch.object(main, 'transcribe_video', return_value='/tmp/video.srt'), \
         patch.object(main, 'parse_srt_to_text',
                      return_value='[00:00:00,000 --> 00:00:01,000] hello'), \
         patch.object(main, 'translate_transcription',
                      return_value='[00:00:00,000 --> 00:00:01,000] 你好'), \
         patch.object(main, 'format_to_markdown', return_value=('zh', 'en')), \
         patch.object(main, 'create_srt_from_transcription', return_value=True), \
         patch.object(main.os.path, 'exists', return_value=srt_exists), \
         patch.object(main, 'process_video_with_subtitles',
                      return_value=process_result), \
         patch('builtins.input', fake_input):
        with redirect_stdout(buf):
            main.process_single_video('https://example.com/watch?v=test')

    return buf.getvalue(), prompts['count']


def test_p1_3_failure_display():
    """P1-3: a failed embed must not print any success checkmark"""
    print("\n=== Testing P1-3: failure must not print success ===")

    output, _ = run_interactive_loop(process_result=(None, None))
    print(f"Captured output: {output.strip()!r}")

    if "✓" in output:
        print("❌ Failure path printed a success checkmark")
        return False
    if "✗" not in output:
        print("❌ Failure path did not print a failure message")
        return False

    print("✅ P1-3 failure display test passed")
    return True


def test_p1_3_success_display():
    """P1-3: a successful embed must still report success (no regression)"""
    print("\n=== Testing P1-3: success still reports success ===")

    output, _ = run_interactive_loop(
        process_result=('/tmp/video_subtitled.mp4', '/tmp/video_subtitled.mp4'))
    print(f"Captured output: {output.strip()!r}")

    if "✓" not in output:
        print("❌ Success path did not print a success message")
        return False
    if "✗" in output:
        print("❌ Success path printed a failure message")
        return False

    print("✅ P1-3 success display test passed")
    return True


def _assert_loop_terminates(label, **kwargs):
    """Shared helper: the loop must prompt exactly once, then exit."""
    try:
        _, prompts = run_interactive_loop(**kwargs)
    except LoopDidNotTerminate as exc:
        print(f"❌ {label}: {exc}")
        return False

    if prompts != 1:
        print(f"❌ {label}: expected 1 prompt, got {prompts}")
        return False

    print(f"✅ {label}: loop terminated after 1 prompt")
    return True


def test_r2_loop_terminates_on_success():
    """R2: loop must exit after a successful run"""
    print("\n=== Testing R2: loop exits on success ===")
    return _assert_loop_terminates(
        "success path",
        process_result=('/tmp/video_subtitled.mp4', '/tmp/video_subtitled.mp4'))


def test_r2_loop_terminates_on_failure():
    """R2: loop must exit when processing fails (the regression that was missed)"""
    print("\n=== Testing R2: loop exits on processing failure ===")
    return _assert_loop_terminates("failure path", process_result=(None, None))


def test_r2_loop_terminates_when_srt_missing():
    """R2: loop must exit when the translated SRT is absent"""
    print("\n=== Testing R2: loop exits when SRT missing ===")
    return _assert_loop_terminates(
        "missing SRT path", process_result=(None, None), srt_exists=False)


def test_r2_loop_terminates_on_no():
    """R2: loop must exit when the user declines"""
    print("\n=== Testing R2: loop exits when user answers n ===")
    return _assert_loop_terminates(
        "declined path", process_result=(None, None), user_input='n')


def main_runner():
    """Run all tests"""
    print("Starting P1 fixes verification tests...")

    tests = [
        test_p1_3_failure_display,
        test_p1_3_success_display,
        test_r2_loop_terminates_on_success,
        test_r2_loop_terminates_on_failure,
        test_r2_loop_terminates_when_srt_missing,
        test_r2_loop_terminates_on_no,
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
    for test_name in passed:
        print(f"  ✅ {test_name}")

    print(f"FAILED: {len(failed)}/{len(tests)}")
    for test_name in failed:
        print(f"  ❌ {test_name}")

    print(f"NOT TESTED: {len(not_tested)}/{len(tests)}")
    for test_name in not_tested:
        print(f"  ⚠️  {test_name}")

    if failed:
        print("❌ Some tests failed")
        return 1
    print("✅ All executed tests passed!")
    return 0


if __name__ == "__main__":
    sys.exit(main_runner())
