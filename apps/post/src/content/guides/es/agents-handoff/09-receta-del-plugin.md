**09**

# Receta del plugin, paso a paso

[← Índice](README.md)

---

### Requisitos

- Claude Code **2.1.287 o posterior** (plugins con módulo TypeScript, acceso anticipado).
- Un handoff con vínculo por sesión ([cap. 03](03-handoff-en-disco.md)): `<repo>/tmp/handoff/.sessions/<session_id>` contiene el nombre del trabajo y `<repo>/tmp/handoff/<trabajo>/PROGRESS.md` existe.
- `git` en el `PATH`.

No necesita un script propio: el paso 4 detecta el trabajo vinculado desde el plugin. Los tipos del motor (`claude-code`) los trae Claude Code; si una firma de esta receta no coincide con tu versión, `claude plugin validate` lo dice. Manda el tipo instalado, no este texto.

### 1. Archivos

```text
<carpeta-de-plugins>/                      # p. ej. .claude/plugins-local/
├── .claude-plugin/marketplace.json        # declara el marketplace local
└── handoff-compact/
    ├── .claude-plugin/plugin.json         # manifiesto
    └── hooks/
        ├── hooks.json                     # qué módulos cargar
        ├── register.ts                    # los hooks
        ├── tail.ts                        # elige la cola (puro, sin E/S)
        └── tail.test.ts                   # tests de la cola
```

`.claude-plugin/marketplace.json`:

```json
{
  "name": "<marketplace>",
  "owner": { "name": "<tu nombre>" },
  "plugins": [{ "name": "handoff-compact", "source": "./handoff-compact" }]
}
```

`handoff-compact/.claude-plugin/plugin.json`:

```json
{
  "name": "handoff-compact",
  "version": "0.1.0",
  "description": "Compacta sin resumir con el modelo cuando la sesión tiene un handoff en disco"
}
```

`handoff-compact/hooks/hooks.json`:

```json
{ "modules": ["./register.ts"] }
```

### 2. Lo que usas de la API

| Pieza | Uso |
| :-- | :-- |
| `import type { Register, EngineInterface, SessionMessage } from 'claude-code'` | Tipos del módulo, del contexto del hook y de un mensaje |
| `export const register: Register = on => { … }` | Punto de entrada: registra hooks con `on` |
| `on('session.compact', async ($, e, next) => …)` | Antes de cada compactación |
| `e.trigger` | Origen; `'precompute'` es el resumen anticipado |
| `e.agentId` | Definido si compacta un subagente |
| `e.messages` | La conversación como `SessionMessage[]` |
| `return { messages }` | Reemplaza la conversación; el resumidor no corre |
| `$.session.id()`, `$.session.cwd()` | Id y directorio de la sesión (async) |
| `$.process.run(argv, { cwd, stdin?, timeoutMs? })` | Ejecuta un proceso; devuelve `{ exitCode, stdout, … }` |
| `$.ui.toast(texto)` | Aviso breve en la interfaz |

Un `SessionMessage` tiene `role` (`'user'` o `'assistant'`), `text`, `toolUses`, `toolResults?` y `handle?`. **Con `handle`**, el mensaje vuelve tal cual (con `thinking` y adjuntos); **sin `handle`**, el motor lo rearma con `role`, `text` y los bloques de herramientas. Un mensaje que construyes tú: `{ role, text, toolUses: [] }`.

### 3. La cola: `hooks/tail.ts`

Puro, sin E/S, para poder probarlo con `claude plugin test`.

