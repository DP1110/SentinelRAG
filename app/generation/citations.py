import re
from typing import List, Dict, Any, Tuple
from app.retrieval.hybrid import RetrievalCandidate


class CitationInfo:
    def __init__(self, citation_id: int, title: str, url: str, chunk_ref: str, snippet: str):
        self.id = citation_id
        self.title = title
        self.url = url
        self.chunk_ref = chunk_ref
        self.snippet = snippet

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "chunk_ref": self.chunk_ref,
            "snippet": self.snippet,
        }


def verify_and_extract_citations(
    raw_answer: str,
    candidates: List[RetrievalCandidate],
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Parses bracketed citations like [1], [2] in raw_answer.
    Verifies that each cited index is within 1 <= index <= len(candidates).
    Drops invalid citations and builds structured citation metadata.
    """
    if not candidates:
        # Strip any hallucinated citations if candidates list was empty
        cleaned_answer = re.sub(r"\[\d+\]", "", raw_answer).strip()
        return cleaned_answer, []

    cited_indices = set()
    matches = re.findall(r"\[([\d,\s]+)\]", raw_answer)
    for m in matches:
        for part in m.split(","):
            part_clean = part.strip()
            if part_clean.isdigit():
                val = int(part_clean)
                if 1 <= val <= len(candidates):
                    cited_indices.add(val)

    # Clean bogus citations that are outside candidate range
    def replace_citation(match):
        raw_inner = match.group(1)
        valid_parts = []
        for part in raw_inner.split(","):
            part_clean = part.strip()
            if part_clean.isdigit():
                val = int(part_clean)
                if val in cited_indices:
                    valid_parts.append(str(val))
        if valid_parts:
            return f"[{', '.join(valid_parts)}]"
        return ""  # Remove bogus citation

    cleaned_answer = re.sub(r"\[([\d,\s]+)\]", replace_citation, raw_answer).strip()
    # Normalize multiple adjacent spaces created by dropped citations
    cleaned_answer = re.sub(r"\s{2,}", " ", cleaned_answer)

    # Build citation list sorted by citation ID
    citations: List[Dict[str, Any]] = []
    for idx in sorted(list(cited_indices)):
        c = candidates[idx - 1]
        snippet = c.text[:200] + ("..." if len(c.text) > 200 else "")
        info = CitationInfo(
            citation_id=idx,
            title=c.doc_title,
            url=c.doc_url,
            chunk_ref=c.chunk_id,
            snippet=snippet,
        )
        citations.append(info.to_dict())

    return cleaned_answer, citations
