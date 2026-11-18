**06**

# Know when the cache expired

[← Index](README.md)

---

### The common rule

No agent shows on screen that the prompt cache expired (except Claude Code's statusline). The signal comes from **each call's token usage**:

> **Cache miss** = the part read from cache drops to ~0 (or to a fixed floor, like the system instructions) and almost the whole prompt is written or billed again.
>
> - **After a pause longer than the TTL:** the cache expired.
> - **Without a pause:** something changed the prefix (model, tools or MCP, system prompt, compaction, effort).

### Per agent

| | Claude Code | Codex | OpenCode | Antigravity |
| :-- | :-- | :-- | :-- | :-- |
| Cache | Anthropic, `cache_control` | OpenAI, automatic by prefix | The provider's (Anthropic in these tests) | Implicit Gemini |
| TTL | **1 h** in the main conversation with a subscription; 5 min with an API key, credits or subagents **[doc]** | No fixed TTL: `in_memory` of 5–10 min (up to 1 h) or `24h`, depending on model and ZDR **[doc]** | 5 min with Anthropic; 1 h if a plugin asks for it | Probabilistic, no published TTL **[doc]** |
| Where to see it | Statusline (`prompt_cache`), `/usage`, transcript JSONL, OTel | `codex exec --json` (`turn.completed.usage`), rollouts in `~/.codex/sessions/` | `message` table of `~/.local/share/opencode/opencode.db`, `opencode export` | `agy -p --output-format json`, `stream-json`, transcript |
| Fields | `cache_read_input_tokens`, `cache_creation_input_tokens` (`ephemeral_5m`, `ephemeral_1h`) | `input_tokens` (**includes** the cached part) and `cached_input_tokens` | `tokens.cache.read`, `tokens.cache.write` | JSON: `input_tokens` **includes** `cache_read_tokens`; transcript: only the uncached part |
| Hit ratio | `read / (read + creation + input)` | `cached / input` | `read / (input + read + write)` | JSON `cache_read / input`; transcript `cache_read / (input + cache_read)` |
| Warning without querying | **Yes:** the statusline runs again when `expires_at` arrives (`warm`, `last_miss_cause`, `recache_tokens_if_cold`) | No | No | No |

### What invalidates the cache without a pause

- **All of them:** switching model, tools or MCP, system prompt, effort or reasoning; compacting.
- **Claude Code** **[doc]**: `/model`, effort, fast mode, connecting or removing an MCP without tool search, `/compact` and an update invalidate it. Editing files, editing CLAUDE.md, changing permissions, `/rewind` and subagents do **not**.
- **OpenAI** **[doc]**: more than 15 requests per minute may land on another machine without the cache.

### How to watch it

1. **Claude Code:** a statusline with `prompt_cache.warm`, `expires_at` and `last_miss_cause`; for a one-off check, `/usage`.
2. **Codex:** `codex exec --json` and `cached_input_tokens / input_tokens` per turn; interactively, the rollouts.
3. **OpenCode:** the `message` table (read-only) or third-party tools.
4. **Antigravity:** `stream-json` and each step's `cache_read_tokens`.

Don't send "pings" to keep the cache alive: they cost tokens. In Claude Code, the official option is `promptCacheTtl: "1h"` (or `CLAUDE_CODE_PROMPT_CACHE_TTL=1h`).

### The handoff's effect on the cache

- **Claude Code and Codex:** the handoff is only injected on startup, resume, compact, `/clear` or fork: it doesn't affect the cache between turns. **[doc]**
- **OpenCode:** it goes in `system` on every call. As long as `PROGRESS.md` doesn't change, the prefix is identical; **editing it rewrites the whole cache** on the next call. Reasonable if it is edited rarely. **[judgment]**
- **Antigravity:** the `ephemeralMessage` doesn't accumulate; later turns read from cache normally. **[measured]**

### In my case

I measured the local logs of the four agents in real sessions. These numbers set the thresholds in [chapter 07](07-pausa-larga.md):

| Agent | What I measured |
| :-- | :-- |
| Claude Code | Pauses of 5 to 18 min: it kept reading from cache (205K–499K) and rewrote almost nothing. A 590 min pause read 28K and rewrote ~130K: the 1 h TTL had expired |
| Codex | Pauses of 42 to 54 min: sometimes 0.98–1.00 hits, other times a floor of ~11K (shared instructions) or 0. From 66 min on, it always misses |
| Antigravity | <1 min 99 %, 1–3 min 95 %, 3–5 min 88 %, 5–7 min 68 %, 7–10 min 11 %, 15–30 min 9 %, >30 min 0 %. A new conversation's first call does not read cache |
| OpenCode | With the 5 min default: 100 % with pauses < 5 min and 0 % with > 30 (2145 messages). With 1 h requested by the plugin: after 6 min 40 s it read 59 505 and wrote 20; 2 of 7 pauses rewrote with no cause found |

Some blogs claim Claude Code's TTL dropped to 5 min. The documentation and my measurements show 1 h with a subscription.

Sources: [Claude Code prompt caching](https://code.claude.com/docs/en/prompt-caching.md), [statusline](https://code.claude.com/docs/en/statusline.md), [Anthropic prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching), [OpenAI prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching), [Antigravity headless](https://antigravity.google/docs/cli/headless), [Gemini caching](https://aistudio.google.com/docs/caching).

`prompt-caching` `ttl` `tokens` `costs`
