**03**

# What a code block looks like

[← Index](README.md)

---

### The pieces Claude uses

Inside a block, Claude has a set of functions to reach the tools **[doc]**:

| Piece | What for |
| :-- | :-- |
| `` $`command` `` | Runs a shell command; `.text()`, `.lines()` or `.json()` read the output, `.nothrow()` doesn't throw on a non-zero exit |
| `file(path).text()` | Reads a file |
| `edit(path, old, new)` / `write(path, text)` | Edits or writes, with the diff visible in the conversation |
| `Promise.all([...])` | Runs several calls at once |
| MCP tools | Called as functions; their responses are processed inside the script |

### What goes back to the model

Only the block's last expression (or whatever is logged explicitly). A typical pattern:

```js
const [log, tests] = await Promise.all([
  $`git log --oneline -20`.text(),
  $`pnpm test`.nothrow(),
])
;({ commits: log.trim().split('\n').length, testsOk: tests.exitCode === 0, tail: tests.stdout.slice(-2000) })
```

The model gets a count, a boolean and the last lines of the tests, not the full log or all the output.

### Background blocks

A slow block can keep running while Claude does something else or answers you; `Poll` collects the result when it ends. The limits **[doc]**:

- If Claude waits for the block, it's cut at **10 minutes**.
- In the background it can run up to **2 hours**, but only if the session **started** in auto mode or `bypassPermissions`.
- `Esc` stops a running block; background ones are listed and stopped in `/tasks`.

### The result gets cut

What a block returns is trimmed to about 30 thousand characters (the start and the end), and the middle isn't saved anywhere. The trick is to keep the result in a variable and ask only for pieces, or trim before returning.

### In my case

In my sessions, a typical block runs one or two commands and returns an object with the essentials; only one in ten uses `Promise.all` to parallelize ([ch. 07](07-mis-mediciones.md)). Long blocks are the exception: only one in ten goes past 27 lines.

`code-mode` `javascript` `anatomy`
