**09**

# The plugin recipe, step by step

[← Index](README.md)

---

### Shortcut: the published plugin

If you only use Claude Code and don't want to build it by hand, install the plugin that came out of this recipe: [bypabloc/claude-plugin-session-handoff](https://github.com/bypabloc/claude-plugin-session-handoff) (MIT).

```bash
claude plugin marketplace add bypabloc/claude-plugins
claude plugin install session-handoff@bypabloc
claude plugin list   # check
```

It requires Claude Code 2.1.287 or later and needs no Python or Node. Besides the summary-free compaction in this chapter, it brings the rest of the guide's system: it re-injects the handoff on start, resume and compaction ([ch. 03](03-handoff-en-disco.md)), won't let the turn end while a `Next step` remains, rejects `AskUserQuestion` without a valid `blocked`, and shows phase, ETA and `ctx %` in a band above the prompt. The `blocked` categories, the specs folder and the closing text are configured in `.claude/session-handoff.json`. Details are in its README.

The rest of the chapter builds the compaction piece from scratch, to understand or adapt it.

### Requirements

- Claude Code **2.1.287 or later** (module plugins in TypeScript, early access).
- A handoff with a per-session link ([ch. 03](03-handoff-en-disco.md)): `<repo>/tmp/handoff/.sessions/<session_id>` holds the task name and `<repo>/tmp/handoff/<work>/PROGRESS.md` exists.
- `git` on the `PATH`.

It doesn't need a script of its own: step 4 detects the linked task from the plugin. The engine types (`claude-code`) ship with Claude Code; if a signature in this recipe doesn't match your version, `claude plugin validate` will say so. The installed type wins, not this text.

### 1. Files

```text
<plugins-folder>/                          # e.g. .claude/plugins-local/
├── .claude-plugin/marketplace.json        # declares the local marketplace
└── handoff-compact/
    ├── .claude-plugin/plugin.json         # manifest
    └── hooks/
        ├── hooks.json                     # which modules to load
        ├── register.ts                    # the hooks
        ├── tail.ts                        # picks the tail (pure, no I/O)
        └── tail.test.ts                   # tail tests
```

`.claude-plugin/marketplace.json`:

```json
{
  "name": "<marketplace>",
  "owner": { "name": "<your name>" },
  "plugins": [{ "name": "handoff-compact", "source": "./handoff-compact" }]
}
```

`handoff-compact/.claude-plugin/plugin.json`:

```json
{
  "name": "handoff-compact",
  "version": "0.1.0",
  "description": "Compacts without a model summary when the session has an on-disk handoff"
}
```

`handoff-compact/hooks/hooks.json`:

```json
{ "modules": ["./register.ts"] }
```

### 2. What you use from the API

| Piece | Use |
| :-- | :-- |
| `import type { Register, EngineInterface, SessionMessage } from 'claude-code'` | Types of the module, the hook context and a message |
| `export const register: Register = on => { … }` | Entry point: registers hooks with `on` |
| `on('session.compact', async ($, e, next) => …)` | Before every compaction |
| `e.trigger` | Origin; `'precompute'` is the early summary |
| `e.agentId` | Defined if a subagent compacts |
| `e.messages` | The conversation as `SessionMessage[]` |
| `return { messages }` | Replaces the conversation; the summarizer doesn't run |
| `$.session.id()`, `$.session.cwd()` | The session's id and directory (async) |
| `$.process.run(argv, { cwd, stdin?, timeoutMs? })` | Runs a process; returns `{ exitCode, stdout, … }` |
| `$.ui.toast(text)` | Short notice in the UI |

A `SessionMessage` has `role` (`'user'` or `'assistant'`), `text`, `toolUses`, `toolResults?` and `handle?`. **With `handle`**, the message comes back as is (with `thinking` and attachments); **without `handle`**, the engine rebuilds it from `role`, `text` and the tool blocks. A message you build yourself: `{ role, text, toolUses: [] }`.

