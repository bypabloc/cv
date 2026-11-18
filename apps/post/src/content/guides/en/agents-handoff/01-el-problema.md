**01**

# Why the agent loses track

[← Index](README.md)

---

### What compacting is

When the context fills up, the agent **compacts**: it replaces the conversation with a summary written by a model and drops tool outputs (files read, logs, diffs). That is what makes hours-long sessions possible, but it has a cost.

### The six problems

| # | Problem | What happens | Where it is solved |
| :-- | :-- | :-- | :-- |
| 1 | **Late compaction** | Compacting near the limit gives a worse summary: the model summarizes a huge conversation with little room, and the last turns work saturated | [Ch. 02](02-compactar-antes.md) |
| 2 | **What gets lost when compacting** | The summary drops or distorts decisions, the current step and the pitfalls already found: the agent repeats mistakes or goes backwards | [Ch. 03](03-handoff-en-disco.md) to [05](05-configurar-cada-agente.md) |
| 3 | **Expired cache** | After a pause longer than the TTL, the next message resends the whole history with no discount | [Chs. 06](06-cache-de-prompt.md) and [07](07-pausa-larga.md) |
| 4 | **The summary is redundant** | With the state on disk, the summarizing call is slow and almost everything it produces is already written down | [Chs. 08](08-compactar-sin-resumen.md) and [09](09-receta-del-plugin.md) |
| 5 | **The agent cuts the work short** | It ends the turn after compacting, asks what it could decide, or keeps waiting | [Ch. 11](11-uso-diario.md) |
| 6 | **Several sessions at once** | They overwrite each other's state or saturate shared resources | [Ch. 11](11-uso-diario.md) |

### Why the summary is not enough

- **It is a paraphrase.** Another model call writes it and decides what to keep. A decision with its reason becomes "X was decided"; the reason disappears and gets argued again.
- **It enforces nothing.** Asking the summary to "re-read `PROGRESS.md`" does little: the instruction stays as text and the model may ignore it. What brings the information back into the context is a **hook**.
- **It also affects the rules.** With Codex's remote compaction, `AGENTS.md` and the rules go through the summarizing model too. **[community]** ([CompressAgent](https://codex.danielvaughan.com/2026/08/28/control-under-compression-agent-control-context-reliability-codex-cli-compaction-agents-md/))

### Factory defaults

| Agent | When it compacted |
| :-- | :-- |
| Claude Code with a 1M window | Around 967K tokens, ≈97 % **[doc + test]** |
| Codex with a 272k window | At the model's limit; end-of-turn compaction off **[doc]** |
| OpenCode | With the default `buffer` **[doc]** |
| Antigravity | No documented value **[bin]** |

The "83 %" quoted in blogs for Claude Code belongs to the old 200K window.

### The idea behind the guide

> **What is on disk survives compaction; the conversation does not.**

The agent keeps a few short files with the state of the task. After compacting (or on startup, resume, or coming back from a pause), a hook injects them into the context. The agent continues from data it wrote itself, not from a summary written by another model.

### What you will build

1. A versioned compaction threshold per agent ([ch. 02](02-compactar-antes.md)).
2. The handoff folder and its status lines ([ch. 03](03-handoff-en-disco.md)).
3. One shared script that answers the hooks of the four agents ([chs. 04](04-script-comun.md) and [05](05-configurar-cada-agente.md)).
4. Long-pause detection ([chs. 06](06-cache-de-prompt.md) and [07](07-pausa-larga.md)).
5. Optional, in Claude Code: a plugin that compacts without a summary ([chs. 08](08-compactar-sin-resumen.md) and [09](09-receta-del-plugin.md)).
6. Tests that prove the model receives the handoff ([ch. 10](10-probar-el-handoff.md)).

### In my case

The system did not come out in one go. The first version was one handoff folder per branch, and each of the six problems showed up as a concrete failure: two sessions on the same branch overwrote each other's state, a worktree's handoff never reached the main checkout's session, and the agent, with the handoff correctly injected, still ended the turn on a budget warning. The design reached its fourth version ([ch. 03](03-handoff-en-disco.md)), and the compaction plugin went through seven ([ch. 08](08-compactar-sin-resumen.md)). This guide is the final version, with the failures that explain it.

`compaction` `context` `handoff` `problem`
