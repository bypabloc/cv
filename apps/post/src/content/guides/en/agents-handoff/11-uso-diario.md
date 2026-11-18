**11**

# Daily use and several sessions

[← Index](README.md)

---

### Once per machine

- **Claude Code:** install the compaction plugin from the main checkout ([ch. 08](08-compactar-sin-resumen.md)), if you use it.
- **Codex:** install the user hook with its per-repo guard, approve it in `/hooks` and restart the session ([ch. 05](05-configurar-cada-agente.md)).
- **OpenCode:** `opencode service restart` after changing the plugin or `opencode.json`.

### The routine

1. **Open sessions at the main checkout's root** and work in worktrees under `../<repo>-worktrees/`.
2. **Link the session:** write the task name to `tmp/handoff/.sessions/<session_id>` with the file tool; the hook gives you the `session_id` on startup.
3. **Keep the status lines** at the top of `PROGRESS.md`, in English and ≤ 120 characters. Update them after each commit or decision and before a long run or a pause.
4. **Waiting is not blocking:** CI, a merge, a lock or a shared resource are `Phase: external-wait`.
5. **Decide and record** in the decision log instead of asking, except for the four `blocked` categories.
6. **After a long pause:** Claude Code and OpenCode continue on their own. In Codex and Antigravity, open a new session and type "resume task `<name>`", or resend the message if you prefer the full context.
7. **When compacting:** with the Claude Code plugin there is no summary, only the handoff and ~20k recent tokens survive. Without the plugin, `PreCompact` asks the summary to keep the task and the next step.
8. **When the task closes:** delete its handoff folder and its links in the same step you remove the worktree.
9. **To review what happened:** check `tmp/handoff/.log/events.jsonl`.

### Keep the agent working

| What happened | What fixes it |
| :-- | :-- |
| It took a token-budget warning as a limit: compacted, summarized and ended the turn | The re-injected message orders it to continue with the `Next step` and clarifies those warnings are not a limit. A `Stop` hook blocks the end of the turn while there is a `Next step` without `Status: done\|blocked`, and lets it stop after 3 blocks in a row without changes to `PROGRESS.md` (anti-loop) |
| It marked `blocked` for a wait and, on resuming, asked even though the reason no longer existed | The wait is `external-wait`, and there `Stop` lets it stop. On resuming a `blocked`, it checks the reason and, if it no longer applies, continues without asking |
| It stopped to ask "(a) or (b)" about something it could decide | `blocked` requires a category: **production data**, **cost**, **credentials** or **a user request to stop**. A `PreToolUse` rejects the question tool while a plan runs. Every other decision is made by picking the right option, not the fastest one, and recorded in a versioned log with reason and alternatives |
| The status lines were ~1500-character paragraphs and `PROGRESS.md` weighed 14 KB | A 120-character cap. The warning arrives **right after editing** the file (`PostToolUse`): with the warning only on re-injection, the session went back to writing them long |
| Hours waiting on a lock whose process had already died | Before waiting or declaring `blocked`, `kill -0 <pid>` on the lock: no file or a dead PID means it is free |
| It wrote the link with `echo >` and a guardrail blocked it | The rule says the handoff is written with the file tool |

### Autonomous runs

In an autonomous run the user doesn't type for hours, and everything that depended on "the user's last message" failed: the plugin only opened the tail on a user message, and everything was a single turn, so trimming old turns trimmed nothing ([ch. 08](08-compactar-sin-resumen.md)).

A periodic reminder (cron) woke the session six times, and each time it delivered a report and stopped. **The reminder's prompt must order it to resume the work** after the report, not just to report.

### Worktrees outside the repo

- With worktrees in a folder **inside** the repo, a main-checkout session loads the worktree's rules as nested rules, and the kept tail attaches them again, duplicated.
- Put them in `../<repo>-worktrees/<name>/`, declared in `permissions.additionalDirectories` to read and edit without prompts. Scripts that look for worktrees or transcripts must recognize the new path.
- **The rule alone was not enough:** a handoff written before the change had the old path and the agent followed it. A `Bash` `PreToolUse` hook that rejects `git worktree add <path inside the repo>` (exit 2 and the suggested path) stopped it. The rule must say it wins over what an old handoff says.
- Don't open sessions inside a worktree: the main checkout's handoff falls outside the workspace, and Claude Code, Codex and Antigravity ask for approval (in headless mode they deny it without failing).

### Heavy shared resources: one turn per host

Several sessions running E2E against a real stack, API recordings and benchmarks at the same time saturate the machine. The protocol:

1. Before a heavy run, a command that reads `/proc` and the agent's session registry says who is using the resource (exit 0 free, 1 busy), which session it hangs from and which project sessions are open.
2. Free: tell the other sessions "taking the resource" and run.
3. Busy: ask the owner to announce when it frees up, schedule a check every ~10 min **only while waiting** and continue with what doesn't use it.
4. When done: announce "free" and delete the check.

The turn's state goes in `PROGRESS.md`, and the re-injected message repeats the protocol: that is how it survives compaction.

### Instructions cut without warning

Every agent has an instruction limit and none of them fails loudly:

| Agent | What happened |
| :-- | :-- |
| Claude Code | It warned "21 instruction files add up to 150.7k chars, over the 150.0k-char total limit" |
| Codex | It read `AGENTS.md` (~50 KB) truncated to 32 KiB, the default `project_doc_max_bytes` |
| Antigravity | It dropped 17 rules without a `trigger` frontmatter; there is also a ~24 KB limit per rule |

- A pre-commit check that discovers what each agent loads (repo and home), measures it against its limits and fails naming the file to trim.
- Rules as **a short core + a reference**: what is always loaded stays short, and detail goes into a document read when needed.
- Your own limits: ~15 000 characters per file and ~80 000 for everything always loaded.

### In my case

With the worktrees inside the repo, on entering each new worktree the call right after compacting rose to ~120k and ~131k (against ~95k): +24k to +45k tokens just from duplicated rules. Moving them out and adding the hook that blocks `git worktree add` inside the repo solved it. As for instructions, `AGENTS.md` went from 49 KB to 6.5 KB once it was split into core and reference.

`worktrees` `parallel-sessions` `autonomy` `workflow`