### 3. The tail: `hooks/tail.ts`

Pure, no I/O, so it can be tested with `claude plugin test`.

```ts
import type { SessionMessage } from 'claude-code'

/** Budget weight of a message that comes back whole (its thinking and attachments travel unmeasured). */
export const WHOLE_WEIGHT = 3
/** Minimum messages in a weighted cut before trying unweighted. */
export const MIN_KEPT = 12

/** Approximate size in characters: text, each call's arguments and each result's text, once each. */
export const sizeOf = (m: SessionMessage): number =>
  m.text.length +
  m.toolUses.reduce((n, use) => n + JSON.stringify(use.input).length, 0) +
  (m.toolResults ?? []).reduce((n, r) => n + r.text.length, 0)

/**
 * Safe place to open the tail: any assistant message (its results come after) or a user message with
 * text and no results. Opening on a message with results would leave results without their call.
 */
const opensTurn = (m: SessionMessage): boolean =>
  m.role === 'assistant' || (m.text.trim() !== '' && (m.toolResults?.length ?? 0) === 0)

/**
 * The most recent stretch that fits in `budget` characters and opens at a safe place. Messages that will
 * come back whole weigh `weight`: the current turn (since the user's last request) and the `whole` newest.
 * Null if not even the newest stretch fits: then it compacts with the summary.
 */
export function keepTail(messages: readonly SessionMessage[], budget: number, whole: number, weight = WHOLE_WEIGHT): SessionMessage[] | null {
  let size = 0
  let start = -1
  let pastPrompt = false
  for (let i = messages.length - 1; i >= 0; i--) {
    const m = messages[i]!
    const isWhole = !pastPrompt || i >= messages.length - whole
    size += sizeOf(m) * (isWhole ? weight : 1)
    if (m.role === 'user' && opensTurn(m)) pastPrompt = true
    if (size > budget) break
    if (opensTurn(m)) start = i
  }
  const kept = start < 0 ? null : messages.slice(start)
  // A large batch of parallel tools, or a cut that leaves almost nothing: try unweighted.
  if (weight > 1 && (kept?.length ?? 0) < MIN_KEPT) {
    const plain = keepTail(messages, budget, whole, 1)
    if ((plain?.length ?? 0) > (kept?.length ?? 0)) return plain
  }
  return kept
}

/**
 * Returns everything except the current turn and the `whole` newest without `handle`: the engine rebuilds
 * them without thinking or nested rules (~90 % of a real tail). The current turn stays whole: the API
 * requires its thinking intact.
 */
export function slim(tail: readonly SessionMessage[], whole: number): SessionMessage[] {
  let turn = -1
  for (let i = tail.length - 1; i >= 0; i--) if (tail[i]!.role === 'user' && opensTurn(tail[i]!)) { turn = i; break }
  const from = Math.max(0, Math.min(turn, tail.length - whole))
  return tail.map((m, i) => {
    if (i >= from) return m
    const { handle: _drop, ...rebuilt } = m
    return rebuilt
  })
}
```

Starting values: `budget = 80_000` characters (~20k tokens) and `whole = 4`. Measure before raising them ([ch. 12](12-problemas-y-soluciones.md)).

### 4. Know whether there is a linked task

