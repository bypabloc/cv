**08**

# Claude Code: compact without a summary

[← Index](README.md)

---

### Why

With the handoff on disk and re-injected by `SessionStart` `compact`, compaction still calls the model to summarize the whole conversation (~600k tokens at 60 % of 1M). That call is slow, and almost everything it produces is already in the handoff. The classic hooks don't replace it: `PreCompact` only changes the instructions or blocks it, and `SessionStart` acts once it is over.

This chapter explains the design and why it ended up this way. The code is in [chapter 09](09-receta-del-plugin.md).

### The piece that makes it possible: module plugins

Claude Code loads plugins with a TypeScript module that runs in-process and handles engine events (early access: the API may change). The `session.compact` event fires before every compaction (`/compact`, the threshold, another plugin or the precompute):

| Hook response | Effect |
| :-- | :-- |
| `next(e)` | Normal compaction: `PreCompact` and the model's summary |
| `next({ ...e, instructions })` or `next({ ...e, messages })` | Changes the instructions or what gets summarized |
| `{ skip: "reason" }` | Doesn't compact |
| Your own `{ messages }`, without `next` | **The conversation is left with those messages and the summarizer doesn't run** |

A message returned with its `handle` stays exactly as the engine holds it, tool blocks included. One without `handle` is rebuilt from its `role` and text, without `thinking` or attachments.

### The final design

1. **Precompute** (early summary): skipped with `skip`; it compacts when needed, with that moment's state.
2. **Subagent:** `next(e)`, normal summary.
3. **Is there a linked task?** If not, `next(e)`.
4. **The tail:** the most recent messages that fit in ~80 000 characters (~20k tokens, at ~4 characters per token):
   - The cut opens on an assistant message or on a user message **without** tool results: no result is left without its call.
   - Turns before the user's last request are returned **without `handle`**: the engine rebuilds them without `thinking` or nested rules.
   - The current turn stays whole (the API requires its `thinking` intact), and each whole message weighs ×3 in the budget.
   - If no safe cut fits with that weight, it retries unweighted; same if the cut leaves fewer than 12 messages and more fit unweighted.
   - If it still doesn't fit, `next(e)`.
5. **Response:** a notice ("conversation compacted without a summary; the handoff comes separately and wins; if the work is not done, continue with the next step"), an "Understood." (omitted if the tail opens on the assistant, so roles alternate) and the tail. It does **not** repeat the handoff: `SessionStart` `compact` injects it right after.
6. **Log:** each decision (`kept` with how many messages, or `fallback` with its reason) goes to the handoff log.

On the plugin's path, **`PreCompact` doesn't run** (nor do global hooks that depend on it, like a transcript backup); `PostCompact` and `SessionStart` `compact` do.

### Installation: local marketplace with `project` scope

In `.claude/settings.json`, versioned:

```json
"enabledPlugins": { "<plugin>@<marketplace>": true },
"extraKnownMarketplaces": { "<marketplace>": { "source": { "source": "directory", "path": "./<folder>" } } }
```

Once per machine, **from the main checkout**:

```bash
claude plugin marketplace add ./<folder> --scope project
claude plugin install <plugin>@<marketplace> --scope project
git checkout .claude/settings.json   # the CLI reorders the file and stores an absolute path
claude plugin list                   # Scope: project · Read from: <repo>/<folder>/<plugin>
```

- **The CLI rewrites `settings.json`** with the absolute path: restore the versioned one.
- **Don't install from a worktree:** the user registry stores that path and breaks when you delete it. Fix: `uninstall`, `marketplace remove` and repeat from the main checkout.
- `install` without the prior `marketplace add` fails with "not found in marketplace".
- After editing the plugin, `/reload-plugins` reloads it without reinstalling.

### Optional: the task state on screen

The same plugin can read the status lines (the script's `--status` mode) on startup, on each prompt, at the end of the turn and after each `Write` or `Edit`:

- The **spinner** shows `<Phase> · <Current> · ETA <ETA>` while the turn works.
- A one-line **band** above the prompt with `● status · phase · ETA · ctx <n>%`; the reason only if it is `blocked`. The percentage comes from the `session.measure` hook. A band with full paragraphs took half the screen.

### Limits

- Claude Code only; the other agents keep their compaction and their handoff.
- Plugins have no sandbox: this one runs `git` and `python3` in the session's directory.
- With `--resume`, the message chain brings back the originals with their `thinking`: the trim only applies to the current session.
- Whatever is not in the handoff or the tail is lost: keep `PROGRESS.md` current.

### In my case

The final design is the seventh version. Every row is a real failure:

| Version | Problem | Fix |
| :-- | :-- | :-- |
| Limit to the last 3 prompts | Hook reminders are also user messages with text | Size budget only |
| Repeat the handoff in the response | It arrived twice (`SessionStart` runs anyway) | Only the notice |
| ~80k tail that only opened on a user message with text | In autonomous runs, with no user messages for hours, it fell back to the summary in 31 of 32 compactions | Also open on the assistant |
| The same tail, measured in real use | It measured far more than the cap (p90 316k): ~90 % was `thinking` and nested rules the estimator didn't see | Old turns without `handle` and a ~20k cap |
| Unweighted | In autonomous runs everything is one turn: nothing got trimmed (188 of 188 messages) | ×3 weight for whole messages |
| With ×3 weight | A batch of 14 parallel reads didn't fit and fell back to the summary | Unweighted retry |
| Weighted cut | Once it left 6 of 1006 messages and the agent re-read the plan | Minimum of 12 |

The result, measured over my transcripts: the plugin answers in ~90 ms against a 52 s median for the summary, and saves ~37–64 s per compaction. On tokens it **saves nothing**: the next settled call came out at ~133k against ~124k with a summary. I keep it for the time and because recent turns stay verbatim, not paraphrased ([ch. 12](12-problemas-y-soluciones.md)).

`claude-code` `plugin` `compaction` `design`
