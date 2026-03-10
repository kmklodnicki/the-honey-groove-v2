"""
Smart Moderation Engine: Fuzzy off-platform payment detection.

Detects payment service mentions even through leetspeak, spacing tricks,
and special character obfuscation (e.g. "v3nm0", "p@yp@l", "c a $ h a p p").
"""
import re

# Leet-speak character mappings
LEET_MAP = {
    'a': r'[a4@\^]',
    'e': r'[e3\u00a3]',
    'i': r'[i1!l\|]',
    'o': r'[o0]',
    's': r'[s5\$]',
    't': r'[t7\+]',
    'l': r'[l1\|i]',
}

# Optional separator between letters: whitespace, dots, dashes, underscores, asterisks
SEP = r'[\s._\-*\\/,;:\'"`~]*'

# Target payment words and their aliases
PAYMENT_TARGETS = [
    "venmo",
    "paypal",
    "cashapp",
    "cash app",
    "zelle",
    "crypto",
    "bitcoin",
    "ethereum",
    "wire transfer",
    "western union",
    "bank transfer",
]


def _build_fuzzy_pattern(word: str) -> str:
    """Build a regex pattern for a word that handles leetspeak + separators."""
    parts = []
    for ch in word.lower():
        if ch == ' ':
            parts.append(r'[\s._\-*]+')
        elif ch in LEET_MAP:
            parts.append(LEET_MAP[ch])
        else:
            parts.append(re.escape(ch))
    return SEP.join(parts) if ' ' not in word else ''.join(parts)


# Pre-compile all patterns
_PATTERNS = []
for target in PAYMENT_TARGETS:
    if ' ' in target:
        # Multi-word: build pattern with flexible space
        raw = _build_fuzzy_pattern(target)
    else:
        # Single word: insert separators between each char pattern
        char_patterns = []
        for ch in target.lower():
            if ch in LEET_MAP:
                char_patterns.append(LEET_MAP[ch])
            else:
                char_patterns.append(re.escape(ch))
        raw = SEP.join(char_patterns)
    _PATTERNS.append((target, re.compile(raw, re.IGNORECASE)))


BLOCK_MESSAGE = (
    "Safety First! To protect the Hive, we don't allow off-platform payment "
    "mentions. Please keep transactions within The Honeypot."
)


def detect_offplatform_payment(text: str) -> tuple[bool, list[str]]:
    """Scan text for off-platform payment references.

    Returns (flagged: bool, matched_keywords: list[str]).
    Handles leetspeak, spacing tricks, and character obfuscation.
    """
    if not text:
        return False, []

    matched = []
    for keyword, pattern in _PATTERNS:
        if pattern.search(text):
            matched.append(keyword)

    return bool(matched), matched