```ts
/** Root of the main checkout (also from a worktree), or null outside git. */
async function mainCheckout($: EngineInterface): Promise<string | null> {
  const cwd = await $.session.cwd()
  const run = await $.process.run(['git', 'rev-parse', '--path-format=absolute', '--git-common-dir'], { cwd })
  if (run.exitCode !== 0) return null
  const common = run.stdout.trim()
  return common.endsWith('/.git') ? common.slice(0, -5) : null
}

/** Name of the task linked to this session if its PROGRESS.md exists; null otherwise. */
async function boundWork($: EngineInterface): Promise<string | null> {
  const root = await mainCheckout($)
  if (!root) return null
  const id = await $.session.id()
  if (!/^[\w-]+$/.test(id)) return null
  const link = await $.process.run(['cat', `${root}/tmp/handoff/.sessions/${id}`], { cwd: root })
  const work = link.exitCode === 0 ? link.stdout.trim() : ''
  if (!/^[\w.-]+$/.test(work) || work.startsWith('.')) return null   // no ../ and no paths
  const progress = await $.process.run(['test', '-f', `${root}/tmp/handoff/${work}/PROGRESS.md`], { cwd: root })
  return progress.exitCode === 0 ? work : null
}
```

- Validate the id and the task name before building paths: the link is a file anyone can write.
- This variant does not inject the handoff: your `SessionStart` `compact` hook does. If you don't have that hook, the plugin must add the handoff to its response (see the notes in step 5).
- If you already have the script from [chapter 04](04-script-comun.md), you can run it with the `SessionStart` `compact` input plus `"probe": true` (so it doesn't log the query) and check whether the output starts with a linked session's header.

### 5. The hook: `hooks/register.ts`

```ts
import type { EngineInterface, Register, SessionMessage } from 'claude-code'
import { keepTail, slim } from './tail.ts'

const TAIL_BUDGET = 80_000   // characters, ~20k tokens
const WHOLE = 4              // newest messages that come back whole
const MARKER =
  '[handoff-compact] Conversation compacted without a summary. The session handoff comes separately ' +
  '(SessionStart compact) and wins over what follows; check it against git status and git log. ' +
  'What follows are the newest messages, unsummarized. If the work is not finished, continue now ' +
  'with the next step: budget or token warnings are not a limit.'
const ACK = 'Understood.'

const built = (role: SessionMessage['role'], text: string): SessionMessage => ({ role, text, toolUses: [] })

// boundWork and mainCheckout from step 4

export const register: Register = on => {
  on('session.compact', async ($, e, next) => {
    if (e.trigger === 'precompute') return { skip: `${$.plugin.name}: compacts on demand from the handoff` }
    if (e.agentId !== undefined) return next(e)                  // subagent: normal summary
    if (!(await boundWork($))) return next(e)                     // no handoff: normal summary
    const tail = keepTail(e.messages, TAIL_BUDGET, WHOLE)
    if (!tail) return next(e)                                     // no safe cut fits
    const kept = slim(tail, WHOLE)
    $.ui.toast(`${$.plugin.name}: ${kept.length} of ${e.messages.length} messages kept, no summary`)
    // Roles must alternate: if the tail opens on the assistant, it goes right after the notice.
    const ack = kept[0]?.role === 'assistant' ? [] : [built('assistant', ACK)]
    return { messages: [built('user', MARKER), ...ack, ...kept] }
  })
}
```

- **Don't repeat the handoff** in `messages` if a `SessionStart` `compact` hook already injects it: it would arrive twice.
- If you **don't** have that hook, read `PROGRESS.md` (and, if you like, `DECISIONS.md` and `NOTES.md`) in the plugin and append them to the `MARKER`, truncated to a few thousand characters each.
- Any error inside the hook must end in `next(e)`: a failed compaction is worse than a summary. Wrap the detection in `try/catch` if your I/O can throw.

### 6. Tests: `hooks/tail.test.ts`

```ts
import type { SessionMessage } from 'claude-code'
import { expect, test } from 'claude-code/testing'
import { keepTail, MIN_KEPT, sizeOf, slim } from './tail.ts'

const prompt = (text: string): SessionMessage => ({ role: 'user', text, toolUses: [] })
const reply = (text: string): SessionMessage => ({ role: 'assistant', text, toolUses: [] })
const result: SessionMessage = {
  role: 'user', text: '', toolUses: [],
  toolResults: [{ tool_use_id: 't1', text: 'ok', isError: false }] as SessionMessage['toolResults'],
}
const talk = [prompt('one'), reply('a'), prompt('two'), reply('b'), result, reply('c'), prompt('three'), reply('d')]
const size = (list: SessionMessage[]) => list.reduce((n, m) => n + sizeOf(m), 0)
const cut = (list: SessionMessage[], budget: number) => keepTail(list, budget, 0, 1)

test('keeps everything that fits', () => expect(cut(talk, 100_000)).toEqual(talk))

test('never opens on a tool result', () => {
  const tail = cut(talk, size(talk.slice(4)))!
  expect(tail[0]!.toolResults?.length ?? 0).toBe(0)
})

test('opens on an assistant turn when there is no prompt (autonomous run)', () => {
  const run = [prompt('go'), ...Array.from({ length: 20 }, (_, i) => [reply(`step ${i}`), result]).flat()]
  expect(cut(run, size(run.slice(-6)))![0]!.role).toBe('assistant')
})

test('null when not even the newest safe stretch fits', () => expect(cut(talk, 0)).toBeNull())

test('drops the handle of old turns and keeps the current turn whole', () => {
  const withHandle = talk.map(m => ({ ...m, handle: {} }) as SessionMessage)
  const out = slim(withHandle, 0)
  expect(out[0]!.handle).toBeUndefined()
  expect(out.at(-1)!.handle).toBeDefined()
})

test('a weighted cut that keeps too little retries plain', () => {
  const big = Array.from({ length: 40 }, (_, i) => (i % 2 ? reply('x'.repeat(50)) : prompt('y'.repeat(50))))
  expect(keepTail(big, size(big.slice(-MIN_KEPT)), 0)!.length).toBeGreaterThanOrEqual(MIN_KEPT)
})
```

If `claude plugin test` complains about the literals, adjust them to your types: the exact shape of `toolResults` may vary between versions.

### 7. Install and test

```bash
claude plugin validate <plugins-folder>/handoff-compact     # manifest, module and types
claude plugin test <plugins-folder>/handoff-compact         # tail.test.ts
claude plugin marketplace add ./<plugins-folder> --scope project   # from the main checkout
claude plugin install handoff-compact@<marketplace> --scope project
git checkout .claude/settings.json                          # the CLI rewrites it with an absolute path
```

Real test:

1. Link a test session to a task with an invented marker in `PROGRESS.md`.
2. Run `claude --debug-file ./tmp/compact.log --resume <id> -p "/compact"`.
3. The log must say the plugin answered `session.compact` without `next()` and the summarizer didn't run.
4. Ask for the marker, without tools ([ch. 10](10-probar-el-handoff.md)).
5. Repeat without a link: the normal summary must be used.

### 8. Checklist

- [ ] Precompute with `skip`; subagent and no handoff with `next(e)`.
- [ ] The tail never opens on a message with tool results.
- [ ] Old turns without `handle`; current turn whole.
- [ ] Weights, unweighted retry and minimum of messages.
- [ ] Roles alternate after the notice.
- [ ] The handoff arrives only once (the `SessionStart` hook or the `MARKER`, not both).
- [ ] Any error ends in `next(e)`.
- [ ] Installed from the main checkout, with `settings.json` restored.
- [ ] Tested with a marker and measured in real use.

### In my case

Before publishing the recipe I copied the blocks from steps 1, 3, 4, 5 and 6 verbatim into an empty git repo, with no other hook, on the November 2026 Claude Code and Haiku:

| Test | Result |
| :-- | :-- |
| `claude plugin validate` | Passes; only warns that an icon is missing |
| `claude plugin test` | 6/6 |
| `/compact` with the linked session (`--plugin-dir`) | `answered session.compact without next() in 13.4ms` and `core never ran` |
| `/compact` without a link | The link's `cat` exits 1, `PreCompact` runs and the normal summary (`source=compact`) |

`claude-code` `plugin` `typescript` `recipe`
