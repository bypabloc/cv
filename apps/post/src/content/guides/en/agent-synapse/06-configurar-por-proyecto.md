**06**

# Per-project configuration

[← Index](README.md)

---

### Routine commands

Subcommands starting with any of these prefixes are treated as routine development: Laya doesn't evaluate them and the decision is `pass`. Block and confirmation rules still apply first.

`.synapse/commands.json` (falling back to `.claude/synapse-commands.json`):

```json
{ "routine_commands": ["bun devtools/run.ts", "graphify"] }
```

Editing this file asks for confirmation: it's security configuration.

Without declaring anything, these already count as routine: `bun|npm|pnpm run|test`, `uv run <tool>`, `python -m pytest`, the project's versioned scripts, `git -C`, `git worktree list|add` and `gh pr|run|issue` (not `merge`).

### Proposing the list from the trace

```bash
python3 <plugin>/scripts/learn_from_log.py --project ~/code/my-app --replay
```

It summarizes the project's decisions, replays them with the current version and suggests prefixes for `routine_commands`. It's how repeated confirmations become rules instead of being approved by hand every time.

### Environment variables

They're set in the `env` of the agent's configuration (in Claude Code, the global or project `settings.json`):

| Variable | What it does | Default |
| :-- | :-- | :-- |
| `SYNAPSE_LAYA` | `on` turns Laya on; `off` turns it off in every hook | Unset: Laya off |
| `SYNAPSE_LAYA_HOOKS` | Hooks where Laya runs, comma-separated | Empty |
| `SYNAPSE_LOG_DIR` | Trace folder | The agent's ([ch. 02](02-instalacion.md)) |
| `SYNAPSE_LOG_RETENTION_DAYS` | Days traces are kept (`0` = all) | `30` |
| `SYNAPSE_DEBUG` | Diagnostic messages on stderr | `0` |
| `SYNAPSE_PYTHON` | Interpreter to use | Whatever the launcher finds |
| `SYNAPSE_LAYA_IDLE_SECONDS` | Idle time after which the Laya daemon frees VRAM | `1200` |
| `SYNAPSE_LAYA_STARTUP_SECONDS` | Max wait for the daemon to start | `40` |

### Native layers worth adding

Synapse is one more layer, not the only one. Each agent has its own controls that combine well:

| Agent | Recommended native layer |
| :-- | :-- |
| Codex | `workspace-write` sandbox and `"**/*.env" = "deny"` in the permission profile |
| Antigravity | Sandbox on and `permissions.deny` for `read_file(**/.env)` |
| OpenCode | `permission.read["*.env"] = "deny"` and `external_directory = "ask"` |

### In my case

The routine rules that ship by default came about like this: in one project's month-long trace, the only `ask`s left were harmless commands (`bun run typecheck`, `git worktree list`, `pdfinfo`, a `timeout N tail -f /dev/null`). Each one became a rule or a routine prefix, with a case pinning it down, and that project's confirmations nearly disappeared without touching a single block rule.

`configuration` `variables` `routine`
