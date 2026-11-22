**01**

# Why an agent needs guardrails

[← Index](README.md)

---

### What can go wrong

A coding agent runs commands and writes files at high speed. In an autonomous run lasting several hours, one reasoning mistake is enough for something hard to undo:

| Risk | Example |
| :-- | :-- |
| Irreparable deletion | `rm -rf` on an empty variable or a path outside the project |
| Rewritten history | `git push --force`, `git reset --hard`, `filter-branch` |
| Leaked secrets | `cat .env` dumps credentials into the context and the transcript |
| Credentials in the repo | A token pasted into a config file or a test |
| Damaged infrastructure | Hand-editing `.git/`, `.venv/` or a lockfile |
| Changes to its own rules | The agent edits its permission or hook configuration |
| Getting around the checks | Writing files with `echo >` or `sed -i` instead of the edit tool |

### Why native permissions aren't enough

Every agent has its own permission system, and in practice it makes you choose between two extremes:

- **Ask about everything:** the agent stops constantly for harmless operations. You end up approving without reading (confirmation fatigue cancels the control) or watching the screen so the work keeps moving.
- **Allow everything:** the agent moves on its own, but nothing tells an `rm` of a temp file apart from an `rm -rf` on your home folder.

Native permissions also look at the command's name, not what it does: `p=/home/x; rm -rf "$p/other"` looks like a relative `rm` until the variable is resolved.

### The idea behind this guide

> **What a rule can decide is left neither to the model nor to the user.**

Synapse checks every tool before it runs. If the operation is clearly safe, it lets it through without asking. If it's clearly dangerous, it blocks it and tells the agent why. Only what's genuinely ambiguous reaches you. The agent spends no context on this: the hooks run outside the conversation.

### What you'll set up

1. The plugin installed on the agent you use ([ch. 02](02-instalacion.md)).
2. A map of what each hook decides ([chs. 03](03-que-decide.md) to [05](05-secretos-y-env.md)).
3. Your project's configuration so routine work doesn't ask ([ch. 06](06-configurar-por-proyecto.md)).
4. Reading the trace to debug ([ch. 07](07-la-traza.md)).
5. Optional: Laya for ambiguous cases ([ch. 08](08-laya.md)).

### In my case

The first hooks were four scripts in one project's `.claude/hooks/` folder. They worked, but every new project meant copying them and every tweak had to be repeated everywhere. Turning them into a plugin, the first version (1.0.0, October 2026) already had today's four hooks; the fourteen versions after it were mostly about removing unnecessary confirmations without opening holes.

`guardrails` `permissions` `problem`
