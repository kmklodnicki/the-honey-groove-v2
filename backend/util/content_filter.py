"""
Smart Moderation Engine: Fuzzy off-platform payment detection,
profanity filtering, and contact-info leak prevention.
"""
import re

# ──────────────────────────────────────────────
# LEET-SPEAK MAPPINGS
# ──────────────────────────────────────────────
LEET_MAP = {
    'a': r'[a4@\^]',
    'e': r'[e3\u00a3]',
    'i': r'[i1!l\|]',
    'o': r'[o0]',
    's': r'[s5\$]',
    't': r'[t7\+]',
    'l': r'[l1\|i]',
    'u': r'[uv\u00fc]',
}

SEP = r'[\s._\-*\\/,;:\'"`~]*'

# ──────────────────────────────────────────────
# OFF-PLATFORM PAYMENT DETECTION
# ──────────────────────────────────────────────
PAYMENT_TARGETS = [
    "venmo", "paypal", "cashapp", "cash app", "zelle",
    "crypto", "bitcoin", "ethereum",
    "wire transfer", "western union", "bank transfer",
]

def _build_leet_pattern(word: str) -> str:
    """Single word → regex with leet + optional separators between chars."""
    parts = []
    for ch in word.lower():
        parts.append(LEET_MAP.get(ch, re.escape(ch)))
    return SEP.join(parts)

def _build_multiword_pattern(phrase: str) -> str:
    """Multi-word phrase → regex with flexible internal spacing."""
    result = []
    for ch in phrase.lower():
        if ch == ' ':
            result.append(r'[\s._\-*]+')
        else:
            result.append(LEET_MAP.get(ch, re.escape(ch)))
    return ''.join(result)

_PAYMENT_PATTERNS = []
for target in PAYMENT_TARGETS:
    raw = _build_multiword_pattern(target) if ' ' in target else _build_leet_pattern(target)
    _PAYMENT_PATTERNS.append((target, re.compile(raw, re.IGNORECASE)))

BLOCK_MESSAGE = (
    "Safety First! To protect the Hive, we don't allow off-platform payment "
    "mentions. Please keep transactions within The Honeypot."
)

def detect_offplatform_payment(text: str) -> tuple[bool, list[str]]:
    """Scan text for off-platform payment references."""
    if not text:
        return False, []
    matched = []
    for keyword, pattern in _PAYMENT_PATTERNS:
        if pattern.search(text):
            matched.append(keyword)
    return bool(matched), matched


# ──────────────────────────────────────────────
# PROFANITY BLACKLIST (with leet-speak support)
# ──────────────────────────────────────────────
_PROFANITY_WORDS = [
    "shit", "fuck", "cunt", "dick", "cock", "pussy", "bitch",
    "asshole", "nigger", "nigga", "faggot", "retard",
    "whore", "slut", "twat",
]

_PROFANITY_PATTERNS = []
for word in _PROFANITY_WORDS:
    raw = _build_leet_pattern(word)
    _PROFANITY_PATTERNS.append((word, re.compile(raw, re.IGNORECASE)))

PROFANITY_BLOCK_MESSAGE = (
    "That username contains language that isn't allowed on The Honey Groove. "
    "Please choose a different username."
)

def detect_profanity(text: str) -> tuple[bool, list[str]]:
    """Check text for profane words including leetspeak variants."""
    if not text:
        return False, []
    matched = []
    for word, pattern in _PROFANITY_PATTERNS:
        if pattern.search(text):
            matched.append(word)
    return bool(matched), matched


# ──────────────────────────────────────────────
# USERNAME VALIDATION (profanity + payment)
# ──────────────────────────────────────────────
USERNAME_BLOCK_MESSAGE = (
    "That username isn't allowed. Please choose a different one."
)

def validate_username(username: str) -> tuple[bool, str]:
    """Validate a username against profanity and payment filters.

    Returns (is_valid: bool, error_message: str).
    """
    if not username:
        return False, "Username is required."

    flagged, _ = detect_profanity(username)
    if flagged:
        return False, PROFANITY_BLOCK_MESSAGE

    flagged, _ = detect_offplatform_payment(username)
    if flagged:
        return False, "Usernames cannot contain payment service references."

    return True, ""


# ──────────────────────────────────────────────
# BIO CONTACT INFO LEAK DETECTION
# ──────────────────────────────────────────────
# Email pattern: word@word.tld — also catches (at) and [at] obfuscation
_EMAIL_RE = re.compile(
    r'[a-zA-Z0-9._%+\-]+\s*(?:@|\(at\)|\[at\]|@)\s*[a-zA-Z0-9.\-]+\s*[.\(\[]\s*[a-zA-Z]{2,}',
    re.IGNORECASE,
)

# Phone pattern: sequences of 7+ digits (with optional separators)
_PHONE_RE = re.compile(
    r'(?:\+?\d[\s.\-()]*){7,}',
)

BIO_CONTACT_BLOCK_MESSAGE = (
    "To keep the community safe, bios cannot contain email addresses or "
    "phone numbers. Please use The Honey Groove's messaging system instead."
)

def detect_contact_info(text: str) -> tuple[bool, list[str]]:
    """Scan text for email addresses and phone numbers.

    Returns (flagged: bool, types_found: list[str]).
    """
    if not text:
        return False, []
    found = []
    if _EMAIL_RE.search(text):
        found.append("email")
    if _PHONE_RE.search(text):
        found.append("phone")
    return bool(found), found


def validate_bio(text: str) -> tuple[bool, str]:
    """Full bio validation: payment mentions + contact info leaks.

    Returns (is_valid: bool, error_message: str).
    """
    if not text:
        return True, ""

    flagged, _ = detect_offplatform_payment(text)
    if flagged:
        return False, BLOCK_MESSAGE

    flagged, _ = detect_contact_info(text)
    if flagged:
        return False, BIO_CONTACT_BLOCK_MESSAGE

    return True, ""