```ts
import type { SessionMessage } from 'claude-code'

/** Peso en el presupuesto de un mensaje que vuelve entero (su thinking y adjuntos viajan sin que se midan). */
export const WHOLE_WEIGHT = 3
/** Mínimo de mensajes de un corte ponderado antes de probar sin ponderar. */
export const MIN_KEPT = 12

/** Tamaño aproximado en caracteres: texto, argumentos de cada llamada y texto de cada resultado, una vez cada uno. */
export const sizeOf = (m: SessionMessage): number =>
  m.text.length +
  m.toolUses.reduce((n, use) => n + JSON.stringify(use.input).length, 0) +
  (m.toolResults ?? []).reduce((n, r) => n + r.text.length, 0)

/**
 * Lugar seguro para abrir la cola: cualquier mensaje del asistente (sus resultados vienen después) o uno del
 * usuario con texto y sin resultados. Abrir en un mensaje con resultados dejaría resultados sin su llamada.
 */
const opensTurn = (m: SessionMessage): boolean =>
  m.role === 'assistant' || (m.text.trim() !== '' && (m.toolResults?.length ?? 0) === 0)

/**
 * El tramo más reciente que cabe en `budget` caracteres y abre en un lugar seguro. Pesan `weight` los mensajes
 * que volverán enteros: el turno en curso (desde el último pedido del usuario) y los `whole` más nuevos.
 * Null si ni el tramo más reciente cabe: entonces se compacta con el resumen.
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
  // Un lote grande de herramientas en paralelo, o un corte que deja casi nada: probar sin ponderar.
  if (weight > 1 && (kept?.length ?? 0) < MIN_KEPT) {
    const plain = keepTail(messages, budget, whole, 1)
    if ((plain?.length ?? 0) > (kept?.length ?? 0)) return plain
  }
  return kept
}

/**
 * Devuelve sin `handle` todo salvo el turno en curso y los `whole` más nuevos: el motor los rearma sin thinking
 * ni reglas anidadas (~90 % de una cola real). El turno en curso queda entero: la API exige su thinking intacto.
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

Valores de partida: `budget = 80_000` caracteres (~20k tokens) y `whole = 4`. Antes de subirlos, mide ([cap. 12](12-problemas-y-soluciones.md)).

### 4. Saber si hay trabajo vinculado

```ts
/** Raíz del checkout principal (también desde un worktree), o null fuera de git. */
async function mainCheckout($: EngineInterface): Promise<string | null> {
  const cwd = await $.session.cwd()
  const run = await $.process.run(['git', 'rev-parse', '--path-format=absolute', '--git-common-dir'], { cwd })
  if (run.exitCode !== 0) return null
  const common = run.stdout.trim()
  return common.endsWith('/.git') ? common.slice(0, -5) : null
}

/** Nombre del trabajo vinculado a esta sesión si su PROGRESS.md existe; null si no. */
async function boundWork($: EngineInterface): Promise<string | null> {
  const root = await mainCheckout($)
  if (!root) return null
  const id = await $.session.id()
  if (!/^[\w-]+$/.test(id)) return null
  const link = await $.process.run(['cat', `${root}/tmp/handoff/.sessions/${id}`], { cwd: root })
  const work = link.exitCode === 0 ? link.stdout.trim() : ''
  if (!/^[\w.-]+$/.test(work) || work.startsWith('.')) return null   // nada de ../ ni rutas
  const progress = await $.process.run(['test', '-f', `${root}/tmp/handoff/${work}/PROGRESS.md`], { cwd: root })
  return progress.exitCode === 0 ? work : null
}
```

- Valida el id y el nombre del trabajo antes de armar rutas: el vínculo es un archivo que cualquiera puede escribir.
- Esta variante no inyecta el handoff: lo hace tu hook `SessionStart` `compact`. Si no tienes ese hook, el plugin debe agregar el handoff a su respuesta (ver las notas del paso 5).
- Si ya tienes el script del [capítulo 04](04-script-comun.md), puedes ejecutarlo con la entrada de `SessionStart` `compact` y `"probe": true` (para que no registre la consulta en la bitácora), y mirar si la salida trae el encabezado de una sesión vinculada.

### 5. El hook: `hooks/register.ts`

```ts
import type { EngineInterface, Register, SessionMessage } from 'claude-code'
import { keepTail, slim } from './tail.ts'

const TAIL_BUDGET = 80_000   // caracteres, ~20k tokens
const WHOLE = 4              // mensajes más nuevos que vuelven enteros
const MARKER =
  '[handoff-compact] Conversation compacted without a summary. The session handoff comes separately ' +
  '(SessionStart compact) and wins over what follows; check it against git status and git log. ' +
  'What follows are the newest messages, unsummarized. If the work is not finished, continue now ' +
  'with the next step: budget or token warnings are not a limit.'
const ACK = 'Understood.'

