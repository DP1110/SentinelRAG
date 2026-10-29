import re
from typing import List, Dict, Any
from app.ingestion.cleaner import clean_text
from app.ingestion.risk_scorer import score_prompt_injection


class ChunkItem:
    def __init__(
        self,
        ordinal: int,
        text: str,
        metadata: Dict[str, Any],
        risk_score: float = 0.0,
    ):
        self.ordinal = ordinal
        self.text = text
        self.metadata = metadata
        self.risk_score = risk_score


def chunk_document(
    raw_content: str,
    doc_id: str,
    doc_title: str,
    target_chars: int = 1500,
    overlap_chars: int = 200,
) -> List[ChunkItem]:
    """
    Performs structure-aware splitting on headings, code blocks, and paragraphs.
    Calculates prompt injection risk scores for each chunk.
    """
    cleaned = clean_text(raw_content)
    if not cleaned:
        return []

    # 1. First split by major markdown headings or section breaks
    section_pattern = r"(?=(?:^|\n)#{1,4}\s+)"
    raw_sections = re.split(section_pattern, cleaned)
    sections = [s.strip() for s in raw_sections if s.strip()]

    chunks: List[ChunkItem] = []
    ordinal = 0

    for sec in sections:
        # Determine heading if present
        heading_match = re.match(r"^(#{1,4}\s+[^\n]+)", sec)
        current_heading = heading_match.group(1).strip() if heading_match else doc_title

        # If section is small enough, keep as single chunk
        if len(sec) <= target_chars:
            risk_score, _ = score_prompt_injection(sec)
            chunks.append(
                ChunkItem(
                    ordinal=ordinal,
                    text=sec,
                    metadata={
                        "doc_id": doc_id,
                        "doc_title": doc_title,
                        "section": current_heading,
                        "char_count": len(sec),
                    },
                    risk_score=risk_score,
                )
            )
            ordinal += 1
        else:
            # Split section by paragraphs or code blocks
            paragraphs = re.split(r"\n\s*\n", sec)
            current_buffer = ""

            for p in paragraphs:
                p = p.strip()
                if not p:
                    continue

                if len(current_buffer) + len(p) + 2 <= target_chars:
                    if current_buffer:
                        current_buffer += "\n\n" + p
                    else:
                        current_buffer = p
                else:
                    if current_buffer:
                        risk_score, _ = score_prompt_injection(current_buffer)
                        chunks.append(
                            ChunkItem(
                                ordinal=ordinal,
                                text=current_buffer,
                                metadata={
                                    "doc_id": doc_id,
                                    "doc_title": doc_title,
                                    "section": current_heading,
                                    "char_count": len(current_buffer),
                                },
                                risk_score=risk_score,
                            )
                        )
                        ordinal += 1
                        # Maintain overlap from end of previous buffer
                        overlap_text = current_buffer[-overlap_chars:] if len(current_buffer) > overlap_chars else ""
                        current_buffer = (overlap_text + "\n\n" + p).strip() if overlap_text else p
                    else:
                        # Paragraph itself is huge, slice it
                        for start_idx in range(0, len(p), target_chars - overlap_chars):
                            sub_text = p[start_idx : start_idx + target_chars]
                            risk_score, _ = score_prompt_injection(sub_text)
                            chunks.append(
                                ChunkItem(
                                    ordinal=ordinal,
                                    text=sub_text,
                                    metadata={
                                        "doc_id": doc_id,
                                        "doc_title": doc_title,
                                        "section": current_heading,
                                        "char_count": len(sub_text),
                                    },
                                    risk_score=risk_score,
                                )
                            )
                            ordinal += 1
                        current_buffer = ""

            if current_buffer:
                risk_score, _ = score_prompt_injection(current_buffer)
                chunks.append(
                    ChunkItem(
                        ordinal=ordinal,
                        text=current_buffer,
                        metadata={
                            "doc_id": doc_id,
                            "doc_title": doc_title,
                            "section": current_heading,
                            "char_count": len(current_buffer),
                        },
                        risk_score=risk_score,
                    )
                )
                ordinal += 1

    return chunks
