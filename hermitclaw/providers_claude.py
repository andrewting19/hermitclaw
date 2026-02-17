"""LLM calls via Claude Agent SDK (for Claude Max OAuth)."""

import glob
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path

from hermitclaw.config import config

logger = logging.getLogger("hermitclaw.providers_claude")

# OAuth constants (same as session-summarizer)
OAUTH_TOKEN_URL = "https://console.anthropic.com/v1/oauth/token"
OAUTH_CLIENT_ID = "9d1c250a-e61b-44d9-88ed-5944d1962f5e"


def refresh_oauth_token() -> str | None:
    """Refresh OAuth token if expired or about to expire. Returns fresh access token."""
    import urllib.request
    import urllib.error

    creds_path = Path.home() / ".claude" / ".credentials.json"
    if not creds_path.exists():
        return None

    creds = json.loads(creds_path.read_text())
    oauth = creds.get("claudeAiOauth", {})

    access_token = oauth.get("accessToken")
    refresh_token = oauth.get("refreshToken")
    expires_at = oauth.get("expiresAt", 0)

    if not refresh_token:
        return access_token

    # Check if token expires within 5 minutes (300000 ms)
    now_ms = int(time.time() * 1000)
    if expires_at > now_ms + 300000:
        return access_token

    # Token expired or expiring soon — refresh it
    try:
        req_data = json.dumps({
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": OAUTH_CLIENT_ID
        }).encode()

        req = urllib.request.Request(
            OAUTH_TOKEN_URL,
            data=req_data,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "hermitclaw/1.0"
            },
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())

        new_access = result["access_token"]
        new_refresh = result.get("refresh_token", refresh_token)
        expires_in = result.get("expires_in", 28800)
        new_expiry = int((time.time() + expires_in) * 1000)

        creds["claudeAiOauth"]["accessToken"] = new_access
        creds["claudeAiOauth"]["refreshToken"] = new_refresh
        creds["claudeAiOauth"]["expiresAt"] = new_expiry

        creds_path.write_text(json.dumps(creds))
        logger.info(f"Refreshed OAuth token, expires in {expires_in}s")

        return new_access

    except (urllib.error.URLError, json.JSONDecodeError, KeyError) as e:
        logger.error(f"Failed to refresh token: {e}")
        return access_token


def cleanup_transcript(session_id: str):
    """Delete SDK session transcript to prevent disk bloat."""
    if not session_id:
        return
    pattern = str(Path.home() / ".claude" / "projects" / "*" / f"{session_id}.jsonl")
    for match in glob.glob(pattern):
        try:
            Path(match).unlink(missing_ok=True)
            logger.debug(f"Cleaned up transcript: {match}")
        except Exception as e:
            logger.warning(f"Failed to clean transcript {match}: {e}")


def chat_short(input_list: list, instructions: str = None) -> str:
    """Short LLM call (importance scoring, reflections) — returns text, no tools.

    Uses asyncio.run() internally. Safe because this is always called from
    threads via asyncio.to_thread().
    """
    import asyncio
    from claude_agent_sdk import query, ClaudeAgentOptions

    # Refresh OAuth token before each call
    access_token = refresh_oauth_token()
    if access_token:
        os.environ["CLAUDE_CODE_OAUTH_TOKEN"] = access_token

    # Build prompt from input_list
    parts = []
    if instructions:
        parts.append(instructions)
    for item in input_list:
        if isinstance(item, dict):
            content = item.get("content", "")
            if isinstance(content, str):
                parts.append(content)
            elif isinstance(content, list):
                for c in content:
                    if isinstance(c, dict) and c.get("type") == "input_text":
                        parts.append(c["text"])
    prompt = "\n\n".join(parts)

    text_parts = []
    sdk_session_id = None

    async def _run():
        nonlocal sdk_session_id
        async for msg in query(
            prompt=prompt,
            options=ClaudeAgentOptions(
                allowed_tools=[],
                max_turns=1,
                model=config.get("claude_model", "claude-opus-4-5-20251101"),
            )
        ):
            if hasattr(msg, "content"):
                for block in msg.content:
                    if hasattr(block, "text") and block.text:
                        text_parts.append(block.text)
            if hasattr(msg, "session_id"):
                sdk_session_id = msg.session_id

    asyncio.run(_run())
    cleanup_transcript(sdk_session_id)
    return "".join(text_parts)


def embed(text: str) -> list[float]:
    """Return empty embedding — Claude has no embeddings API.

    Memory.py handles this gracefully: empty embeddings → relevance score = 0
    → retrieval falls back to recency + importance.
    """
    return []
