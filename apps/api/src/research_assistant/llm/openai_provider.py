from research_assistant.errors import ResearchError


class OpenAIProvider:
    """Chat completions against an OpenAI model. Default model is GPT-4o."""

    name = "openai"

    def __init__(self, *, api_key: str, model: str, client=None) -> None:
        if client is None:
            from openai import OpenAI

            client = OpenAI(api_key=api_key)
        self.client = client
        self.model = model

    def complete(self, *, system: str, user: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
        except Exception as exc:
            raise ResearchError(f"OpenAI request failed: {exc.__class__.__name__}") from exc
        content = response.choices[0].message.content
        return content or ""
