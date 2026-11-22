# Guardrails for your coding agent: no deleting, no leaking secrets, no touching what it shouldn't

> A practical guide to installing and running Synapse, a guardrails plugin for Claude Code, Codex, Antigravity and OpenCode: it blocks destructive commands, writes outside the project, `.env` reads and secrets before the agent runs them, without asking you about routine work. With the case study of how it was ported to four agents and the numbers measured over weeks of use.

**Cost:** USD 0 (MIT plugin) · **Time:** ~1 h to install it and read the guide · **Level:** intermediate (hooks, git, Python)

---

## TL;DR

- **The problem:** with native permissions, the agent interrupts you every few minutes or, if you turn them off, it can delete, leak or rewrite something without anyone noticing.
- **The solution:** four hooks that check every tool **before** it runs and decide `allow`, `ask`, `block` or `pass` with deterministic rules (~8 ms per command) ([ch. 03](03-que-decide.md)).
- **What it covers:** destructive commands and commands outside the project, writing files from Bash, `.env` reads, credentials in what gets written, and core files like `.git/` or lockfiles.
- **Four agents, one logic:** Claude Code, Codex, Antigravity and OpenCode share the same core; only each host's input and output change ([ch. 02](02-instalacion.md) and [ch. 09](09-portar-a-cuatro-agentes.md)).
- **Laya:** an optional neural classifier for ambiguous cases. It can only ask for confirmation, never block, and it ships off because the real trace showed its 24 confirmations were all false positives ([ch. 08](08-laya.md)).
- **A trace of every decision:** who decided, with which rule and why, in a daily JSONL ([ch. 07](07-la-traza.md)).
- **Ready-to-install plugin:** [bypabloc/agent-plugin-synapse](https://github.com/bypabloc/agent-plugin-synapse), a mirror of the [bypabloc/agent-plugins](https://github.com/bypabloc/agent-plugins) monorepo.

---

## Where the idea came from

Synapse was born from constant interruptions. With the default permissions, the agent stopped every few minutes to ask for confirmation on an `rm` of a test file, a `gh pr create` or a read of `.git`, and I had to keep watching the screen for the work to move forward. The alternative, turning permissions off, was worse: nothing stopped an `rm -rf` outside the project, a `cat .env` dumped into the context or a `git push --force`.

I wanted the opposite of both: an agent that no longer depended on me watching it, and dangerous operations that stopped on their own. I first built it as loose hooks inside one project; then I split them into a plugin to use anywhere. With Laya backing up the ambiguous cases, and with the rules I learned from its trace, I now give the agent much more freedom: I leave an autonomous run going and go to sleep without worrying about what it might touch.

---

## The case study

I've used Synapse daily since October 2026 across several of my own projects: monorepos with worktrees, autonomous runs lasting hours and parallel sessions with different agents, on WSL and Windows. Every plugin version came out of a failure seen in a real session and is documented with its symptom, cause, the test that covers it and the lesson.

The projects aren't named and the paths are examples; the numbers are real measurements from those sessions. Each chapter ends with an **In my case** block about what happened when I applied it.

---

## The agent-plugins family

Synapse lives in the [bypabloc/agent-plugins](https://github.com/bypabloc/agent-plugins) monorepo, the source of truth for my coding-agent plugins. Each plugin is also published to its own mirror repo and installed from the same marketplace (`bypabloc-agents`):

| Plugin | What it does | Agents |
| :-- | :-- | :-- |
| [synapse](https://github.com/bypabloc/agent-plugin-synapse) | The guardrails in this guide | Claude Code, Codex, Antigravity, OpenCode |
| [session-handoff](https://github.com/bypabloc/agent-plugin-session-handoff) | Keeps the task state on disk and re-injects it on start and compaction; won't let the turn end with pending work. Covered in [Keep your coding agent focused](https://post.the-full-stack.com/en/agents-handoff/) | Claude Code, Codex, Antigravity, OpenCode |
| [spanish-latam-style](https://github.com/bypabloc/claude-plugin-spanish-latam) | Neutral Latin American Spanish in answers, docs, commits and code | Claude Code (Codex runs its hooks) |

The third one came from a concrete problem. Several times, while working in Spanish, the agent wrote code, docstrings, commit messages and docs with Argentine *voseo* ("ejecutá", "fijate", "tenés"). I have no problem with voseo or with Argentinians, but it doesn't belong in code my coworkers review: code reviews were arriving with voseo nobody on the team uses. The plugin injects a neutral-Spanish rule on every session and every message, so it doesn't fade in long sessions, and ships a linter to check it in CI.

---

## Contents

| # | Chapter | What it solves |
| :-- | :-- | :-- |
| 01 | [Why an agent needs guardrails](01-el-problema.md) | What can go wrong and why native permissions aren't enough |
| 02 | [Installing on each agent](02-instalacion.md) | Claude Code, Codex, Antigravity and OpenCode, with requirements |
| 03 | [What it blocks, asks about and lets through](03-que-decide.md) | The four hooks and the four decisions |
| 04 | [Project scope and recoverable deletes](04-alcance-del-proyecto.md) | What "inside the project" means and when a delete needs no permission |
| 05 | [Secrets and .env files](05-secretos-y-env.md) | Reading `.env` without dumping it and not writing credentials |
| 06 | [Per-project configuration](06-configurar-por-proyecto.md) | Routine commands, exact exceptions and variables |
| 07 | [The trace: who decided and why](07-la-traza.md) | Reading the log and debugging a false positive |
| 08 | [Laya: a classifier that can only ask](08-laya.md) | What it is, its numbers and why it ships off |
| 09 | [Case study: porting to four agents](09-portar-a-cuatro-agentes.md) | Neutral core, adapters and the regression-free golden |
| 10 | [Codex and Windows: what cost hours](10-codex-y-windows.md) | The `ask` that stops the agent and the Windows failures |
| 11 | [Testing, updating and monitoring](11-probar-y-operar.md) | Tests, declarative cases, releases and monitoring |
| 12 | [Problems, myths and what was measured](12-problemas-y-soluciones.md) | What failed, what it doesn't do and the balance |

---

## Conventions

- **Example paths:** `~/code/my-app` is any project; `<plugin>` is the folder where the plugin got installed.
- **Tested versions:** Claude Code 2.1.329 (minimum 2.1.287), Codex 0.171.0 (minimum 0.171), Antigravity CLI `agy` 1.5.13 (minimum 1.5.4), OpenCode 2.3.2 (minimum V2 2.3), Python 3.10 or later. Synapse 1.7.3.
- **Evidence for each claim:** **[doc]** official documentation, **[test]** run and observed, **[measured]** with real numbers, **[real use]** seen over weeks of use, **[judgment]** reasoning without measurement.
- **Data as of:** November 2026.

`claude-code` `codex` `opencode` `antigravity` `security` `hooks` `guardrails`
