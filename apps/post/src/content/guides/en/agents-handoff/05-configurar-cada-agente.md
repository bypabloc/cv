**05**

# Configure each agent

[← Index](README.md)

---

### Summary

| | Claude Code | Codex | OpenCode | Antigravity |
| :-- | :-- | :-- | :-- | :-- |
| Event to re-inject | `SessionStart` `compact` | `SessionStart` `compact` | `context` (every call) | `PreInvocation` (every call) |
| Where the hook lives | Project | **User**, with a per-repo guard | Project (plugin) | Project (`.agents/hooks.json`) |
| Input | snake_case | snake_case | Built by the plugin | camelCase |
| Output | `additionalContext` | `additionalContext` (must not start with `[`) | `system.push` | `injectSteps[].ephemeralMessage` |
| Resent on following turns | Yes | Yes | **No** | **No** |
| Visible errors | Hook stderr | `Failed` in `codex exec` | `debug config` | Only in its log |

### 1. Claude Code: `.claude/settings.json`

```json
{
  "env": { "CLAUDE_AUTOCOMPACT_PCT_OVERRIDE": "60" },
  "permissions": { "additionalDirectories": ["../<repo>-worktrees"] },
  "hooks": {
    "SessionStart": [{ "matcher": "startup|resume|clear|compact|fork",
      "hooks": [{ "type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR/agent-hooks/session_handoff.py\"", "timeout": 10 }] }],
    "PreCompact": [{ "matcher": "manual|auto", "hooks": [{ "type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR/agent-hooks/session_handoff.py\"" }] }],
    "Stop": [{ "hooks": [{ "type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR/agent-hooks/session_handoff.py\"" }] }],
    "PreToolUse": [{ "matcher": "^AskUserQuestion$", "hooks": [{ "type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR/agent-hooks/session_handoff.py\"" }] }],
    "PostToolUse": [{ "matcher": "^(Edit|Write)$", "hooks": [{ "type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR/agent-hooks/session_handoff.py\"" }] }]
  }
}
```

| Hook | What for |
| :-- | :-- |
| `SessionStart` | Injects the handoff on startup, resume, after `/clear`, on a fork and **right after compacting** (also when a plugin compacts). **[doc + test]** |
| `PreCompact` | Runs before the summary: **its stdout is instructions for the summary**; exit 2 blocks the compaction. It does not run if a plugin answers the compaction. **[doc + test]** |
| `Stop` | Blocks the end of the turn (`decision: block`) while work is pending. **[real use]** |
| `PreToolUse` of questions | Rejects a question to the user when the agent should decide. **[real use]** |
| `PostToolUse` of `Edit\|Write` | Validates the status lines right after they are written. **[real use]** |

- **Input:** `session_id`, `cwd`, `source`, `transcript_path` and `hook_event_name`.
- `$CLAUDE_PROJECT_DIR` points to the project where the session was opened: the script that runs is **the main checkout's**.
- `PostCompact` exists but doesn't inject context: it is only for side effects.
- The long pause needs nothing: `idleCompaction` is on by default ([ch. 07](07-pausa-larga.md)).
- Recommended: a `Bash` `PreToolUse` that rejects `git worktree add` with a path inside the repo ([ch. 11](11-uso-diario.md)).

### 2. Codex: project and user

`.codex/config.toml` (project, only in trusted paths):

```toml
model_post_turn_compact_threshold_percent = 65
model_auto_compact_token_limit = 190000
project_doc_max_bytes = 65536
```

The hooks do **not** go in the project. Project hooks (`.codex/hooks.json`) only run if the path is trusted **and** they were approved in `/hooks`. Every worktree is a different path: there the hook **does not run and Codex does not warn**, not even with `--dangerously-bypass-hook-trust`. **[test]**

The fix is a **user** hook, `~/.codex/hooks.json`, with three events:

| Event | Matcher | Command | If it does not apply |
| :-- | :-- | :-- | :-- |
| `SessionStart` | `^(startup\|resume\|clear\|compact\|fork)$` | `session_handoff.py` | `\|\| true` |
| `UserPromptSubmit` | — | `session_handoff.py` | `\|\| true` |
| `Stop` | — | `session_handoff.py --touch` | `\|\| echo '{}'` (requires JSON) |

Each command carries a **per-repo guard**, because a user hook runs in any repo Codex opens:

