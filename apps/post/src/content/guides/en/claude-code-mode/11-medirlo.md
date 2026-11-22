**11**

# How to measure it in your project

[← Index](README.md)

---

### An honest A/B

1. **Pick 3 or 4 real tasks** from your project with different shapes: one with many MCP calls, one multi-file edit, one "implement and test" and one simple question.
2. **New sessions** for each run, with the same model, effort, permissions and MCP servers.
3. **The same prompt**, copied verbatim.
4. **At least 2 or 3 runs per mode:** variation between identical runs is large.
5. **Record:** time, `/cost` at the end, `/context` at the start and end, and whether the result passes the same check (tests, an expected count).
6. **Compare per task**, not a global average.

| Command | What it tells you |
| :-- | :-- |
| `/status` | That the mode is really on |
| `/context` | How much the tools weigh and how much the context grew with the task |
| `/cost` | Estimated cost at API prices (with a subscription, it isn't the bill) |
| `/usage` | How much of the 5-hour and weekly quota you used (careful: lots of noise if other sessions run at the same time) |
| `Ctrl+O` | What Claude wrote in each block |

### Measuring what you already did: the transcripts

Transcripts live in `~/.claude/projects/<project>/<session>.jsonl` (or under your `CLAUDE_CONFIG_DIR`). Each line is a JSON event; Code Mode blocks are `tool_use` entries named `REPL` with the code in `input.code`. This script counts the blocks and their shape:

```python
import glob, json, re, statistics, sys

seen, lines, shell = set(), [], []
for path in glob.glob(sys.argv[1] + '/**/*.jsonl', recursive=True):
    for raw in open(path, encoding='utf-8', errors='ignore'):
        if '"name":"REPL"' not in raw:
            continue
        event = json.loads(raw)
        for block in (event.get('message') or {}).get('content') or []:
            if block.get('type') != 'tool_use' or block.get('name') != 'REPL':
                continue
            if block['id'] in seen:
                continue
            seen.add(block['id'])
            code = block['input'].get('code', '')
            lines.append(code.count('\n') + 1)
            shell.append(len(re.findall(r'\$`', code)))

print(f'blocks: {len(lines)}')
print(f'lines (median): {statistics.median(lines)}')
print(f'shell commands per block: {sum(shell) / len(shell):.2f}')
```

```bash
python3 count_blocks.py ~/.claude/projects
```

For token usage, each `assistant` message carries `message.usage` (`input_tokens`, `cache_read_input_tokens`, `cache_creation_input_tokens`, `output_tokens`); group them by `message.id` so you don't count the same request twice.

### Common measuring mistakes

- Comparing a resumed session with a new one: the starting context isn't the same.
- Measuring on different versions.
- Launching `claude` from inside another session: it inherits variables and the mode may not start.
- Counting only tokens without looking at time or whether the result is correct.

### In my case

I ran the comparisons this way, with tasks from klinikae and content-studio, and counted my transcripts with an extended version of this script. The most useful thing was sorting tasks by shape before measuring: after that, the result became predictable.

`measurement` `benchmark` `transcripts`
