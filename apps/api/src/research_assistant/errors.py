class ResearchError(Exception):
    """A research run failed in a way the API should report."""


class ProviderConfigError(ResearchError):
    """LLM or search provider settings are missing or unknown."""
