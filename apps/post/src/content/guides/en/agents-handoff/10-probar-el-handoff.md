**10**

# Prove the handoff arrives

[← Index](README.md)

---

### The principle: test with a marker

The file existing, or the hook exiting 0, does not prove the model received the handoff. The test that tells them apart:

1. Write an **invented marker** (`WK-208`, `OT-555`) in a test task's `PROGRESS.md`.
2. Link the session to that task.
3. Ask the agent for the marker **forbidding it to read files or run commands**.

If it answers with the marker, it could only get it from what was injected.

- In a session **without a link**, the list of active tasks includes each one's next step and the marker could leak through there: link the session to **another** task with another marker and check it answers that one.
- When done, delete the task, the links and the pause state.

### Claude Code: `claude -p`

```bash
claude --permission-mode bypassPermissions --model haiku \
  --disallowedTools "WebSearch" "WebFetch" "Bash" "Read" "Glob" "Grep" \
  --strict-mcp-config --mcp-config '{"mcpServers":{}}' \
  --output-format json -p "What is the task's next step?" </dev/null > tmp/config-tests/marker.json
jq -r '.is_error, .result' tmp/config-tests/marker.json
```

- Without `Bash`, `Read`, `Glob` or `Grep`, the answer can only come from the injected context.
- Real `/compact`: create the session with `-p`, link it and run `--resume <id> -p "/compact"`; the transcript must show the handoff after compacting.
- Compaction plugin: the same, with `--debug-file`, looking for the summarizer not having run ([ch. 09](09-receta-del-plugin.md)).

### Codex: `codex exec`

```bash
codex exec --ephemeral -s read-only -c model_reasoning_effort='"low"' \
  -o tmp/config-tests/marker.txt "What is the task's next step?" </dev/null
```

- Without `</dev/null`, `codex exec` waits for stdin.
- The output shows `hook: SessionStart Completed` (it ran) or `Failed` (its output is invalid).
- An inline hook, without writing files: `-c 'hooks.SessionStart=[…]'` with `--dangerously-bypass-hook-trust` (tests only).
- Configuration: `codex debug prompt-input` (0 if valid). Trust and loaded layers: `codex doctor`.

### Antigravity: `agy -p`

```bash
agy -p 'hello' --output-format json </dev/null                      # returns conversation_id
# write the task name into tmp/handoff/.sessions/<conversation_id>
agy -p "What is the task's next step?" --conversation <id> --output-format json </dev/null
```

- If the hook doesn't seem to run, check the most recent log in `~/.gemini/antigravity-cli/log/`.
- `agy -p '/compact' --conversation <id>` creates a `CHECKPOINT` whose summary includes what was injected.
- To measure whether the `ephemeralMessage` accumulates, add up `input_tokens` and `cache_read_tokens` of each `PLANNER_RESPONSE` in the transcript.

### OpenCode: `opencode run`

```bash
opencode service restart && opencode debug config        # checks compaction.buffer
opencode run --standalone -s ses_test01 --format json "What is the task's next step?" </dev/null
```

- `--standalone` bypasses the background service, which keeps the old `setup`; `--print-logs` shows `loading plugin`.
- To confirm the plugin runs the script: a `python3` wrapper on the `PATH` that logs every call.

### Simulated long pause

Write `{"last": 0}` to `tmp/handoff/.idle/<id>` and send the next message:

| Agent | What you should see |
| :-- | :-- |
| OpenCode | Turn 1 "remember TULIPAN"; after the pause, the session doesn't know the word and copies the `Next step`; the state stores the cut |
| Antigravity | Exit 3, `status: ERROR` and the notice, with no `PLANNER_RESPONSE`. Resending answers |
| Codex | `hook: Stop Completed` records the time; after the pause, `hook: UserPromptSubmit Blocked`; resending answers |

### Unit tests for the script

| Group | What it covers |
| :-- | :-- |
| Current task | The link wins; two sessions on the same branch don't clash; the branch's plan number; rejecting `../` and links to folders that don't exist |
| Message | Injection and truncation; session without a link; silence without an id; text by state, phase and event |
| Main checkout | **A real git repo with a worktree**: from the worktree, the main checkout and a subfolder; outside git, nothing |
| Input and output | snake_case, camelCase, default `source`; each agent's JSON |
| Status lines | Bullets, bold, missing keys, long lines |
| End of turn and questions | Blocks; lets it stop when done, validly blocked, waiting externally or at the cap |
| Pauses | Thresholds, corrupt state, unsafe ids, Antigravity cut only with `invocationNum` 0, persistent OpenCode cut, variable at `0`, a long command that doesn't trigger the cut |
| Codex installer | A merge that keeps foreign hooks, idempotency, backup and **a foreign repo with the script that doesn't run it** |

### What short tests don't cover

| What | Why | How to close it |
| :-- | :-- | :-- |
| That compaction happens exactly at the threshold | You'd have to fill the context | Measure in real use from the transcripts ([ch. 12](12-problemas-y-soluciones.md)) |
| Interactive Codex with the user hook | It must be approved in `/hooks` | Install, approve and ask for the marker |
| Real 10, 30 or 55 min pauses | They are simulated | The notice says how many minutes passed |
| OpenCode plugins in the service | Tests use `--standalone` | `opencode service restart` and check usage |

### In my case

In OpenCode, after the pause cut, the next turn wrote 145 tokens and read ~59k (system and tools); the one after, 164. And one bug that only the real test showed, not the unit tests: inside a worktree, no copy of the OpenCode plugin acted because of the repeated `id` ([ch. 05](05-configurar-cada-agente.md)). Short tests also missed what showed up over weeks of use: autonomous runs, several sessions at once and large batches of parallel tools ([ch. 11](11-uso-diario.md)).

`testing` `headless` `hooks` `verification`
