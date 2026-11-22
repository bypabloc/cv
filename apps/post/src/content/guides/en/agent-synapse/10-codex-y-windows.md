**10**

# Codex and Windows: what cost hours

[← Index](README.md)

---

### Codex's ask

Codex has no confirmation dialog from a hook: it can only allow or deny. Synapse handles it like this:

1. An `ask` is emitted as a `deny` with a single-use id.
2. **You** approve that run in your terminal (the agent can't):

```bash
python3 <plugin>/scripts/synapse.py approve <id>
```

3. The agent retries the command and this time it passes. The approval expires and isn't reused.

A dedicated rule (`self_approval`) blocks any attempt by the agent to run that `approve` itself.

### The incident: 4 h 27 min and a Markdown file

In a Codex session on Windows, after 4 h 27 min of autonomous work, a documentation `apply_patch` included a Markdown rules file from the `.agents/rules/` folder. Synapse treated it as agent configuration and answered `deny`, asking for approval. The agent stopped working, asked me for the `approve`, and two tasks were left undone until I came back. On top of that, the reason showed up with garbled characters (`Synapse � protect_files … Configuraci�n`).

| Cause | Fix (1.7.1) |
| :-- | :-- |
| The whole rules folder was treated as host governance, though the `.md` files are instructions like `AGENTS.md` | A `.md` in that folder passes; the rest stays `ask` |
| The `deny` text said "tell the user and wait for their answer", and the agent obeyed | The text asks it to apply separately what doesn't depend on the file, keep working and ask for approval at the end of the turn |
| Output used the console encoding (cp1252) and Codex reads UTF-8 | stdin, stdout and stderr in explicit UTF-8 |

**The lesson:** in Claude Code, an `ask` costs a click. In Codex it stops the agent until you're back, even if it's been working alone for hours. Every `ask` in Codex has to justify that cost, and the `deny` must tell the agent how to keep going without getting around the rule.

### A --help that stopped the agent

The agent wanted to see another CLI's help (`codex exec --help`). The `agent_wrapper` rule, which asks for confirmation when launching another agent non-interactively, treated it as a launched agent and it was left waiting. Since 1.7.2, `--help`, `-h`, `--version` and `-V` don't count: the CLI prints and exits without running anything. `codex exec 'prompt'` stays `ask`, and with `--dangerously-*`, `--yolo` or `--full-auto`, `block`.

### Windows: the Store's python3

In Claude Code on Windows, every tool showed `PreToolUse:Edit hook failed` with a "Python was not found; run without arguments to install from the Microsoft Store" message. `python3` resolved to the Store shortcut even though a real Python was installed. And a failing hook **doesn't block**: Synapse wasn't checking anything.

The fix (1.7.2): every hook goes through a launcher (`run-hook.cmd`) that finds a real Python, keeps the exit 2 Claude Code blocks with and, if it finds no Python, answers `ask` instead of nothing. On Linux and macOS the launcher `exec`s the same `python3`, so the output doesn't change.

### In my case

Both Windows failures had something in common: the agent kept going, so nothing looked broken. Since then the monorepo's monitoring treats a `hook failed` as a finding even if the session continues, and checks that every declared hook script exists (a hook pointing to a deleted clone fails silently on every tool).

`codex` `windows` `approvals` `incidents`
