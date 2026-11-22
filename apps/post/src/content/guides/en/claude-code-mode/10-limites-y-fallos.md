**10**

# Known limits and bugs

[← Index](README.md)

---

### What isn't available

- `claude -p`, the Agent SDK, the VS Code panel, Desktop, cloud sessions, Remote Control, Claude in Chrome and computer use **[doc]**.
- Moving the session to Desktop or turning it into a background session.
- A session started with Code Mode **can only be resumed in the terminal and with the mode on**.
- There's no official way to choose the mode per skill, subagent or call (it's an open request).

### Subagents

Whether a subagent uses Code Mode depends on its tool list: all tools include it; a fixed list doesn't, unless it includes `REPL`; `disallowedTools: REPL` turns it off. It isn't officially documented. A subagent's code isn't visible with `Ctrl+O` from the main session **[doc]**.

### Bugs already fixed

In eight days there were seven releases with dozens of fixes to the mode **[doc]**:

| Version | Fix |
| :-- | :-- |
| 2.1.325 | Scripts that ignored the active worktree |
| 2.1.326 | Support with agent teams (in-process) |
| 2.1.328 | A 0.75 s pause after each script; variables left `undefined` after a failed script; `write()`/`edit()` offered to read-only subagents; on Windows, the shell is Git Bash |
| 2.1.329 | A failing `PreToolUse` hook no longer rejects the call; a limit against loops that filled memory |
| 2.1.330 | Long pause after reading hundreds of files with path-scoped rules; `/context` undercounting tools |

### Bugs open as of November 22

- The result is cut at about 30 thousand characters and the middle is lost.
- Steps chained after a background command that never run.
- On WSL2, file tasks with hundreds of individual reads, slower than normal mode.
- Read-only subagents that, according to their reporter, still get `write()`/`edit()`.

### In my case

What affected me most was resuming: several times I wanted to go back to a session without the mode to compare, and you can't. My rule became: a new session for each comparison, and `claude update` before measuring, because an old version measures a different mode.

`limits` `bugs` `changelog`
