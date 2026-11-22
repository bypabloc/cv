**05**

# When it saves

[← Index](README.md)

---

### The rule

> **How many tool calls Claude makes, and whether their result can be reduced, matters more than how many files there are.**

### The tasks where it pays off

| Task | Why it saves |
| :-- | :-- |
| Many calls to an MCP server (querying records, issues, rows) and returning a total | A shell script can't call MCP tools; with Code Mode, the responses are processed inside the block and only the result reaches the model |
| Reading many responses and classifying them | Same reason, with more care: the filter can leave data out ([ch. 06](06-cuando-no.md)) |
| Research with several web searches | Pages are summarized inside the script |
| Implementing something and running the tests | Editing, building and testing in one block saves round trips |
| Several independent commands (build, typecheck, lint) | They run at once and a summary comes back |
| Long commands | They can run in the background while Claude moves on |

### What they have in common

- **Many related calls** that would be many turns in normal mode.
- **A small result** at the end: a count, a total, a yes or no, the last lines of a log.
- **Tools the shell can't reach** (MCP, web) or steps that depend on the previous one.

### How to help it

- Explicitly ask for a summary: "tell me how many fail and which ones, not the full output".
- Ask for counts per step and the list of what failed, so a filter doesn't hide errors.
- On big MCP tasks, ask it to work in batches and return partial totals.

### In my case

In my comparisons, the tasks where the saving was clear had this shape: several consecutive queries to an MCP server ending in a number or a short list, and "edit, build, test" loops where Claude used to make one trip per step. It matches what the published tests in [ch. 08](08-lo-que-midieron-otros.md) show.

`when-to-use` `mcp` `savings`
