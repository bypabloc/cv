**03**

# What it blocks, asks about and lets through

[← Index](README.md)

---

### The four decisions

| Decision | Meaning | Example |
| :-- | :-- | :-- |
| `allow` | Runs without asking | Deleting something in `./tmp/` or `dist/` |
| `ask` | The user is asked to confirm | A `git reset --hard` |
| `block` | Doesn't run; the agent gets the reason | `rm -rf /`, a `cat .env` |
| `pass` | Synapse has no opinion; the agent's normal permissions apply | Reads, `git status`, `pnpm test` |

`pass` is the most frequent decision and the one that matters most: routine work shouldn't cost a millisecond of attention.

### The four hooks

All run on `PreToolUse`, before the tool runs:

| Hook | Tools | What it decides |
| :-- | :-- | :-- |
| `block_dangerous` | Bash (and each agent's shell) | Destructive commands, writes outside the project, exfiltration, writing files from Bash |
| `block_env_read` | Read, Bash | Reading `.env` files |
| `detect_secrets` | Edit, Write | Credentials in the content about to be written |
| `protect_files` | Edit, Write | `.git/`, `.venv/`, lockfiles and agent configuration |

### block_dangerous in detail

| Decision | Cases |
| :-- | :-- |
| **block** | `rm -rf /` or `~`, fork bombs, writing to `/dev/sd*`, `chmod 777 /`, `curl … \| sh`, reverse shells, `kill -1`, credential exfiltration, writes outside the project (with resolved variables: `p=/home/x; rm -rf "$p"`), writing files from Bash (`echo >`, `cat <<EOF >`, `sed -i`) |
| **ask** | Force push, `reset --hard`, `DROP DATABASE`, `filter-branch`, modifying `.git/`, output sent to the system `/tmp`, deleting tracked code with changes, privileged docker, launching another agent non-interactively (`codex exec`, `claude -p`) |
| **allow** | Operations in `./tmp/`, the agent's scratchpad and build artifacts (`dist/`, `build/`, `.turbo/`, `target/`, `.cache/`, `node_modules/`); deleting tracked, clean content ([ch. 04](04-alcance-del-proyecto.md)) |
| **pass** | Reads, routine `git`/`gh`, `bun\|npm\|pnpm run\|test`, `uv run <tool>`, `python -m pytest`, the project's versioned scripts and the prefixes you declare ([ch. 06](06-configurar-por-proyecto.md)) |

### Why writing from Bash is blocked

The `detect_secrets` and `protect_files` hooks check Edit and Write. If the agent writes a file with `cat <<EOF > config.ts`, those checks don't see it. So Synapse blocks writing files from Bash and asks the agent to use the edit tool. Tool output (`pytest > log`, `cmd | tee log`) and heredoc commit messages are still allowed.

### protect_files

- **block:** hand-editing `.git/`, `.venv/` or lockfiles (`package-lock.json`, `pnpm-lock.yaml`, `bun.lock`, `uv.lock`, `poetry.lock`, `Cargo.lock`).
- **ask:** agent configuration (`.claude/settings.json`, `.codex/config.toml`, hooks) and Synapse's own.
- **pass:** Markdown instructions (`AGENTS.md`, `CLAUDE.md`, `.agents/rules/*.md`): they aren't permissions, and protecting them creates waits without adding security ([ch. 10](10-codex-y-windows.md)).

### What the agent sees

A block names the hook, the engine and the rule, and explains why:

```text
🚫 BLOCKED · Synapse · block_dangerous (python) · regla structure.outside_project
Prohibido modificar rutas fuera del proyecto (~/code/my-app): 'rm' sobre ~/other.
```

With that text the agent almost always fixes things on its own: it changes the path, uses the edit tool, or notes that it needs your approval and moves on with the rest.

### In my case

The rule that changed my daily work most was the one about writing from Bash. Before it, the agent unknowingly got around the secret checks with heredocs; afterwards, every file goes through the edit tool and gets checked. The cost was a batch of false positives at first (an `rg "a|b"` that looked like a pipe, a `sed` with a quoted `;`), fixed by making tokenization respect quotes.

`decisions` `block_dangerous` `protect_files`
