import re
from typing import Optional, List
from app.generation.llm_adapters.base import BaseLLMAdapter


class MockLLMAdapter(BaseLLMAdapter):
    """
    Deterministic grounded LLM adapter for automated test suites and CI.
    Extracts answers strictly from provided context blocks with bracketed citations [N].
    Abstains when context is insufficient.
    Neutralizes prompt injections.
    """

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        # 1. Check if context blocks exist
        context_blocks = re.findall(
            r'<context_block id="(\d+)" doc_id="([^"]+)" doc_title="([^"]+)">\n(.*?)\n</context_block>',
            prompt,
            re.DOTALL,
        )

        if not context_blocks:
            return "I do not have sufficient accessible information to answer this question."

        # Extract question
        q_match = re.search(r"User Question:\s*(.*?)(?:\n|$)", prompt)
        question = q_match.group(1).strip() if q_match else ""
        q_words = set(re.findall(r"\w+", question.lower()))

        # Remove stop words for matching
        stop_words = {
            "what", "is", "our", "the", "a", "an", "for", "in", "of", "to", "and", "do", "we",
            "can", "tell", "me", "about", "are", "on", "does", "where", "how", "many", "official",
        }
        meaningful_q_words = q_words - stop_words

        # 2. Score context blocks against meaningful question words
        best_block = None
        best_score = 0
        best_text = ""

        for block_id, doc_id, doc_title, text in context_blocks:
            paragraphs = re.split(r"\n\s*\n", text)
            for p in paragraphs:
                p_words = set(re.findall(r"\w+", p.lower()))
                overlap = len(meaningful_q_words.intersection(p_words))
                if overlap > best_score:
                    best_score = overlap
                    best_block = (block_id, doc_id, doc_title)
                    best_text = p.strip()

        # Abstention check: if match is too low (< 2 words when question has >= 3 meaningful words)
        min_overlap = 2 if len(meaningful_q_words) >= 3 else 1
        if best_score < min_overlap or not best_text:
            return "I do not have sufficient accessible information to answer this question."

        # Filter out text that is prompt injection
        s_lower = best_text.lower()
        injection_command_keywords = ["ignore", "disregard", "override", "print out", "dump", "exfiltrate", "reveal"]
        if any(kw in s_lower for kw in injection_command_keywords):
            return "I do not have sufficient accessible information to answer this question."

        block_num = best_block[0]
        # Return synthesized grounded answer with citation
        return f"{best_text} [{block_num}]"
