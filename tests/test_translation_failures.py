#!/usr/bin/env python3
"""
Test script for translation failure scenarios.
"""

import os
import sys
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import translation_service


ERROR_PAGE = (
    "Error 500 (Server Error)!!1500.That's an error.There was an error. "
    "Please try again later.That's all we know."
)


class FakeGoogleTranslator:
    """Stand-in for GoogleTranslator that replays a scripted response sequence.

    translate_to_traditional_chinese constructs a new translator for every
    attempt, so the call counter has to live on the class for a retry sequence
    to be observable at all. Once the script runs out the last entry repeats,
    which is what "this line keeps failing" looks like.
    """

    _responses = [""]
    _calls = 0
    _by_text = None
    _delay = 0.0

    @classmethod
    def script(cls, responses):
        """Set the response sequence and rewind the counter."""
        cls._responses = list(responses)
        cls._calls = 0
        cls._by_text = None

    @classmethod
    def script_by_text(cls, mapping):
        """Answer according to the input text rather than the call order.

        translate_transcription sends its lines concurrently, so call order is
        no longer deterministic and a positional script would pair lines with
        translations at random. Keying on the input is order independent, and
        stricter besides: it catches a translation landing on the wrong line,
        which a positional script cannot see at all.
        """
        cls._by_text = dict(mapping)
        cls._calls = 0

    def __init__(self, source='auto', target='zh-TW'):
        self.source = source
        self.target = target

    def translate(self, text):
        if FakeGoogleTranslator._delay:
            time.sleep(FakeGoogleTranslator._delay)
        if FakeGoogleTranslator._by_text is not None:
            return FakeGoogleTranslator._by_text[text]
        index = FakeGoogleTranslator._calls
        FakeGoogleTranslator._calls += 1
        if index < len(FakeGoogleTranslator._responses):
            return FakeGoogleTranslator._responses[index]
        return FakeGoogleTranslator._responses[-1]


def test_error_page_returns_none():
    """Scenario 1: Translator returns Google error page -> should return None."""
    print("\n=== Test 1: Error page returns None ===")
    
    # Save original
    original_google_translator = translation_service.GoogleTranslator

    # Both attempts hit the error page, so the call must give up and return None.
    FakeGoogleTranslator.script([ERROR_PAGE, ERROR_PAGE])
    translation_service.GoogleTranslator = FakeGoogleTranslator
    
    try:
        result = translation_service.translate_to_traditional_chinese("Hello world")
        
        if result is None:
            print("✅ Test 1 passed: Error page correctly returns None")
            return True
        else:
            print(f"❌ Test 1 failed: Expected None, got: {result!r}")
            return False
    finally:
        translation_service.GoogleTranslator = original_google_translator


def test_retry_then_success():
    """Scenario 2: First call returns error page, second returns normal translation -> should return translation."""
    print("\n=== Test 2: Retry then success ===")
    
    original_google_translator = translation_service.GoogleTranslator
    
    success_response = "你好世界"

    # First attempt fails, the retry succeeds.
    FakeGoogleTranslator.script([ERROR_PAGE, success_response])
    translation_service.GoogleTranslator = FakeGoogleTranslator
    
    try:
        result = translation_service.translate_to_traditional_chinese("Hello world")
        
        if result == success_response:
            print("✅ Test 2 passed: Retry works, returns successful translation")
            return True
        else:
            print(f"❌ Test 2 failed: Expected {success_response!r}, got: {result!r}")
            return False
    finally:
        translation_service.GoogleTranslator = original_google_translator


def test_transcription_preserves_lines_on_failure():
    """Scenario 3: One line fails persistently -> output line count matches input, failed line preserves original."""
    print("\n=== Test 3: Transcription preserves lines on failure ===")
    
    original_google_translator = translation_service.GoogleTranslator
    
    # Every line fails on both attempts, whatever order they are sent in.
    FakeGoogleTranslator.script_by_text({
        "Hello": ERROR_PAGE,
        "World": ERROR_PAGE,
        "Test": ERROR_PAGE,
    })
    translation_service.GoogleTranslator = FakeGoogleTranslator

    try:
        input_text = """[00:00:01] Hello
[00:00:03] World
[00:00:05] Test"""
        
        result = translation_service.translate_transcription(input_text)
        
        if result is None:
            print("❌ Test 3 failed: Result is None")
            return False
        
        input_lines = input_text.split('\n')
        output_lines = result.split('\n')
        
        if len(output_lines) != len(input_lines):
            print(f"❌ Test 3 failed: Line count mismatch. Input: {len(input_lines)}, Output: {len(output_lines)}")
            return False
        
        # Check that the failed line preserves original text with timestamp
        # All lines should fail, so all should preserve original
        if output_lines[0] != input_lines[0]:
            print(f"❌ Test 3 failed: Line 1 not preserved. Expected: {input_lines[0]!r}, Got: {output_lines[0]!r}")
            return False
        
        if output_lines[1] != input_lines[1]:
            print(f"❌ Test 3 failed: Line 2 not preserved. Expected: {input_lines[1]!r}, Got: {output_lines[1]!r}")
            return False
        
        if output_lines[2] != input_lines[2]:
            print(f"❌ Test 3 failed: Line 3 not preserved. Expected: {input_lines[2]!r}, Got: {output_lines[2]!r}")
            return False
        
        print("✅ Test 3 passed: All lines preserved with original text and timestamps")
        return True
    finally:
        translation_service.GoogleTranslator = original_google_translator


