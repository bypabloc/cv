**11**

# Testing, updating and monitoring

[← Index](README.md)

---

### The tests

```bash
claude plugin validate --strict .   # manifest
python3 -m pytest                   # everything, deterministic rules only (~40 s)
python3 -m pytest --laya gpu        # with Laya on CUDA (--laya cpu for CPU)
python3 -m pytest tests/e2e         # only the full pipeline from hooks.json
```

| Folder | What it holds |
| :-- | :-- |
| `tests/cases/<hook>.json` | Declarative cases: payload → expected decision, exit and stderr |
| `tests/unit/` | One module per hook and per shared rule |
| `tests/golden/` | Claude Code's exact output, which no change may alter |
| `tests/fixtures/<host>/` | Real payloads from each agent, by OS and version |
| `tests/e2e/` | The real hooks, and each agent's CLI when installed |

### Adding a case

Just add an entry to the hook's JSON. Every false positive is pinned with two cases: the one that failed and a similar one that must keep its decision. For example, `pass_agent_wrapper_help_runs_no_agent` (`codex exec --help` passes) next to a `codex exec 'prompt'` that stays `ask`. A new case must fail before the change.

### Updating after a release

| Agent | How |
| :-- | :-- |
| Claude Code | `claude plugin marketplace update bypabloc-agents && claude plugin update synapse@bypabloc-agents`; `/reload-plugins` in open sessions |
| Codex | `codex plugin marketplace upgrade` then `/hooks` to trust again; restart open sessions |
| Antigravity | Repeat `agy plugin install https://github.com/bypabloc/agent-plugin-synapse` |
| OpenCode | With a pinned version (`#vX.Y.Z`), change the reference; with `#main`, it updates on start |

### Monitoring real sessions

A guardrail nobody looks at degrades silently. The routine I use:

1. Review the last few days' trace: new `ask`s and `block`s, and their `decided_by`.
2. Look for failed hooks in the agent's logs, even if the session kept going.
3. Confirm the installed version on each agent and profile.
4. Every finding is repaired with a case that reproduces it, a new version and a log entry: symptom, cause, change, test and lesson.

### In my case

The monorepo has a monitoring collector that walks the Windows and WSL traces read-only, and a fixed repair flow: worktree, failing case, fix, PR to `dev` and `main`, version tag and updating every installation. The rule is that a repair isn't done until it's published and installed on every agent; otherwise the next session trips over the same failure.

`tests` `release` `monitoring`
