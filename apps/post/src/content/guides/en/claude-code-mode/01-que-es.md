**01**

# What Code Mode is and what changes

[← Index](README.md)

---

### Normal mode: one trip per tool

Without Code Mode, Claude asks for a tool, waits for the result, reads it and only then decides the next one: read a file, run a command, read the output, edit, run again. Each step is a trip to the model, and each full result stays in the context window for the rest of the session.

### With Code Mode: a script that chains tools

With the mode on, Claude writes a JavaScript block that makes the calls for it, and Claude Code runs it inside the session **[doc]**:

```js
const hits = await $`rg -l "maxAttempts: 3" src`.text()
for (const f of hits.trim().split('\n')) await edit(f, 'maxAttempts: 3', 'maxAttempts: 5')
const t = await $`npm test`.nothrow()
;({ edited: hits.trim().split('\n').length, tests: t.exitCode })
```

A single block searches, edits several files and runs the tests. **The last expression is the only thing that goes back to the model**: in the example, two numbers, not the file list or the test output.

### What the model sees

Instead of a dozen tools, the model gets two **[doc]**:

| Tool | What for |
| :-- | :-- |
| `REPL` | Runs a JavaScript block with access to the shell, files, the web and MCP servers |
| `Poll` | Collects the result of a block still running in the background |

Inside the block, the usual tools (Bash, Read, Edit, MCP) still exist: they're called from the code and go through your permissions and hooks under their normal names ([ch. 09](09-permisos-y-hooks.md)).

### What it promises and what it doesn't

The documentation gives no savings figures. It says to try it in three cases: a change repeated across many files, a search whose results need filtering before being read, and several independent commands that can run at once **[doc]**. It's experimental, off by default, and may change or disappear in any release.

An important detail: **the model decides** when to write a script. With the mode on, a simple question is still answered with a single read.

### In my case

What surprised me most at first was how short the blocks were. I expected long scripts that did everything; in my sessions, half the blocks are 5 lines or fewer ([ch. 07](07-mis-mediciones.md)). Claude uses the script to group two or three steps and return only what's needed, not to write a program.

`code-mode` `claude-code` `concepts`
