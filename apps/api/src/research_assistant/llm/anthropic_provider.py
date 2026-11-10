from research_assistant.errors import ResearchError


class AnthropicProvider:
    """Messages API against an Anthropic Claude model."""

    name = "anthropic"

    def __init__(self, *, api_key: str, model: str, client=None) -> None:
        if client is None:
            import anthropic

            client = anthropic.Anthropic(api_key=api_key)
        self.client = client
        self.model = model

    def complete(self, *, system: str, user: str) -> str:
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
        except Exception as exc:
            raise ResearchError(f"Anthropic request failed: {exc.__class__.__name__}") from exc
        parts: list[str] = []
        for block in response.content:
            text = getattr(block, "text", None)
            if text:
                parts.append(text)
        return "".join(parts)
