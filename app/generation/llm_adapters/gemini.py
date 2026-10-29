import os
from typing import Optional
from app.generation.llm_adapters.base import BaseLLMAdapter
from app.core.config import settings


class GeminiLLMAdapter(BaseLLMAdapter):
    """Google Gemini API adapter."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY")

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if not self.api_key:
            # Fall back to mock adapter if API key is not configured
            from app.generation.llm_adapters.mock import MockLLMAdapter
            return MockLLMAdapter().generate(prompt, system_prompt)

        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                system_instruction=system_prompt,
            )
            response = model.generate_content(prompt)
            return response.text or "I do not have sufficient accessible information to answer this question."
        except Exception:
            from app.generation.llm_adapters.mock import MockLLMAdapter
            return MockLLMAdapter().generate(prompt, system_prompt)
