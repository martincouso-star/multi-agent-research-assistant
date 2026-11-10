from typing import Protocol


class LLMProvider(Protocol):
    name: str

    def complete(self, *, system: str, user: str) -> str:
        """Return the model's text response."""
