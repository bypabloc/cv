**07**

# Resume after a long pause

[← Index](README.md)

---

### The question

Can you avoid resending the whole conversation after a long pause and continue from the handoff alone?

- **Intercepting once the cache has already expired doesn't work on its own.** No agent has a "cache expired" event, and the first request after the pause already pays for the full rewrite, unless what gets sent is trimmed.
- The savings come from two paths:
  1. **Before it expires:** compact while the cache is warm. Claude Code does this natively.
  2. **On return:** don't send the history. A new session where the startup hook injects the handoff (Codex and Antigravity), or trim what gets sent within the same session (OpenCode).
- Condition for both: the handoff must be on disk **at the end of every turn**, not only when you come back.
- Only in sessions **with a linked task**: without a handoff, a new session has nothing to continue from.

### What each agent does

| | Claude Code | Codex | OpenCode | Antigravity |
| :-- | :-- | :-- | :-- | :-- |
| Mechanism | Native: `idleCompaction` at ~90 % of the TTL | `Stop` records the time; `UserPromptSubmit` blocks once | Plugin: a cut at the message that opens the turn | `PostInvocation` records; `PreInvocation` (`invocationNum` 0) ends the turn |
| Threshold | ~54 min (with ≥ 200k tokens) | 30 min | 55 min with a 1 h cache (5 min if the cache is 5) | 10 min |
| What you see | "Compacted while idle…" | `hook: UserPromptSubmit Blocked` and the notice | Nothing: it continues in the same session | An error with the notice; exit 3 in `-p` |
| How you continue | As always | New session (not `resume`) + "resume task X", or resend | As always | New conversation + "resume task X", or resend |
| What it keeps | The summary (or the tail) and the handoff | Only the handoff and the repo | The handoff and what comes after the cut | Only the handoff |
| Evidence | **[bin]** and real compactions | **[test]** `codex exec` | **[test]** 3 turns and measured tokens | **[test]** transcript without a model call |

### Claude Code: already solved

`idleCompaction` schedules a timer at `lastActivityAt + 0.9 × (expiresAt − lastActivityAt)`: about 54 min with a 1 h TTL. It compacts **reading from cache**, the best possible outcome. **[bin]**

- Conditions: interactive session, 1 h TTL, unchanged prefix and at least `max(100k, CLAUDE_CODE_IDLE_COMPACT_MIN_TOKENS)` tokens (200 000 by default).
- Turned off with `"idleCompaction": false`.
- After each one, `SessionStart` `compact` re-injects the handoff. **[test]**

### Codex: block once and ask for a new session

No Codex hook can trim what gets sent: `UserPromptSubmit` can only add context or block. **[doc]**

1. `Stop` (with `--touch`) records the time in `tmp/handoff/.idle/<session_id>` and prints `{}`.
2. On the next message, if more than 30 min passed, `UserPromptSubmit` returns `{"decision":"block","reason":"…"}` with the minutes, the task and its folder.
3. You open a new session and type "resume task `042-login-form`". **Don't use `resume`**: it loads the whole conversation.
4. The block happens once: if you resend the message, it continues in the same session, in case the full context is worth more than the savings.

### Antigravity: end the turn before calling the model

- `PostInvocation` records the time; `PreInvocation` evaluates **only with `invocationNum` 0** (the turn's first call).
- After 10 min, it returns `terminationBehavior: "terminate"` with an `errorMessage`: it stops **before** calling the model. **[doc + test]**
- Pitfalls: with `terminate`, `agy -p` exits 3, and the JSON's `usage` is **cumulative** even though the model was not called.

### OpenCode: trim within the same session

- The `context` hook receives `messages` and can replace them: removing old ones only changes what gets sent, not the stored history. **[test]**
- After the pause, the plugin sets a cut at the user message that opens the turn and sends only what follows, with the handoff in `system`. It cuts at a turn boundary so it doesn't break `tool_use`/`tool_result` pairs.
- The cut is saved: later calls send the same prefix, which gets cached again.
- A long command does **not** trigger the cut: within a turn, the next call is opened by a tool result, not by the user.

### Asking for a 1 h cache in OpenCode

With the Anthropic API, OpenCode uses a 5 min cache and doesn't let you configure it: a command longer than 5 min made the next call rewrite the whole prefix (×1.25) instead of reading it (×0.1).

- The plugin handles `http.request`, rewrites every request to the provider and sets `ttl: "1h"` on **every** `cache_control` (Anthropic requires 1 h marks to precede 5 min ones).
- A 1 h write costs ×2. With that, the pause cut goes from 5 to 55 min.
- If the body is not JSON, the request goes through unchanged. Check `cache_creation.ephemeral_1h_input_tokens` in the `message_start`.

### The thresholds

- They come from each agent's measured TTL ([ch. 06](06-cache-de-prompt.md)).
- One environment variable changes them all and `0` turns them off. In OpenCode the background service reads it.
- Per-session state in `tmp/handoff/.idle/<session_id>` (`last` and, in OpenCode, `cut`). Writing `{"last": 0}` simulates a pause ([ch. 10](10-probar-el-handoff.md)).

### In my case

| Case | Without this | With this | Basis |
| :-- | :-- | :-- | :-- |
| OpenCode after the pause | The next message rewrites the whole history | Only the uncached part: 145 and 164 tokens after the cut | **[measured]** |
| Codex, 150k of context | ~USD 0.75 cold per message | New session with an 8k handoff: ~USD 0.04 | **[calculation]** |
| Antigravity | The whole history with ~11 % hits after 7 min | The new conversation starts from the handoff | **[measured]** hits |
| Claude Code, 200k, 1 h TTL | ~400k rewrite units (write ×2) | ~40k: it compacts before expiry | **[calculation]** |

I first looked at what the community had: auto-handoff plugins and 55-minute compaction plugins for Claude Code (which overlap with the native feature), manual handoff kits for Codex and a manual `/handoff` for OpenCode. None of them detected the pause and continued from an on-disk handoff automatically in Codex, OpenCode or Antigravity.

`prompt-caching` `idle` `costs` `handoff`
