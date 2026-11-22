# Code Mode in Claude Code: when it saves and when it doesn't

> A practical guide to Code Mode, the experimental Claude Code mode in which the model writes JavaScript to chain its tools instead of asking for them one by one: how to turn it on, what changes, where the savings come from, which tasks it pays off in and which ones get slower, what happens to permissions and hooks, and how to measure it in your own projects. With my measurements on real projects.

**Cost:** USD 0 (ships with Claude Code) · **Time:** ~10 min to turn it on, ~1 h to measure it properly · **Level:** intermediate (terminal, hooks, permissions)

---

## TL;DR

- **What it is:** with `CLAUDE_CODE_EXPERIMENTAL_CODE_MODE=1`, Claude stops calling tools one at a time and writes a script that searches, reads, edits and tests in a single step; only what the script returns goes back to the model ([ch. 01](01-que-es.md)).
- **Where it saves:** on tasks with many calls whose results can be reduced to a total, a count or a short list, especially through MCP. There, the added context drops to a fraction ([ch. 05](05-cuando-ahorra.md)).
- **Where it doesn't:** on local file work that Claude already solved with an `rg` or a Python script. It can come out the same or **slower**, sometimes with hundreds of individual reads ([ch. 06](06-cuando-no.md)).
- **A fixed saving:** every session starts about 13 thousand tokens smaller in tool definitions ([ch. 04](04-de-donde-sale-el-ahorro.md)).
- **Security:** every internal call goes through your rules and hooks; the auto mode classifier, however, reviews the whole script without seeing values computed at run time ([ch. 09](09-permisos-y-hooks.md)).
- **Requirements:** interactive terminal, native install, a direct Anthropic account and Opus 5.5, Sonnet 5.5, Haiku 5.5 or Fable 5.2. It doesn't run with `claude -p`, VS Code or Desktop ([ch. 02](02-activar.md)).
- **Don't trust a single percentage:** measure the same task with the mode on and off ([ch. 11](11-medirlo.md)).

---

## Where the idea came from

I follow every Claude Code release closely, and when 2.1.323 (November 12, 2026) shipped Code Mode it caught my attention right away: the promise was that the model would stop making one trip per tool and solve in a script what used to take ten turns. I work with long sessions and autonomous runs, so every trip saved shows in time and in quota.

The promise came without official numbers: Anthropic didn't publish how much it saves. So instead of trusting the percentages that started circulating, I turned it on in my projects and compared.

---

## The case study

I've been using it for about eight days on real work: **klinikae** (a web platform with a backend and several apps) and **content-studio** (a content studio with video workflows), plus this portfolio and my plugins monorepo. I used it on WSL and Windows, mostly with Opus 5.5 and some sessions with Haiku 5.5.

The numbers from my sessions come from the transcripts Claude Code keeps ([ch. 07](07-mis-mediciones.md)); tests published by others are separate, with their source ([ch. 08](08-lo-que-midieron-otros.md)). Each chapter ends with an **In my case** block.

---

## Contents

| # | Chapter | What it solves |
| :-- | :-- | :-- |
| 01 | [What Code Mode is and what changes](01-que-es.md) | From step by step to a script |
| 02 | [Turning it on and checking it's on](02-activar.md) | Requirements, variable, `/status` and `Ctrl+O` |
| 03 | [What a code block looks like](03-anatomia-de-un-bloque.md) | What Claude writes, what it returns and its limits |
| 04 | [Where the savings come from](04-de-donde-sale-el-ahorro.md) | The two sources and the 37 % myth |
| 05 | [When it saves](05-cuando-ahorra.md) | The tasks where it pays off |
| 06 | [When it doesn't (and is slower)](06-cuando-no.md) | Local files, individual reads and filters that hide data |
| 07 | [My measurements](07-mis-mediciones.md) | What my real sessions show |
| 08 | [What others measured](08-lo-que-midieron-otros.md) | Public tests, with their source |
| 09 | [Permissions, hooks and security](09-permisos-y-hooks.md) | What each layer checks and what stays blind |
| 10 | [Known limits and bugs](10-limites-y-fallos.md) | What doesn't work yet |
| 11 | [How to measure it in your project](11-medirlo.md) | An honest A/B in an afternoon |
| 12 | [Problems, myths and verdict](12-problemas-y-balance.md) | What fails, what circulates and my decision |

---

## Conventions

- **Version:** Claude Code 2.1.330 (the latest as of November 22, 2026). Code Mode changed a lot in a few days: numbers measured on 2.1.325–2.1.327 may not represent the current version.
- **Evidence for each claim:** **[doc]** official documentation or changelog, **[measured]** in my sessions, **[published]** a third party's measurement with its source, **[judgment]** reasoning without measurement.
- **Processed tokens:** input plus cache reads and writes. Cache reads cost much less, so "fewer tokens" isn't always "lower cost".
- **Data as of:** November 2026.

`claude-code` `code-mode` `experimental` `tokens` `mcp` `hooks` `productivity`
