import re
import unicodedata

# Zero-width and invisible unicode characters often used in steganography / prompt injection
ZERO_WIDTH_CHARS = [
    "\u200b",  # zero-width space
    "\u200c",  # zero-width non-joiner
    "\u200d",  # zero-width joiner
    "\ufeff",  # zero-width no-break space (BOM)
    "\u200e",  # left-to-right mark
    "\u200f",  # right-to-left mark
    "\u202a",  # left-to-right embedding
    "\u202b",  # right-to-left embedding
    "\u202c",  # pop directional formatting
    "\u202d",  # left-to-right override
    "\u202e",  # right-to-left override
]


def clean_text(text: str) -> str:
    """Normalizes text, strips zero-width hidden characters, and sanitizes whitespace."""
    if not text:
        return ""

    # 1. Strip zero-width characters
    for ch in ZERO_WIDTH_CHARS:
        text = text.replace(ch, "")

    # 1b. Strip hidden HTML comments (often used for hidden prompt injection)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)

    # 2. Normalize unicode (NFKC)
    text = unicodedata.normalize("NFKC", text)

    # 3. Normalize windows/mac newlines to \n
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 4. Collapse runs of horizontal whitespace (spaces/tabs) to a single space
    lines = []
    for line in text.split("\n"):
        cleaned_line = re.sub(r"[ \t]+", " ", line).strip()
        lines.append(cleaned_line)

    # 5. Collapse excessive vertical blank lines (>2 blank lines to 2)
    collapsed_text = "\n".join(lines)
    collapsed_text = re.sub(r"\n{3,}", "\n\n", collapsed_text).strip()

    return collapsed_text
