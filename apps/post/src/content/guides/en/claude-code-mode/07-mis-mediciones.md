**07**

# My measurements

[← Index](README.md)

---

### Where they come from

Claude Code keeps every session in a JSONL transcript with the messages, each request's token usage and, in Code Mode, the code of every block. I measured the transcripts of my latest sessions with the mode on and compared them with my normal Opus 5.5 sessions over the same period (November 12–22, 2026).

| Sample | Value **[measured]** |
| :-- | :-- |
| Sessions with Code Mode | 10 (klinikae 5, content-studio 2, portfolio 1, plugins monorepo 1, other 1) |
| Models | Opus 5.5 in 8, Haiku 5.5 in 2 |
| Version | 2.1.330 |
| Code blocks | 873 |
| Normal reference sessions (Opus 5.5) | 43 |

### How Claude writes the blocks

| Metric | Value **[measured]** |
| :-- | :-- |
| Lines per block (median) | 5 |
| Lines per block (90th percentile) | 27 |
| Shell commands per block (average) | 1.5 |
| Blocks with 3 or more shell commands | 17 % |
| Blocks with no shell command (files or MCP only) | 19 % |
| Blocks that parallelize with `Promise.all` | 11 % |

Claude doesn't write long programs: it groups two or three steps and returns the essentials. Explicit parallelization is the exception, not the rule.

### Per request, against my normal sessions

| Per request (Opus 5.5) | Without Code Mode (43 sessions) | With Code Mode (8 sessions) |
| :-- | --: | --: |
| Context read from cache | ~283 thousand tokens | ~68 thousand tokens |
| Context written to cache | ~3.3 thousand tokens | ~0.9 thousand tokens |
| Output tokens | ~830 | ~220 |
| Estimated cost (API prices) | ~US$0.114 | ~US$0.024 |
| API time | ~11.5 s | ~2.4 s |

**How to read this table.** It isn't an A/B: the tasks differ. Code Mode sessions have many short `Poll` requests that lower the average, and normal sessions include very long autonomous runs with huge contexts. The table shows the pattern (each Code Mode request carries much less context), not a savings percentage.

### My per-task comparisons

Besides the transcripts, I repeated tasks from my projects with the mode on and off. The results were very close to the published tests in [chapter 08](08-lo-que-midieron-otros.md):

- **With many calls and a small result** (repeated MCP queries, edit-and-test loops), the saving was clear in tokens and cost.
- **On local file work** that a shell script already handled, the saving was small or nil, and some runs took longer.
- **On a question about one file**, only the fixed tool saving showed.

### In my case

The number that helped me most wasn't a percentage but the shape of the blocks: if a task of mine ends in one- or two-line blocks that only read files, I gain nothing; if it ends in a block that calls several tools and returns a small object, I do. Chapter 11 has the script I used to count all this, so you can run it on your transcripts.

`measurements` `transcripts` `real-data`
