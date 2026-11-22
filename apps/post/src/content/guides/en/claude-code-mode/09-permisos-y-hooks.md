**09**

# Permissions, hooks and security

[← Index](README.md)

---

### Every internal call goes through your rules

Inside a block, every tool call goes through the `deny` and `ask` rules and the `PreToolUse` hooks **under its normal name** (`Bash`, `Read`, `mcp__server__tool`) **[doc]**. A guardrail you already had keeps working: no need to rewrite it for Code Mode.

Two practical consequences:

- **More hook invocations.** A block that reads 500 files fires your read hooks 500 times. Slow hooks show, and under load they can time out.
- **Compound commands.** A `git push` inside a folder can reach the hook as `cd 'app' && git push`: the hook must check each part.

### Auto mode: the classifier reviews the script, not the values

In auto mode, the classifier reviews **each block before it runs**, not each call. It doesn't see values computed during execution, such as a path taken from a search **[doc]**. For critical operations, keep `ask` rules or your own hooks: those do see each call with its real arguments.

### The sandbox only covers the shell

The shell sandbox applies to the commands the script launches. The JavaScript and its file, web and MCP calls run **outside the sandbox**. To isolate everything, the docs recommend a container or a VM **[doc]**.

### What happens if a hook fails

Since 2.1.329, if a `PreToolUse` hook fails (not by timeout or by decision), **the call runs by default**. For a guard to fail closed you have to declare `"onFailure": "block"` in `command` or `http` hooks **[doc]**. Before 2.1.329 it was the other way around, so guides written in the first days say Code Mode "fails closed": that's outdated.

### Reviewing or approving scripts

| You want to | How |
| :-- | :-- |
| Approve each script before it runs | `"permissions": { "ask": ["REPL"] }` (the prompt doesn't show the code: open it with `Ctrl+O`) |
| Review the code with a hook | `PreToolUse` with matcher `REPL`, reading `tool_input.code` |
| Redact what goes back to the model | `PostToolUse` with matcher `REPL`, returning `updatedToolOutput` |
| Confirm critical commands | `ask` rules like `Bash(git push *)` |

### In my case

I use [Synapse](https://post.the-full-stack.com/en/agent-synapse/), my guardrails as `PreToolUse` hooks, and it worked unchanged: while writing this guide, a Code Mode block tried to run `git` on a repo outside the project and Synapse blocked it with its usual rule, even though the call came from inside a script. Same with session-handoff: its notices after each write arrived just the same from inside the blocks. What I did check was that my guard hooks declared `onFailure: "block"`.

`security` `hooks` `permissions` `auto-mode`
