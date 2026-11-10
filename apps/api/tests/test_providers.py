import pytest

from research_assistant.config import Settings
from research_assistant.errors import ProviderConfigError
from research_assistant.llm.anthropic_provider import AnthropicProvider
from research_assistant.llm.factory import build_llm
from research_assistant.llm.mock import MockLLM
from research_assistant.llm.openai_provider import OpenAIProvider
from research_assistant.search.factory import build_search
from research_assistant.search.mock import MockSearch


def test_default_factories_return_mocks() -> None:
    settings = Settings(llm_provider="mock", search_provider="mock")
    assert isinstance(build_llm(settings), MockLLM)
    assert isinstance(build_search(settings), MockSearch)


def test_openai_and_anthropic_require_keys() -> None:
    with pytest.raises(ProviderConfigError):
        build_llm(Settings(llm_provider="openai", openai_api_key=""))
    with pytest.raises(ProviderConfigError):
        build_llm(Settings(llm_provider="anthropic", anthropic_api_key=""))
    with pytest.raises(ProviderConfigError):
        build_search(Settings(search_provider="tavily", tavily_api_key=""))
    with pytest.raises(ProviderConfigError):
        build_llm(Settings(llm_provider="unknown"))


def test_openai_provider_sends_system_and_user_messages() -> None:
    captured = {}

    class Completions:
        def create(self, **kwargs):
            captured.update(kwargs)

            class Response:
                choices = [type("Choice", (), {"message": type("Msg", (), {"content": "ok"})()})()]

            return Response()

    class Client:
        def __init__(self):
            self.chat = type("Chat", (), {"completions": Completions()})()

    provider = OpenAIProvider(api_key="test", model="gpt-4o", client=Client())
    assert provider.complete(system="sys", user="user") == "ok"
    assert captured["model"] == "gpt-4o"
    assert captured["messages"][0] == {"role": "system", "content": "sys"}
    assert captured["messages"][1] == {"role": "user", "content": "user"}


def test_anthropic_provider_collects_text_blocks() -> None:
    captured = {}

    class Messages:
        def create(self, **kwargs):
            captured.update(kwargs)

            class Response:
                content = [
                    type("Block", (), {"type": "text", "text": "Hello "})(),
                    type("Block", (), {"type": "text", "text": "there"})(),
                ]

            return Response()

    class Client:
        def __init__(self):
            self.messages = Messages()

    provider = AnthropicProvider(api_key="test", model="claude-sonnet-5-5", client=Client())
    assert provider.complete(system="sys", user="user") == "Hello there"
    assert captured["model"] == "claude-sonnet-5-5"
    assert captured["system"] == "sys"
    assert captured["messages"] == [{"role": "user", "content": "user"}]