```sh
[ "$(git rev-parse --path-format=absolute --git-common-dir 2>/dev/null)" = '<repo>/.git' ] \
  && r=$(git rev-parse --show-toplevel 2>/dev/null) \
  && [ -f "$r/agent-hooks/session_handoff.py" ] && python3 "$r/agent-hooks/session_handoff.py" || true
```

- Without the guard, a cloned repo that ships an `agent-hooks/session_handoff.py` would run code in every session.
- Worktrees share the common `.git`, so they pass the guard.
- Don't also create `.codex/hooks.json` in the repo: in the main checkout it would add up and inject twice.
- Plain-text output **is** injected; if it starts with `[`, Codex reads it as JSON and marks the hook `Failed`. Emit JSON so you don't depend on that. **[test]**
- Codex stores trust by hash: changing the hook requires approving it again in `/hooks` and restarting the session. **[doc]**
- **Install it with a script**, not with `cp`: one that merges the template into `~/.codex/hooks.json` (replacing only the groups that call the script and backing up the file), prepends the guard with the real `.git` path, and has a `status` mode that exits 1 if an event is missing or differs.

### 3. OpenCode: `opencode.json` and a plugin

```json
{ "compaction": { "buffer": 400000 } }
```

`.opencode/plugins/session-handoff.ts`, the essentials:

```ts
const { text, cut } = handoffFor(request.sessionID, directory, opening) // opening: id of the last message if it is the user's
if (text) request.system.push({ type: "text", text })
if (text) applyCut(request.messages, cut)   // drops what comes before the cut; the stored history doesn't change
// http.request: ttl "1h" on every cache_control of requests to Anthropic (ch. 07)
export default { id: `session-handoff:${PLUGIN_ROOT}`, setup }
```

- Plugins with the V2 API: `export default { id, setup(ctx) }`.
- `ctx.session.hook("context", req => …)` runs **before every model call**. What it adds to `system` **is not saved to the history**: it survives compaction without duplicating. **[test]**
- The `context` name is undocumented, and a hook with a non-existent name doesn't error: repeat the test on every update.
- OpenCode looks for `opencode.json` and `.opencode/` **upwards**: from a worktree inside the repo it also loads the main checkout's. That is why each copy of the plugin acts only if the session's git root is its own, and the `id` carries the checkout path.
- After changing the plugin, `opencode service restart`. To test, `opencode run --standalone`: the background service keeps the old `setup`.

### 4. Antigravity: `.agents/hooks.json`

```json
{ "session-handoff": {
  "PreInvocation":  [{ "type": "command", "command": "python3 <repo>/agent-hooks/session_handoff.py || echo '{}'", "timeout": 10 }],
  "PostInvocation": [{ "type": "command", "command": "python3 <repo>/agent-hooks/session_handoff.py --touch || echo '{}'", "timeout": 10 }]
} }
```

- It is a **map of named hooks**, not the Claude Code format. **[doc + test]** ([CLI hooks](https://antigravity.google/docs/hooks?tab=cli))
- Input in **camelCase**: `conversationId`, `workspacePaths`, `transcriptPath`; `PreInvocation` adds `invocationNum`.
- There is no compaction event: injecting on every `PreInvocation` keeps the handoff always present.
- The `ephemeralMessage` is saved in the transcript (the `/compact` summary uses it), but it is **not resent** on following turns. **[measured]**
- A malformed `hooks.json` doesn't fail the run: the error only shows up in `~/.gemini/antigravity-cli/log/cli-*.log`.
- In headless mode, an action that needs approval is denied, execution continues and it exits 0. **[doc]**

### In my case

The two most expensive mistakes were silent. In Codex, the user hook **had never been installed** on one of my machines: Codex worked without a handoff and nothing said so. That is where the installer with a `status` mode came from. And the first template of that hook called the script at the git root of **any** repo; a test didn't catch it, an automated security review did. The per-repo guard came out of that.

In OpenCode, inside a worktree, no copy of the plugin acted: both had the same `id`, only the first one to load got registered, and that one was discarded by the root check. The real test showed it, not the unit tests. In Antigravity I measured the cost of injecting on every invocation: +1500 tokens on the turn that links and ~210 per turn afterwards, because the message does not accumulate.

`claude-code` `codex` `opencode` `antigravity` `hooks`
