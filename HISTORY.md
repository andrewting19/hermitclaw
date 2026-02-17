# HermitClaw Fork History

**Upstream:** [brendanhogan/hermitclaw](https://github.com/brendanhogan/hermitclaw)
**Fork:** [andrewting19/hermitclaw](https://github.com/andrewting19/hermitclaw) (public)

## Claude Agent SDK Provider

Added Claude as an alternative LLM provider alongside OpenAI. Switch via `HERMITCLAW_PROVIDER=claude` env var or `provider: "claude"` in config.yaml. Uses Claude Max subscription OAuth tokens through the Agent SDK.

**Files changed:**

| File | Change |
|------|--------|
| `config.yaml` | Added `provider` and `claude_model` settings |
| `hermitclaw/config.py` | Added `HERMITCLAW_PROVIDER` env var override |
| `hermitclaw/providers.py` | New router — imports from OpenAI or Claude provider |
| `hermitclaw/providers_openai.py` | Renamed from `providers.py` (no content changes) |
| `hermitclaw/providers_claude.py` | New — `chat_short()`, `embed()`, OAuth refresh, transcript cleanup |
| `hermitclaw/brain.py` | Added `_think_once_claude()`, `_setup_claude_tools()`, provider dispatch, fixed `_reflect()`/`_plan()` to use `chat_short()`, fixed `_broadcast()` race condition |
| `pyproject.toml` | Added optional `[claude]` dependency group |

**Key design decisions:**
- SDK `query()` runs in the main event loop so MCP tool handlers can `await` WebSocket broadcasts
- Async iterable prompt (not string) required for MCP SDK servers to keep stdin open for bidirectional communication
- `permission_mode="bypassPermissions"` prevents the SDK from hanging on tool permission prompts
- `embed()` returns `[]` — memory retrieval falls back to recency + importance (no cosine similarity)
- Transcript cleanup after every `query()` call prevents `~/.claude/projects/` disk bloat
- Opus 4.5 used for all calls (thinking, reflection, planning, importance scoring)
