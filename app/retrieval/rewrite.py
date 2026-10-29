import re
from typing import Optional


def rewrite_query(query: str, chat_history: Optional[str] = None) -> str:
    """
    Expands abbreviations and contextualizes follow-up queries using chat history.
    """
    cleaned_query = query.strip()
    
    # Common enterprise abbreviation expansions
    abbreviations = {
        r"\bpto\b": "paid time off PTO vacation policy",
        r"\bhr\b": "human resources HR",
        r"\beng\b": "engineering",
        r"\bci/cd\b": "continuous integration continuous deployment CI/CD pipeline",
        r"\bk8s\b": "kubernetes k8s cluster",
    }
    
    expanded = cleaned_query
    for pattern, repl in abbreviations.items():
        expanded = re.sub(pattern, repl, expanded, flags=re.IGNORECASE)
        
    return expanded