const built = (role: SessionMessage['role'], text: string): SessionMessage => ({ role, text, toolUses: [] })

// boundWork y mainCheckout del paso 4

export const register: Register = on => {
  on('session.compact', async ($, e, next) => {
    if (e.trigger === 'precompute') return { skip: `${$.plugin.name}: compacts on demand from the handoff` }
    if (e.agentId !== undefined) return next(e)                  // subagente: resumen normal
    if (!(await boundWork($))) return next(e)                     // sin handoff: resumen normal
    const tail = keepTail(e.messages, TAIL_BUDGET, WHOLE)
    if (!tail) return next(e)                                     // ningún corte seguro cabe
    const kept = slim(tail, WHOLE)
    $.ui.toast(`${$.plugin.name}: ${kept.length} of ${e.messages.length} messages kept, no summary`)
    // Los roles deben alternar: si la cola abre en el asistente, va directo tras el aviso.
    const ack = kept[0]?.role === 'assistant' ? [] : [built('assistant', ACK)]
    return { messages: [built('user', MARKER), ...ack, ...kept] }
  })
}
```

- **No repitas el handoff** en `messages` si un hook `SessionStart` `compact` ya lo inyecta: llegaría dos veces.
- Si **no** tienes ese hook, lee `PROGRESS.md` (y si quieres `DECISIONS.md` y `NOTES.md`) en el plugin y agrégalos al `MARKER`, truncados a unos miles de caracteres cada uno.
- Cualquier error dentro del hook debe terminar en `next(e)`: una compactación fallida es peor que un resumen. Envuelve la detección en `try/catch` si tu E/S puede lanzar.

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

Si `claude plugin test` se queja de los literales, ajústalos a tus tipos: la forma exacta de `toolResults` puede variar entre versiones.

### 7. Instalar y probar

```bash
claude plugin validate <carpeta-de-plugins>/handoff-compact     # manifiesto, módulo y tipos
claude plugin test <carpeta-de-plugins>/handoff-compact         # tail.test.ts
claude plugin marketplace add ./<carpeta-de-plugins> --scope project   # desde el checkout principal
claude plugin install handoff-compact@<marketplace> --scope project
git checkout .claude/settings.json                              # la CLI lo reescribe con ruta absoluta
```

Prueba real:

1. Vincula una sesión de prueba a un trabajo con un marcador inventado en `PROGRESS.md`.
2. Ejecuta `claude --debug-file ./tmp/compact.log --resume <id> -p "/compact"`.
3. El log debe decir que el plugin respondió `session.compact` sin `next()` y que el resumidor no corrió.
4. Pregunta por el marcador, sin herramientas ([cap. 10](10-probar-el-handoff.md)).
5. Repite sin vínculo: debe usarse el resumen normal.

### 8. Checklist

- [ ] Precálculo con `skip`; subagente y sin handoff con `next(e)`.
- [ ] La cola nunca abre en un mensaje con resultados de herramienta.
- [ ] Turnos viejos sin `handle`; turno en curso entero.
- [ ] Pesos, reintento sin ponderar y mínimo de mensajes.
- [ ] Roles alternados tras el aviso.
- [ ] El handoff llega una sola vez (hook `SessionStart` o el `MARKER`, no ambos).
- [ ] Cualquier error termina en `next(e)`.
- [ ] Instalado desde el checkout principal, con `settings.json` restaurado.
- [ ] Probado con un marcador y medido en uso real.

### En mi caso

Antes de publicar la receta copié tal cual los bloques de los pasos 1, 3, 4, 5 y 6 en un repo git vacío, sin ningún otro hook, con Claude Code de noviembre de 2026 y Haiku:

| Prueba | Resultado |
| :-- | :-- |
| `claude plugin validate` | Pasa; solo avisa que falta un ícono |
| `claude plugin test` | 6/6 |
| `/compact` con la sesión vinculada (`--plugin-dir`) | `answered session.compact without next() in 13.4ms` y `core never ran` |
| `/compact` sin vínculo | El `cat` del vínculo sale con 1, corre `PreCompact` y el resumen normal (`source=compact`) |

`claude-code` `plugin` `typescript` `receta`
