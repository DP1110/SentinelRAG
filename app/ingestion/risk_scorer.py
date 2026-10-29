import re
from typing import Tuple, List

# Suspicious instruction patterns commonly found in indirect prompt injection attacks
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions?",
    r"disregard\s+(all\s+)?(previous|prior|above)\s+instructions?",
    r"system\s+override",
    r"you\s+are\s+now\s+(an\s+unrestricted|in\s+developer\s+mode|dan)",
    r"forget\s+(your\s+)?(system\s+prompt|rules|constraints)",
    r"(reveal|print|output|dump|leak)\s+(all\s+)?(passwords|secrets|salaries|confidential|documents|system\s+prompt)",
    r"<\s*/?\s*context(_block)?\s*>",
    r"<\s*admin\s*>",
    r"IMPORTANT:\s*do\s+not\s+mention\s+this",
    r"exfiltrate",
    r"send\s+(this|the\s+above)\s+to\s+https?://",
]


def score_prompt_injection(text: str) -> Tuple[float, List[str]]:
    """
    Analyzes chunk text for signs of indirect prompt injection.
    Returns: (risk_score: float [0.0 - 1.0], matched_patterns: List[str])
    """
    if not text:
        return 0.0, []

    matches = []
    text_lower = text.lower()

    for pattern in INJECTION_PATTERNS:
        found = re.findall(pattern, text_lower, re.IGNORECASE)
        if found:
            matches.append(pattern)

    # Compute risk score based on pattern matches
    match_count = len(matches)
    if match_count == 0:
        score = 0.0
    elif match_count == 1:
        score = 0.65
    elif match_count == 2:
        score = 0.85
    else:
        score = 0.99

    return min(score, 1.0), matches
