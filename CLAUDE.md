# HermitClaw

A minimal, self-contained AI agent that lives in a single folder. Like a tamagotchi or pet hermit crab — it thinks continuously, explores files you give it, does web research, and builds up knowledge over time.

**Upstream:** [brendanhogan/hermitclaw](https://github.com/brendanhogan/hermitclaw)
**This fork:** [andrewting19/hermitclaw](https://github.com/andrewting19/hermitclaw) (public)

## Project Structure

- `hermitclaw/` — Python backend (FastAPI + thinking loop)
- `frontend/` — React (Vite + TypeScript) web UI

### Provider Architecture

The LLM provider is configurable. Set `HERMITCLAW_PROVIDER=openai` (default) or `HERMITCLAW_PROVIDER=claude`.

| File | Purpose |
|------|---------|
| `providers.py` | Router — imports from the active provider |
| `providers_openai.py` | OpenAI Responses API (chat, chat_short, embed) |
| `providers_claude.py` | Claude Agent SDK (chat_short, embed stub, OAuth refresh) |
| `brain.py` | `_think_once()` dispatches to `_think_once_openai()` or `_think_once_claude()` |

With Claude, the SDK manages the tool loop internally via MCP. With OpenAI, brain.py manages the tool loop explicitly.

## Running

```bash
# Backend (OpenAI)
pip install -e .
OPENAI_API_KEY=sk-... python hermitclaw/main.py

# Backend (Claude — requires Max subscription OAuth in ~/.claude/.credentials.json)
pip install -e ".[claude]"
HERMITCLAW_PROVIDER=claude python hermitclaw/main.py

# Frontend (dev)
cd frontend && npm install && npm run dev
```

## Design Principles

- **Radically simple code.** Someone who barely codes should be able to follow every file.
- **Single folder world.** The crab can only touch files inside its `{name}_box/`.
- **Continuous thinking.** The crab thinks on a steady pulse, not just in response to input.
- **Organic memory.** Dreams consolidate thoughts into lasting memories that shape personality over time.

## Code Style

- Python: simple, readable, minimal dependencies. No over-engineering.
- TypeScript: functional React components, hooks for state.
- Keep files short and focused. Each file does one thing.

## Gotchas

- Claude SDK `query()` with MCP tools requires an **async iterable prompt**, not a string. String prompts close stdin before tool calls can be handled.
- Always set `permission_mode="bypassPermissions"` when using MCP tools via the SDK, otherwise it hangs waiting for interactive permission approval.
- Claude has no embeddings API — memory retrieval degrades to recency + importance only (no cosine similarity).
- Clean up SDK session transcripts after every `query()` call or `~/.claude/projects/` fills up fast.
