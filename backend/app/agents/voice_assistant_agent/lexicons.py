"""
Lexicons for Voice Assistant Agent

Contains intent words for interruption control and backchannel words for acknowledgment.
"""

# Intent words that trigger immediate stop and switch to listening mode
AGENT_INTENT_WORDS = [
    "stop",
    "wait",
    "pause",
    "hold",
    "enough",
    "cancel",
    "quit",
    "exit",
    "leave",
    "forget",
    "stop it",
    "halt",
    "terminate",
    "abort"
]

# Backchannel words for brief acknowledgment without interruption
AGENT_BACKCHANNEL_WORDS = [
    "okay",
    "ok",
    "yeah",
    "yes",
    "yep",
    "uh",
    "um",
    "hmm",
    "hm",
    "mhm",
    "uh-huh",
    "uhhuh",
    "right",
    "sure",
    "gotcha",
    "oh",
    "ah",
    "alright",
    "wow",
    "omg",
    "great",
    "excellent",
    "perfect",
    "huh",
    "uhm"
]

# Confirmation phrases that indicate user approval to proceed
CONFIRMATION_PHRASES = [
    "yes",
    "yeah",
    "yep",
    "sure",
    "go ahead",
    "proceed",
    "confirm",
    "confirmed",
    "do it",
    "execute",
    "start",
    "begin",
    "let's go",
    "sounds good",
    "that's correct",
    "that's right",
    "correct",
    "right",
    "exactly",
    "perfect",
    "looks good",
    "approved",
    "okay proceed",
    "ok proceed"
]

# Rejection phrases that indicate user wants to modify
REJECTION_PHRASES = [
    "no",
    "nope",
    "wait",
    "hold on",
    "not yet",
    "change",
    "modify",
    "edit",
    "wrong",
    "incorrect",
    "that's not right",
    "let me change",
    "actually",
    "nevermind",
    "never mind",
    "scratch that",
    "start over",
    "redo"
]


def normalize_text(text: str) -> str:
    """Normalize text for comparison (lowercase, strip whitespace)."""
    return text.lower().strip()


def contains_intent_word(text: str) -> bool:
    """Check if text contains any intent word (for interruption)."""
    normalized = normalize_text(text)
    words = normalized.split()
    
    # Check single words
    for word in words:
        if word in AGENT_INTENT_WORDS:
            return True
    
    # Check multi-word phrases
    for phrase in AGENT_INTENT_WORDS:
        if " " in phrase and phrase in normalized:
            return True
    
    return False


def contains_backchannel_word(text: str) -> bool:
    """Check if text contains only backchannel words (acknowledgment)."""
    normalized = normalize_text(text)
    words = normalized.split()
    
    # If text is only backchannel words
    if all(word in AGENT_BACKCHANNEL_WORDS for word in words):
        return True
    
    return False


def is_confirmation(text: str) -> bool:
    """Check if text indicates user confirmation."""
    normalized = normalize_text(text)
    
    for phrase in CONFIRMATION_PHRASES:
        if phrase in normalized:
            return True
    
    return False


def is_rejection(text: str) -> bool:
    """Check if text indicates user rejection/modification request."""
    normalized = normalize_text(text)
    
    for phrase in REJECTION_PHRASES:
        if phrase in normalized:
            return True
    
    return False
