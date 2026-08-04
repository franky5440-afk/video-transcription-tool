#!/usr/bin/env python3
"""
Test script for the source-language check that decides whether to translate.
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import language_detect
from language_detect import is_traditional_chinese


# Simplified samples are derived from the audited pair table rather than typed
# out, so the two never drift apart and the test adds no character data of its
# own to keep in sync.
TO_SIMPLIFIED = str.maketrans(
    language_detect._PAIRS[0::2], language_detect._PAIRS[1::2])

TRADITIONAL_SAMPLE = (
    "[00:00:01] 這個節目今天要說的是一本新書\n"
    "[00:00:04] 它的作者長期研究意識這個題目\n"
    "[00:00:07] 我們會從神經科學的角度來看\n"
    "[00:00:10] 這本書最特別的地方在於\n"
    "[00:00:13] 他沒有給出一個標準答案\n"
    "[00:00:16] 而是讓讀者自己去想\n"
)


def test_traditional_is_detected():
    """A Traditional Chinese transcript needs no translation."""
    print("\n=== Test 1: Traditional Chinese is detected ===")

    if is_traditional_chinese(TRADITIONAL_SAMPLE):
        print("✅ Test 1 passed: Traditional Chinese recognised")
        return True
    print("❌ Test 1 failed: Traditional Chinese not recognised")
    return False


def test_simplified_is_translated():
    """Simplified Chinese must still be translated: converting it is the point."""
    print("\n=== Test 2: Simplified Chinese still gets translated ===")

    simplified = TRADITIONAL_SAMPLE.translate(TO_SIMPLIFIED)
    if simplified == TRADITIONAL_SAMPLE:
        print("❌ Test 2 failed: sample contains no convertible characters")
        return False

    if not is_traditional_chinese(simplified):
        print("✅ Test 2 passed: Simplified Chinese routed to the translator")
        return True
    print("❌ Test 2 failed: Simplified Chinese was mistaken for Traditional")
    return False


def test_single_simplified_character_is_enough():
    """One simplified character anywhere is enough to keep translating."""
    print("\n=== Test 3: A single simplified character is enough ===")

    first_traditional = language_detect._PAIRS[0]
    first_simplified = language_detect._PAIRS[1]
    mixed = TRADITIONAL_SAMPLE.replace(first_traditional, first_simplified, 1)

    if mixed == TRADITIONAL_SAMPLE:
        print("❌ Test 3 failed: sample never contained the character to swap")
        return False

    if not is_traditional_chinese(mixed):
        print("✅ Test 3 passed: one simplified character routes to the translator")
        return True
    print("❌ Test 3 failed: a simplified character slipped through")
    return False


def test_non_chinese_is_translated():
    """English, empty and too-short inputs all keep the existing behaviour."""
    print("\n=== Test 4: Non-Chinese input still gets translated ===")

    cases = {
        "english": "[00:00:01] Hello everyone and welcome to this talk\n"
                   "[00:00:04] today we are going to look at consciousness",
        "empty": "",
        "too short to judge": "[00:00:01] 你好",
        "bilingual": "[00:00:01] 這個 model 的 attention mechanism "
                     "用 transformer 來 encode 整段 sequence",
    }

    for label, text in cases.items():
        if is_traditional_chinese(text):
            print(f"❌ Test 4 failed: {label!r} was wrongly treated as Traditional Chinese")
            return False

    print(f"✅ Test 4 passed: all {len(cases)} non-Chinese cases route to the translator")
    return True


def main():
    """Run all tests."""
    print("Starting language detection tests...")

    tests = [
        test_traditional_is_detected,
        test_simplified_is_translated,
        test_single_simplified_character_is_enough,
        test_non_chinese_is_translated,
    ]

    passed = []
    failed = []

    for test in tests:
        try:
            if test():
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
    for test_name in passed:
        print(f"  ✅ {test_name}")

    print(f"FAILED: {len(failed)}/{len(tests)}")
    for test_name in failed:
        print(f"  ❌ {test_name}")

    if failed:
        print("❌ Some tests failed")
        return 1
    print("✅ All executed tests passed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
