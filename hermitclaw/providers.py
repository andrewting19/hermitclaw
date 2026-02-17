"""Provider router — picks OpenAI or Claude based on config."""

from hermitclaw.config import config

if config.get("provider") == "claude":
    from hermitclaw.providers_claude import chat_short, embed  # noqa: F401
    chat = None  # not used with Claude — SDK manages tool loop in brain.py
else:
    from hermitclaw.providers_openai import chat, chat_short, embed  # noqa: F401