def test_all_normal_translation():
    """Scenario 4: All lines translate normally -> line count matches, content is translated."""
    print("\n=== Test 4: All normal translation ===")
    
    original_google_translator = translation_service.GoogleTranslator
    
    # One successful translation per line, no retries expected. Keyed by input
    # so that a line receiving another line's translation fails the test.
    FakeGoogleTranslator.script_by_text({
        "Hello": "你好",
        "World": "世界",
        "Test": "測試",
    })
    translation_service.GoogleTranslator = FakeGoogleTranslator
    
    try:
        input_text = """[00:00:01] Hello
[00:00:03] World
[00:00:05] Test"""
        
        result = translation_service.translate_transcription(input_text)
        
        if result is None:
            print("❌ Test 4 failed: Result is None")
            return False
        
        input_lines = input_text.split('\n')
        output_lines = result.split('\n')
        
        if len(output_lines) != len(input_lines):
            print(f"❌ Test 4 failed: Line count mismatch. Input: {len(input_lines)}, Output: {len(output_lines)}")
            return False
        
        # Check that translations are in the output
        expected_translations = ["你好", "世界", "測試"]
        for i, (expected, output_line) in enumerate(zip(expected_translations, output_lines)):
            if expected not in output_line:
                print(f"❌ Test 4 failed: Line {i+1} missing translation. Expected to contain: {expected!r}, Got: {output_line!r}")
                return False
            
            # Check timestamp is preserved
            if not output_line.startswith(f"[00:00:0{2*i+1}]"):
                print(f"❌ Test 4 failed: Line {i+1} timestamp not preserved. Got: {output_line!r}")
                return False
        
        print("✅ Test 4 passed: All lines translated correctly with timestamps preserved")
        return True
    finally:
        translation_service.GoogleTranslator = original_google_translator


def test_concurrent_lines_keep_their_own_translation():
    """Scenario 5: Many slow lines -> sent concurrently, each keeps its own translation."""
    print("\n=== Test 5: Concurrent lines keep their own translation ===")

    original_google_translator = translation_service.GoogleTranslator

    line_count = 40
    delay = 0.05
    sources = [f"line number {i}" for i in range(line_count)]
    mapping = {source: f"譯文{i}" for i, source in enumerate(sources)}

    FakeGoogleTranslator.script_by_text(mapping)
    FakeGoogleTranslator._delay = delay
    translation_service.GoogleTranslator = FakeGoogleTranslator

    try:
        input_text = '\n'.join(
            f"[00:00:{i:02d}] {source}" for i, source in enumerate(sources))

        started = time.monotonic()
        result = translation_service.translate_transcription(input_text)
        elapsed = time.monotonic() - started

        if result is None:
            print("❌ Test 5 failed: Result is None")
            return False

        output_lines = result.split('\n')
        if len(output_lines) != line_count:
            print(f"❌ Test 5 failed: Line count mismatch. Expected {line_count}, got {len(output_lines)}")
            return False

        # The point of the test: line i must carry translation i, not whichever
        # response happened to come back first.
        for i, output_line in enumerate(output_lines):
            expected = f"[00:00:{i:02d}] 譯文{i}"
            if output_line != expected:
                print(f"❌ Test 5 failed: Line {i} mismatched. Expected {expected!r}, got {output_line!r}")
                return False

        # Sequential would take line_count * delay; concurrency has to beat that
        # by a wide margin or the pool is not actually overlapping anything.
        sequential = line_count * delay
        if elapsed > sequential / 2:
            print(f"❌ Test 5 failed: No concurrency. Took {elapsed:.2f}s, sequential would be {sequential:.2f}s")
            return False

        print(f"✅ Test 5 passed: {line_count} lines correctly paired, "
              f"{elapsed:.2f}s vs {sequential:.2f}s sequential")
        return True
    finally:
        FakeGoogleTranslator._delay = 0.0
        translation_service.GoogleTranslator = original_google_translator


def main():
    """Run all tests."""
    print("Starting translation failure tests...")
    
    tests = [
        test_error_page_returns_none,
        test_retry_then_success,
        test_transcription_preserves_lines_on_failure,
        test_all_normal_translation,
        test_concurrent_lines_keep_their_own_translation,
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
            import traceback
            traceback.print_exc()
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