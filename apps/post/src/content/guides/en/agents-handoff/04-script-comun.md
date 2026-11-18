**04**

# The shared hook script

[← Index](README.md)

---

### One script, four agents

`agent-hooks/session_handoff.py` (dependency-free Python, versioned in the repo) answers every event of the four agents and returns the output in each one's format. Keeping **a single** piece of logic prevents the agents from receiving different messages for the same state.

### Inputs it handles

| Input (stdin JSON) | Source | Response |
| :-- | :-- | :-- |
| `{"session_id","cwd","source"}` | `SessionStart` of Claude Code and Codex | The handoff in `additionalContext`. Without `source`, assumes `compact` |
| `{"hook_event_name":"PreCompact", …}` | Claude Code | Plain text: what the summary must keep (task, path, next step) |
| `{"hook_event_name":"Stop", …}` | Claude Code | `decision: block` while there is a `Next step` without a terminal status; capped at 3 blocks without changes |
| `PreToolUse` of the question tool | Claude Code | Rejects the question while a plan is running, unless there is a `blocked` with a valid category |
| `PostToolUse` of `Write`/`Edit` | Claude Code | If a handoff `PROGRESS.md` was edited, names the status lines over 120 characters |
| `{"hook_event_name":"UserPromptSubmit", …}` | Codex | Nothing; after a long pause, `{"decision":"block","reason":…}` once |
| `Stop` with `--touch` | Codex | Records activity and prints `{}` |
| `{"conversationId","workspacePaths","invocationNum"}` | Antigravity `PreInvocation` | `injectSteps[].ephemeralMessage`; after a pause with `invocationNum` 0, `errorMessage` and `terminationBehavior: terminate` |
| The same with `--touch` | Antigravity `PostInvocation` | Records activity and prints `{}` |
| `{"session_id","cwd","source":"context","agent":"opencode","message_id"}` | OpenCode plugin | The handoff, plus the cut message id after a pause |
| `--status` | On-screen indicator ([ch. 08](08-compactar-sin-resumen.md)) | The status lines as JSON |
| `--log` | Compaction plugin | Logs its decision |

### Pieces

| Piece | What it does |
| :-- | :-- |
| `main_checkout(cwd)` | Parent of `git rev-parse --path-format=absolute --git-common-dir`: the main checkout, also from a worktree |
| `current_work(store, session_id, branch)` | The `.sessions/<id>` link and, if missing, the folder with the branch's plan number. Rejects unsafe names (`../`) |
| `active_works(store)` | Tasks with their `Next step` |
| `progress_fields(text)` | Reads the status lines (tolerates bullets and bold, not translated keys) |
| `build_message(...)` | Builds the text by state, phase and event; truncates each file to ~6000 characters |
| `render(message, output)` | Converts it to each agent's JSON |
| Texts module | Every message in one place: continue, decide, blocked, done, by phase, by event, end of turn, long line |
| Pauses module | Threshold per agent (Codex 30, Antigravity 10, OpenCode 55 min; one environment variable changes them and `0` turns them off), last activity in `tmp/handoff/.idle/<id>` and the OpenCode cut |
| Log | `tmp/handoff/.log/events.jsonl`: `inject`, `precompact`, `compact.kept`/`compact.fallback`, `stop.block`/`stop.release`, `idle.block`, with snapshots by hash |

### Minimal skeleton to start with

This skeleton covers the essentials: it finds the main checkout, reads the session's link, builds the message and answers in the Claude Code and Codex format or the Antigravity one. On top of it you add the pieces from the table above, one at a time.

