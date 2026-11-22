# Keep your coding agent focused

> A practical guide to making Claude Code, Codex, OpenCode and Antigravity carry a long task without losing decisions or the current step: compact earlier, keep the state on disk, re-inject it with hooks, resume after a long pause without paying for the whole history, and stop the agent from cutting the work short. With the real case study from my projects and its measured numbers.

**Cost:** USD 0 (configuration and one script) · **Time:** ~2 h the first time · **Level:** advanced (hooks, git worktrees, Python, TypeScript)

---

## TL;DR

- **The problem:** when the context fills up, the agent summarizes the conversation and the summary loses decisions, the next step and the pitfalls already found. After a long pause the cache also expires, and the next message is billed in full.
- **Compact earlier:** a threshold versioned in the repo. Claude Code at 60 %, Codex at 65 % plus a token cap, OpenCode with 40 % of the window free.
- **On-disk handoff:** `tmp/handoff/<work>/` with `PROGRESS.md`, `DECISIONS.md` and `NOTES.md`. A single script re-injects it into all four agents after compacting, on startup and after a pause.
- **Keep the agent going:** an end-of-turn hook that won't let it stop while there is a `Next step`; `blocked` only for four reasons.
- **Compact without a summary (Claude Code):** a plugin keeps the most recent ~20k tokens verbatim. It saves ~37–64 s per compaction; on tokens it comes out close to a tie.
- **Ready-to-install plugin (Claude Code, Codex, Antigravity and OpenCode):** [session-handoff](https://github.com/bypabloc/agent-plugin-session-handoff), from the [agent-plugins](https://github.com/bypabloc/agent-plugins) monorepo, packages the handoff, the end-of-turn block and, in Claude Code, the summary-free compaction ([ch. 09](09-receta-del-plugin.md)).
- **Several sessions:** worktrees outside the repo, one folder per task and one link per session.

---

## Where the idea came from

It started with a post going around on social media. It suggested asking Claude, in `CLAUDE.md`, to start every answer with your name: not to be friendly, but as a **canary**. The model doesn't go from working well to hallucinating all at once; first it stops following a small instruction. If one day it stops calling you by name, the canary died and it's time to open a new session. The post attributed the technique to Peter Steinberger, the creator of OpenClaw.

When I checked the source, Steinberger himself denied it [on X](https://x.com/steipete/status/2113741901384089824): he never called it a canary, and he doesn't have `CLAUDE.md` files.

The attribution was false, but the underlying observation was useful: the context window degrades gradually, and by the time you notice, the agent is already working from a summary that lost what mattered. Instead of waiting for the canary to die, I wanted the session not to depend on what the conversation remembers. That is where the on-disk handoff came from: manage the task's knowledge outside the context, re-inject it when needed, and compact before the window saturates. The marker test in [chapter 10](10-probar-el-handoff.md) is, in fact, a deliberate canary: a fact the agent can only answer if the handoff arrived.

---

## The case study

I built and used everything that follows in my own projects: a monorepo with several apps and a backend, where I work in sessions that last hours, autonomous runs that execute one plan after another without me typing anything, and up to four sessions in parallel, each in its own worktree. I tested the four agents with their November 2026 versions and left the system running for several weeks before writing this.

Paths and task names are anonymized; the numbers are real measurements from those sessions. Each chapter ends with an **In my case** block that tells what happened when I applied it.

---

## Index

| # | Chapter | What it covers |
| :-- | :-- | :-- |
| 01 | [Why the agent loses track](01-el-problema.md) | The six problems and which part of the guide solves each one |
| 02 | [Compact earlier](02-compactar-antes.md) | Each agent's versioned threshold and how to check it |
| 03 | [The on-disk handoff](03-handoff-en-disco.md) | The three files, the status lines and where they live |
| 04 | [The shared hook script](04-script-comun.md) | One dependency-free Python script for the four agents |
| 05 | [Configure each agent](05-configurar-cada-agente.md) | Claude Code, Codex, OpenCode and Antigravity, with their pitfalls |
| 06 | [Know when the cache expired](06-cache-de-prompt.md) | TTL, usage fields and measurements per agent |
| 07 | [Resume after a long pause](07-pausa-larga.md) | Continue from the handoff instead of resending the history |
| 08 | [Claude Code: compact without a summary](08-compactar-sin-resumen.md) | The plugin's design and why it ended up this way |
| 09 | [The plugin recipe, step by step](09-receta-del-plugin.md) | Full code, tests and installation |
| 10 | [Prove the handoff arrives](10-probar-el-handoff.md) | The marker test and the headless commands |
| 11 | [Daily use and several sessions](11-uso-diario.md) | Routine, status, decisions and shared resources |
| 12 | [Problems, myths and what was measured](12-problemas-y-soluciones.md) | What failed, what circulates and is false, and the balance |

---

## Conventions

- **Example paths:** `<repo>` is the main checkout (`~/code/my-app`); `../<repo>-worktrees/` is the worktrees folder, **outside** the repo; `<plan>` is the task's spec folder (`docs/specs/042-login-form/`).
- **Handoff:** `<repo>/tmp/handoff/`, inside a git-ignored folder. The script lives in `<repo>/agent-hooks/session_handoff.py` (versioned).
- **Versions tested:** Claude Code 2.1.3xx, Codex `codex-cli 0.167.0`, OpenCode `2.0.29` and Antigravity CLI `agy 1.5.3`.
- **session-handoff plugin 0.5.4:** Claude Code 2.1.287 or later, Codex ≥ 0.171, `agy` ≥ 1.5.4 and OpenCode V2 ≥ 2.3 (tested with Codex 0.171.0, `agy` 1.5.13 and OpenCode 2.3.2).
- **Evidence for each claim:** **[doc]** official documentation, **[bin]** seen in the binary or its cache, **[test]** run and observed, **[measured]** with real numbers, **[calculation]** from official prices, **[real use]** seen over weeks of use, **[community]** unverified blog or issue, **[judgment]** reasoning without measurement. When an agent updates, re-test whatever is marked **[test]** and **[bin]**.
- **Data as of:** November 2026.

`claude-code` `codex` `opencode` `antigravity` `context-engineering` `hooks` `prompt-caching`
