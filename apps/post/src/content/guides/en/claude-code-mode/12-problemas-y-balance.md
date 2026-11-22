**12**

# Problems, myths and verdict

[← Index](README.md)

---

### Problems and solutions

| Problem | Cause | Solution |
| :-- | :-- | :-- |
| `Code Mode (experimental) isn't available` | Unsupported provider, auth, model or plugin | Read the reason in `/status` |
| It won't start when launched from another session | It inherits the `CLAUDE_*` variables | Clean terminal |
| I can't resume a session without the mode | A session started with the mode only resumes with it | New session |
| The task took longer than in normal mode | The script did one read per file | Ask for "a single shell command" or use normal mode |
| The answer says it read everything, but data is missing | A script filter dropped records | Ask for counts per step and what was dropped |
| The middle of a result is missing | Cut at ~30 thousand characters | Return summaries or pieces |
| My hooks got slow | They fire on every internal call | Light hooks, a proper `timeout` |
| A guard didn't block after a hook error | Since 2.1.329 the call runs by default | `"onFailure": "block"` |
| It doesn't run in my automation | `claude -p` doesn't support it | Use it in interactive sessions |

### Claims that circulate

| Claim | Reality |
| :-- | :-- |
| "It saves 37 % of tokens" | That's a 2025 API figure, not Code Mode |
| "It's always faster" | On local files it's often the same or slower |
| "Code Mode fails closed if a hook fails" | True until 2.1.328; since 2.1.329 you have to ask for it with `onFailure` |
| "The auto mode classifier protects me the same" | It reviews the script, not the values it computes at run time |
| "With Code Mode my quota lasts longer" | Nobody has measured it yet |
| "It uses it for everything" | The model decides; a simple question is still one read |

### My verdict

| Kind of work | I use it |
| :-- | :-- |
| Research and queries with many MCP calls | **Yes** |
| Implementing something with edit, build and test loops | **Yes** |
| Several independent checks and long commands | **Yes** |
| Audits or mechanical changes across many local files | No: a shell script is faster |
| Automations with `claude -p` | Not possible |

### What I didn't measure

- The real effect on my subscription's 5-hour and weekly quota.
- Sonnet 5.5 and Fable 5.2: my sessions were with Opus 5.5 and Haiku 5.5.
- The quality of the resulting code beyond the tests passing.

### Risks worth keeping in mind

- **It's experimental:** it changes every few days and may disappear.
- **Filters can lie by omission:** always ask for counts.
- **The classifier is partly blind:** critical operations need your own rules or hooks.
- **A percentage without its task is useless:** measure in your project.

`troubleshooting` `myths` `verdict` `code-mode`
