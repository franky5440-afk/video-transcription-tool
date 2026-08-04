#!/usr/bin/env python3
"""
Language Detection Module

Decides whether a transcription still needs to be sent to the translator.

A Chinese-language video already transcribes to Chinese, so running it through
"translate to Traditional Chinese" is at best a no-op. Measured on a 32 minute
Chinese video (2026-08-05): 519 of 850 subtitle lines came back altered, and the
alterations included outright meaning changes. Skipping that round trip protects
the transcript and removes the slowest step of the run.

The check only reports True when it is confident, because being wrong in that
direction silently ships an untranslated transcript. Anything ambiguous falls
through to the existing behaviour: translate it.
"""

# Traditional/simplified pairs, written adjacently so the two sets stay aligned
# and can be checked by eye. These are the highest frequency characters that
# differ between the two scripts, which is all that is needed here: any text as
# long as a transcript hits many of them.
_PAIRS = (
    "這这個个們们來来說说時时對对開开會会發发"
    "國国學学長长邊边進进還还過过無无見见題题實实"
    "產产東东車车馬马點点給给經经樣样種种難难"
    "電电腦脑網网話话讀读寫写書书聽听買买賣卖"
    "萬万與与專专業业愛爱興兴舊旧當当應应"
)

_TRADITIONAL_ONLY = frozenset(_PAIRS[0::2])
_SIMPLIFIED_ONLY = frozenset(_PAIRS[1::2])

# How much of the alphabetic content must be Chinese before the text counts as a
# Chinese transcript. Occasional Latin terms ("AI") are expected and fine; a
# genuinely bilingual talk drops below this and gets translated as before.
_MIN_CJK_RATIO = 0.9

# Enough traditional-only characters to be a positive signal rather than a text
# that merely happens to avoid simplified forms.
_MIN_TRADITIONAL_HITS = 5


def _is_cjk(char: str) -> bool:
    """True for CJK unified ideographs (the range Chinese text actually uses)."""
    return "一" <= char <= "鿿"


def is_traditional_chinese(text: str) -> bool:
    """
    Reports whether the text is already Traditional Chinese throughout.

    Returns True only when translation would be a no-op. Everything else --
    English, Japanese, Simplified Chinese, bilingual content, text too short to
    judge -- returns False so the caller keeps translating.

    Args:
        text (str): The transcription text to inspect.

    Returns:
        bool: True if the text is confidently Traditional Chinese already.
    """
    if not text:
        return False

    cjk = 0
    latin = 0
    traditional_hits = 0

    for char in text:
        if _is_cjk(char):
            cjk += 1
            if char in _SIMPLIFIED_ONLY:
                # One simplified character is enough: converting the script is
                # exactly what the translation step is useful for.
                return False
            if char in _TRADITIONAL_ONLY:
                traditional_hits += 1
        elif char.isalpha():
            latin += 1

    if cjk == 0:
        return False
    if cjk / (cjk + latin) < _MIN_CJK_RATIO:
        return False
    return traditional_hits >= _MIN_TRADITIONAL_HITS


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("usage: language_detect.py <text-file>")
        sys.exit(2)

    with open(sys.argv[1], encoding="utf-8") as handle:
        print(is_traditional_chinese(handle.read()))
