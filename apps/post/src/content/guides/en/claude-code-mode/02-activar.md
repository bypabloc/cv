**02**

# Turning it on and checking it's on

[← Index](README.md)

---

### Requirements

| Requirement | Detail **[doc]** |
| :-- | :-- |
| Version | Claude Code 2.1.323 or later (better the latest: there were many fixes) |
| Install | Native |
| Account | A Claude subscription or a Console account. It doesn't work with Bedrock, Vertex, Foundry, a gateway or a custom `ANTHROPIC_BASE_URL` |
| Organization | No HIPAA or zero data retention |
| Model | Opus 5.5, Sonnet 5.5, Haiku 5.5 or Fable 5.2 |
| Where | Only the **interactive** `claude` session in the terminal. Not `claude -p`, the Agent SDK, the VS Code panel, Desktop or cloud sessions |
| Windows | Git for Windows (the scripts' shell commands run in Git Bash) |

### Turning it on for one session

```bash
CLAUDE_CODE_EXPERIMENTAL_CODE_MODE=1 claude
```

In PowerShell:

```powershell
$env:CLAUDE_CODE_EXPERIMENTAL_CODE_MODE = "1"
claude
```

The first time, a confirmation dialog appears; accepting it restarts the session with the mode on. On start, the session shows `Code Mode (experimental) is on · this session can be resumed only with Code Mode on`.

### Keeping it on

In the `env` block of `~/.claude/settings.json`:

```json
{ "env": { "CLAUDE_CODE_EXPERIMENTAL_CODE_MODE": "1" } }
```

The value **is ignored in a project's settings**: a cloned repo can't turn it on by itself. To turn it off, remove the variable or set it to `0`; a `0` anywhere wins over a `1`. An organization can block it with `0` in managed settings, but can't force it on **[doc]**.

### Checking it's active

| Where | What to look for |
| :-- | :-- |
| `/status` | `Code Mode: on (experimental)` and its source, or the reason it isn't available |
| `/context` | "System tools" drop from about 25k to about 11k tokens |
| `Ctrl+O` | The transcript: each script shows up as a **Code** row you can expand to read the JavaScript |
| The conversation | A block summary ("Read 8 files, ran 16 shell commands") and the diffs |

### When it says "isn't available"

`/status` shows the reason. The most common: unsupported provider or gateway, authentication through `apiKeyHelper` or `ANTHROPIC_AUTH_TOKEN`, unsupported model, `--remote-control`, OpenTelemetry tracing, an incompatible plugin or mod, `REPL` missing from `--tools` or in `deny`, and an unwritable `~/.claude.json` **[doc]**. It also fails if you launch `claude` from inside another Claude Code session (it inherits its variables): use a clean terminal.

### In my case

I didn't leave it on permanently: I turn it on per session with a function in my `.zshrc`, `claude-cm() { CLAUDE_CODE_EXPERIMENTAL_CODE_MODE=1 command claude "$@"; }`. That way `claude` stays in normal mode and `claude-cm` opens a session with Code Mode, which is exactly what I need to compare. A session started with the mode can only be resumed with the mode on: to compare, I open new sessions instead of using `--resume`.

`activation` `requirements` `status`
