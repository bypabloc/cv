**12**

# Problems, myths and what was measured

[← Index](README.md)

---

### Problems and solutions

| Problem | Cause | Solution |
| :-- | :-- | :-- |
| Codex waits after a `deny` | An `ask` in Codex is a `deny` with an id | `synapse.py approve <id>` in your terminal; if it's routine, declare it in `routine_commands` |
| Codex stopped applying the hooks after updating | Trust is tied to the scripts' hash | Re-approve in `/hooks` and restart sessions |
| `PreToolUse:… hook failed` on Windows | `python3` resolves to the Store shortcut | Synapse ≥ 1.7.2 (uses `run-hook.cmd`) or `SYNAPSE_PYTHON` |
| Garbled messages on Windows | Output in cp1252 | Synapse ≥ 1.7.1; in your own scripts, `PYTHONUTF8=1` |
| A command from your CLI always asks | It isn't routine yet | Add the prefix to `.synapse/commands.json` |
| The agent can't read a `.env` | That's expected | Use the obfuscated schema or extract the variable in the same command that uses it |
| A worktree shows up "outside the project" | Version before 1.2.0 | Update: the root is computed from git |
| Laya doesn't start | Missing LFS delta, PyTorch or GPU; or native Windows | `synapse.py doctor`; without Laya, Synapse continues with rules |
| A hook fails silently in Codex | A hand-declared hook points to a deleted clone | Remove it from the user config; install the plugin from the marketplace |

### Claims that turned out false

| Claim | Reality |
| :-- | :-- |
| "A neural classifier is safer than some regexes" | In the real trace, rules stopped everything dangerous; Laya's 24 `ask`s were false positives |
| "If the agent keeps going, the hooks work" | A failing hook doesn't block: on Windows, Synapse checked nothing and the session looked normal |
| "Installing the Claude Code plugin on another agent protects it the same way" | In Antigravity, unadapted, everything passed; in Codex, every `ask` let the tool run |
| "Protecting `AGENTS.md` and Markdown rules adds security" | They're instructions, not permissions; protecting them only creates waits (in Codex, hours) |
| "A model retrained on more data always improves" | The delta retrained on the trace lost recall (0.772 → 0.757) and wasn't published |

### What was measured

| Measurement | Result |
| :-- | :-- |
| Cost per command, rules only | ~8 ms (the block in the ch. 07 example: 7.6 ms) |
| Cost per command with Laya (real trace) | ~205 ms |
| Laya latency, in-process vs daemon | ~6 s vs ~70 ms |
| Tuned Laya | 0.15–0.29 % FPR, 78–81 % recall |
| Multi-agent port | 162 identical golden cases, 1394 tests |

### What it doesn't do

- **It isn't a sandbox.** It checks what the agent asks to do; it doesn't isolate processes or the network. Add it to the native sandboxes ([ch. 06](06-configurar-por-proyecto.md)).
- **It doesn't see everything a command runs.** A versioned project script is treated as routine: what it does inside is on you.
- **It doesn't replace code review.** A change with no secrets isn't necessarily correct.
- **It doesn't cover agents without pre-tool hooks.**

### Risks worth keeping in mind

- Every per-project exception (routines, allowed passwords) widens what passes unchecked: keep them short and versioned.
- A guardrail with many false positives ends up turned off. One justified `ask` beats ten routine ones.
- Agent hook APIs change fast: pin minimum versions and recapture their payloads when you update.

`troubleshooting` `measurements` `myths` `security`
