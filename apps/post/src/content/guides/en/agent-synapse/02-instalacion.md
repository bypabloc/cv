**02**

# Installing on each agent

[← Index](README.md)

---

### Requirements

- **Python 3.10 or later.** On Linux and macOS, `python3`; on Windows, `py -3` or `python`. To pin another interpreter, the `SYNAPSE_PYTHON` variable.
- **git** on the `PATH` (project scope is computed from git; without a repo, the root is the current folder).
- The minimum agent versions in the table below.

No GPU or extra dependencies are needed: without Laya, Synapse runs on Python's standard library alone.

### Claude Code

```bash
claude plugin marketplace add bypabloc/agent-plugins
claude plugin install synapse@bypabloc-agents
claude plugin list                       # check
```

For a single project, `--scope project`. To try it without installing, clone the repo and use `claude --plugin-dir ./agent-plugin-synapse`.

### Codex, Antigravity and OpenCode

| Agent | Installation | How it decides |
| :-- | :-- | :-- |
| **Codex** ≥ 0.171 | `codex plugin marketplace add bypabloc/agent-plugins` · `codex plugin add synapse@bypabloc-agents` · then `/hooks` to trust the hooks | Blocks with `deny`. Codex can't ask from a hook: an `ask` is answered as a `deny` with an id, and you approve a single run in your terminal ([ch. 10](10-codex-y-windows.md)) |
| **Antigravity** (`agy` ≥ 1.5.4) | `agy plugin install https://github.com/bypabloc/agent-plugin-synapse` | Native `deny` and `force_ask`. An internal error asks for confirmation, because in Antigravity an error equals allowing |
| **OpenCode** V2 ≥ 2.3 | In `opencode.json`: `"plugins": ["@bypabloc/synapse@git+https://github.com/bypabloc/agent-plugin-synapse.git"]` (option `{"python": "…"}` to pin the interpreter) | `throw` to block and `permission.assert` to ask. If Synapse doesn't answer, it asks |

Codex ties hook trust to the scripts' hash: after every plugin update you have to approve them again in `/hooks`.

### Checking that it works

```bash
python3 <plugin>/scripts/synapse.py doctor
```

It checks the interpreter, the manifests, each CLI's version, the Laya delta and the logs. For an end-to-end test, ask the agent for something that must be blocked, for example deleting a folder outside the project: it should answer with a `🚫 BLOCKED · Synapse · block_dangerous` message and the rule that decided.

In Claude Code, the `synapse-status` skill summarizes the mode (deterministic rules or Laya on GPU/CPU) and recent decisions.

### Where the traces go

| Agent | Folder |
| :-- | :-- |
| Claude Code | `${CLAUDE_CONFIG_DIR:-~/.claude}/logs/synapse/` |
| Codex, Antigravity, OpenCode | `~/.local/state/synapse/logs/` (on Windows, `%LOCALAPPDATA%\synapse\logs`) |

### Platform limits

- **Native Windows:** it protects paths and writes (including Codex's `Set-Content`), but PowerShell command analysis is partial.
- **Laya** doesn't run on native Windows: it needs Unix sockets. On WSL it does.
- **Codex** has no read tool: the `.env` block applies to shell commands.

### In my case

I use all four agents on the same machine, on WSL and Windows. The monorepo has a script that, after every release, updates every installation (each CLI, each profile and each project scope) and keeps Codex's previous cache for sessions still open, because those sessions keep the version they started with. In Codex, also, updating without re-approving in `/hooks` doesn't count as updated.

`installation` `claude-code` `codex` `antigravity` `opencode`