```python
#!/usr/bin/env python3
"""Injects the handoff of the linked session (minimal skeleton)."""

import json
import re
import subprocess
import sys
from pathlib import Path

MAX_CHARS = 6000
FILES = ('PROGRESS.md', 'DECISIONS.md', 'NOTES.md')
SAFE = re.compile(r'^[\w.-]+$')


def main_checkout(cwd: str) -> Path | None:
    """Root of the main checkout, also from a worktree."""
    run = subprocess.run(
        ['git', 'rev-parse', '--path-format=absolute', '--git-common-dir'],
        cwd=cwd, capture_output=True, text=True, check=False,
    )
    if run.returncode != 0:
        return None
    return Path(run.stdout.strip()).parent


def current_work(store: Path, session_id: str) -> str | None:
    """Name of the task linked to the session, validated against ../."""
    if not SAFE.match(session_id):
        return None
    link = store / '.sessions' / session_id
    work = link.read_text().strip() if link.is_file() else ''
    ok = SAFE.match(work) and not work.startswith('.')
    return work if ok and (store / work).is_dir() else None


def build_message(store: Path, work: str, source: str) -> str:
    parts = [
        f'# Handoff: {work} ({source})',
        f'Folder: {store / work}',
        'These files win over any summary; check them against git status '
        'and git log. Continue with the Next step: budget warnings are '
        'not a limit.',
    ]
    for name in FILES:
        path = store / work / name
        if path.is_file():
            text = path.read_text()
            if len(text) > MAX_CHARS:
                text = text[:MAX_CHARS] + '\n[truncated]'
            parts.append(f'## {name}\n{text}')
    return '\n\n'.join(parts)


def render(message: str, data: dict) -> dict:
    if 'conversationId' in data:  # Antigravity PreInvocation
        return {'injectSteps': [{'ephemeralMessage': message}]}
    return {
        'hookSpecificOutput': {
            'hookEventName': 'SessionStart',
            'additionalContext': message,
        },
    }


def main() -> int:
    data = json.load(sys.stdin)
    session_id = data.get('session_id') or data.get('conversationId') or ''
    cwd = data.get('cwd') or (data.get('workspacePaths') or ['.'])[0]
    root = main_checkout(cwd)
    work = root and current_work(root / 'tmp' / 'handoff', session_id)
    if not work:
        print('{}')
        return 0
    store = root / 'tmp' / 'handoff'
    message = build_message(store, work, data.get('source', 'compact'))
    print(json.dumps(render(message, data)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
```

Test it by hand before wiring it to an agent:

```bash
mkdir -p tmp/handoff/.sessions tmp/handoff/042-login-form
printf 'Status: in-progress\nNext step: WK-208\n' > tmp/handoff/042-login-form/PROGRESS.md
echo 042-login-form > tmp/handoff/.sessions/test
echo '{"session_id":"test","cwd":"."}' | python3 agent-hooks/session_handoff.py | jq -r .hookSpecificOutput.additionalContext
```

It must print the message with `WK-208`. Repeat the last command from a worktree: the handoff path must be the main checkout's. With `"session_id":"../x"` or outside git, it must print `{}`.

The message texts are in English, like the status lines: the agent reads them just as well and you don't depend on each session's language.

### The instructions that go with it

- A short, always-loaded rule that says where the handoff is, which files it has, when to write it, the status lines and the `blocked` categories. Detail goes into a reference document, so you don't spend context in every session.
- The table of compaction thresholds per agent ([ch. 02](02-compactar-antes.md)).
- The worktrees rule: outside the repo and, on close, delete the handoff ([ch. 11](11-uso-diario.md)).
- If an agent reads rules with frontmatter (Antigravity), each rule with its `trigger`.

### Applying it to another repo

1. Copy the script, its modules (texts, pauses, log) and its tests. Adjust how a branch's plan is recognized.
2. Make sure `tmp/` is in `.gitignore`.
3. Configure each agent ([ch. 05](05-configurar-cada-agente.md)).
4. Write the rule and its reference.
5. Test with the marker ([ch. 10](10-probar-el-handoff.md)) and open sessions from the main checkout.

### In my case

When I cross-checked the system after implementing it, the new version of the script was not active even though it was already merged into the integration branch. Claude Code runs `$CLAUDE_PROJECT_DIR/agent-hooks/...`, and `$CLAUDE_PROJECT_DIR` is the **main** checkout, which was behind. A change to the script only reaches the agents after the main checkout is updated.

`hooks` `python` `script` `implementation`
