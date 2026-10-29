import os
from typing import Dict, Any


def parse_content(raw_text: str, filename: str = "document.txt") -> Dict[str, Any]:
    """
    Parses content according to file type.
    Handles Markdown, Plain text, and Code.
    """
    ext = os.path.splitext(filename)[1].lower()
    file_type = "text"

    if ext in [".md", ".markdown"]:
        file_type = "markdown"
    elif ext in [".py", ".js", ".ts", ".html", ".css", ".go", ".rs", ".sql", ".sh"]:
        file_type = "code"
    elif ext == ".pdf":
        file_type = "pdf"
    elif ext in [".doc", ".docx"]:
        file_type = "docx"

    return {
        "text": raw_text,
        "file_type": file_type,
        "filename": filename,
    }
