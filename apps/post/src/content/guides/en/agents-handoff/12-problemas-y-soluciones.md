**12**

# Problems, myths and what was measured

[← Index](README.md)

---

### Problems and solutions

| Problem | Cause | Solution |
| :-- | :-- | :-- |
| The Codex hook doesn't run in a worktree | Project hooks only run in trusted, approved paths; each worktree is another path | A **user** hook with a per-repo guard |
| Codex marks the hook as `Failed` | The output starts with `[` and is read as JSON | Emit JSON (`hookSpecificOutput.additionalContext`) |
| Codex injects the handoff twice | User hook plus `.codex/hooks.json` in the repo | Only the user one |
| I changed the Codex hook and it stopped running | Trust is stored by hash | Re-approve in `/hooks` and restart |
| `agy` ignores `.agents/hooks.json` | Claude Code format or malformed JSON; the error only goes to the log | Map of named hooks; check `~/.gemini/antigravity-cli/log/` |
| OpenCode ignores `compaction.buffer` | `"40%"` is dropped in 2.0.29 | An integer (`400000`) and `opencode debug config` |
| The OpenCode plugin doesn't act in a worktree | Two plugins with the same `id` | Checkout path in the `id` |
| The OpenCode plugin doesn't pick up changes | The background service keeps the old `setup` | `opencode service restart`; test with `--standalone` |
| The new script doesn't run | The agents run the main checkout's copy, which is behind | Update the main checkout after merging |
| The Claude Code plugin broke | It was installed from a worktree that got deleted | `uninstall`, `marketplace remove` and repeat from the main checkout |
| The task shows up without a next step | Translated status keys (`Siguiente paso:`) | Keys in English |
| `PROGRESS.md` grows and gets truncated | It is used as a log | Current state; history lives in `git log` |
| The agent follows an old handoff | It wasn't updated before a pause or a compaction | Rewrite it after each commit and decision; check it against git |

### Claims that turned out false

After implementing, I checked each claim against the official documentation and recent sources, and tested each discrepancy with the installed versions (Claude Code 2.1.319, Codex 0.167.0, OpenCode 2.0.29, agy 1.5.3). Several of them circulate in blogs:

| # | Claim | Reality | Evidence |
| :-- | :-- | :-- | :-- |
| 1 | Codex ignores plain text in the `SessionStart` output | **It injects it.** It only fails if the output starts with `[` | Plain text with a marker: the model answered it; with `[`: `Failed` |
| 2 | `agy -p` doesn't accept slash commands | **It does**; `/compact` created a `CHECKPOINT` | Test and `--disable-slash-commands` in `agy --help` |
| 3 | Antigravity's `ephemeralMessage` doesn't stay in the trajectory | **It is saved** (and the summary uses it), but it is **not resent** | +1500 tokens on the linked turn and +210 per turn afterwards |
| 4 | Claude Code's `PreCompact` doesn't influence the summary | **Its stdout is instructions for the summary**; exit 2 blocks it | Documentation and a real `/compact` |
| 5 | OpenCode asks for confirmation to write outside the project | `external_directory` **allows it by default** | Documentation |
| 6 | Codex's 90 % cap applies since a certain version | It comes from an upstream PR; the version was not confirmed | Upstream code |
| 7 | `model_auto_compact_token_limit` acts mid-turn | The documentation doesn't say so; it comes from a blog | Documentation |

Not confirmed in the documentation, but confirmed in practice: OpenCode's `context` hook, Claude Code subagents receiving their parent's `session_id` (only an issue says so) and `agy`'s hook error log.

### Measuring compaction: the metrics lie

A single `/compact` test measures speed, not tokens. You need a script that reads the transcripts of the checkout and its worktrees and separates two cohorts: compactions without a summary (under 2 s) and with one.

| Lesson | Detail |
| :-- | :-- |
| The post-compaction size the agent reports is misleading | It excludes the session's base and the tail's attachments. Measure the **input of the first call** after the cut |
| The first call isn't enough either | Between the first and second calls, Claude Code restores its listings (skills, deferred tools, agents, MCP: ~20k). Compare the **settled call** |
| Filtering by file date mixes versions | A long session drags in its old compactions. Filter each one by its `timestamp`, in UTC |
| Re-reading the handoff is not rework | It is what the rule asks for. Exclude it from the metric |
| Count responses, not entries | A response logged in several entries with the same id is a single call |

### In my case: the balance

| Measurement | Result |
| :-- | :-- |
| 747 compactions, first plugin version | Without a summary: 89 ms median, 69 min saved over 80 compactions; same rework (4.4 % vs 4.5 %) |
| ~80k tail, first call | 197k median vs 164k for the summary: net −26.5M equivalent tokens |
| ~20k tail without old `thinking`, 14 compactions in one run | ~96k median, 0 fallbacks to the summary, 0 API errors, 0.4 % rework |
| Settled call (22 without summary, 2 with summary) | ~133k vs ~124k: net −3.19M; saves ~37–64 s per compaction |

**Conclusion:** compacting without a summary wins on time and on keeping recent turns verbatim; on tokens it comes close to a tie, slightly worse. Before changing the tail cap, measure from the time of the change: the net result must not get worse, rework must not go up and the time savings must hold. For reference, OpenCode V2 keeps 15k literal tokens, and a JetBrains study on SWE-bench shows that masking old tool results matches or beats LLM summarization at half the cost.

### What I didn't measure

- **The hallucination rate before and after.** What there is: marker tests proving the right information reaches the model (after `/compact`, on resume and after a pause) and compaction measurements from real sessions.
- **Summary quality at 60 % against 97 %.**
- The measured rework only counts exact repeats of reads or commands: it doesn't see errors from lost context.

### Risks to keep in mind

- **An outdated handoff is worse than none:** the agent trusts it.
- **The cut, the new session and summary-free compaction discard whatever was not written to disk.**
- **Friction:** Codex and Antigravity block the first message after the pause once.
- **Secrets:** the handoff enters the model's context and may stay in transcripts. Never tokens, `.env` or PII.

`troubleshooting` `measurements` `myths` `compaction`
