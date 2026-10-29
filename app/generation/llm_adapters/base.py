from abc import ABC, abstractmethod
from typing import Optional


class BaseLLMAdapter(ABC):
    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generates completion for given prompt and system instructions."""
        pass
