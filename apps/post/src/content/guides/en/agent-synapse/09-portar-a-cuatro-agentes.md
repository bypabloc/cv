**09**

# Case study: porting to four agents

[← Index](README.md)

---

### The starting point

Up to 1.6.1, Synapse was a Claude Code plugin: four scripts that read Claude Code's JSON on stdin and answered with its protocol (exit 2 to block, `permissionDecision` to ask). When work moved to Codex, Antigravity or OpenCode, there was no control at all.

### The risk of installing it unadapted

The most dangerous part wasn't missing coverage but **false** coverage: several agents read Claude Code manifests, load the hooks and run them with a different protocol.

| Agent | What happened with unadapted Claude Code hooks | Severity |
| :-- | :-- | :-- |
| Antigravity | Every `exit 2` is ignored and stdin uses other names: the scripts didn't find the tool and ended with `exit 0`. **Everything passed** | Critical |
| Codex | Blocks worked, but an `ask` or `allow` left the hook as failed and the tool ran. `apply_patch` patches arrived with empty fields | High |
| OpenCode | Doesn't load Claude Code hooks: no protection | No coverage |

### The architecture: neutral core + adapters

The decision logic (shell tokenizing, git scope, secret signatures, Laya, the trace) wasn't coupled to Claude Code. Only the input, the output and a few paths were. The port focused there:

```text
host stdin ──▶ hosts.normalize() ──▶ HookEvent (kind: shell | read | write | edit,
                                               command, files, cwd, project, session)
               each hook's current logic (unchanged) ──▶ Decision
               hosts.emit() ──▶ each host's exact contract
```

| Host | Shell tool | Write tool |
| :-- | :-- | :-- |
| Claude Code | `Bash` | `Write`, `Edit` |
| Codex | `Bash` | `apply_patch` (one patch, several files) |
| Antigravity | `run_command` | `write_to_file`, `replace_file_content` |
| OpenCode | `shell` | `write`, `edit`, `patch` |

Three principles guided the design:

1. **The host is declared** in each manifest (`--host codex`), never guessed from the payload's shape.
2. **No host fails open because of format.** In Antigravity, an internal error emits `force_ask`, because there a non-zero exit equals allowing.
3. **Degrade toward safety:** where a hook can't ask (Codex), the `ask` is emitted as a `deny` with an approval id.

Codex needed an `apply_patch` parser (`patch.py`): a patch can add, update, move and delete several files, and each one is evaluated separately. A protected file rejects the whole patch, naming the cause.

### No regressions in Claude Code

Before refactoring, I recorded a **golden**: 1.6.1's exact output for every test case. 1.7.0 had to reproduce it byte for byte: 162 identical cases, plus 17 new ones. Each host's fixtures are real payloads captured with a probe (Codex 0.171.0, agy 1.5.13, OpenCode 2.3.2), and the suite reached 1394 tests.

### What couldn't be matched

- **Codex** can't ask from a hook ([ch. 10](10-codex-y-windows.md)).
- **Codex** has no read tool: the `.env` block only covers shell commands.
- **Native Windows**: PowerShell analysis is partial and Laya doesn't run.

### In my case

The decision that paid off most was the golden. During the refactor I changed the input and output of all four hooks, and whenever something shifted, the golden said so immediately. The same pattern (a pure core and one wiring per host) is what I later used to port session-handoff.

`multi-agent` `architecture` `case-study`
