# Orquestacion: workflow / subagents / agents / worktree

> Como Claude Code elige y opera las primitivas de orquestacion en este
> repo: la herramienta `Workflow` (script JS determinístico en background),
> los subagentes (Agent/Task tool), los agent types (`.claude/agents/*.md`),
> los git worktrees (`isolation`) y las tareas en background. Incluye los
> CAPS de concurrencia para NO pegar el rate-limit "Server is temporarily
> limiting requests" y la politica de modelos (Opus 4.8 por defecto,
> Sonnet 4.6 acotado).

## Activacion

Aplica SIEMPRE que se:

- Mencione "workflow", "subagent", "agente", "worktree", "paralelizar",
  "orquestar", "fan-out", "en paralelo", "olas de agentes".
- Diseñe o ejecute un fan-out de agentes.
- Cree un plan (elegir que primitiva usa cada fase — ver
  [plan-format.md](plan-format.md) secciones 8 y 10).
- Decida si una tarea va inline, en un subagente, o en un workflow.

## Politica de modelos (OBLIGATORIA)

- **SIEMPRE** el default es **Opus 4.8** (`claude-opus-4-8`; 1M:
  `claude-opus-4-8[1m]`) para: el loop principal, planificacion, review,
  sintesis, y cualquier agente que requiera juicio. La suscripcion Max
  $200/mes alcanza para operar en Opus 4.8 por defecto.
- **SIEMPRE** los agentes de un workflow/Task **heredan el modelo de la
  sesion** si se OMITE `model`. Con la sesion en Opus 4.8, heredan Opus —
  omitir `model` es lo correcto por defecto.
- **Sonnet 4.6** (`claude-sonnet-4-6`) SOLO para, y porque alivia la
  presion de rate-limit en fan-outs grandes:
  - Fan-outs de **alta concurrencia** (varias olas de agentes a la vez).
  - Trabajo **mecanico/deterministico** sin juicio profundo: busquedas
    amplias, scaffolding repetitivo, transforms simples.
  - En script de workflow: `agent(prompt, {model: 'sonnet'})`.
- **NUNCA** bajar a Sonnet "para ahorrar" cuando la tarea pide juicio
  (architecture, plan, review final, security, debugging de causa raiz):
  ahi va Opus 4.8.
- **NUNCA** Haiku para codigo de produccion del repo (solo clasificacion
  o validacion triviales).

## Caps de concurrencia (para NO pegar el rate-limit) — CRITICO

El error `API Error: Server is temporarily limiting requests (not your
usage limit) · Rate limited` es un throttle transitorio per-minuto / de
capacidad del servidor — **NO tu cuota del plan** (el `(not your usage
limit)` lo dice literal). Lo dispara una RAFAGA de agentes concurrentes
con contexto grande: cada agente Opus 1M hereda todo el contexto ->
pico de input-tokens/min (ITPM) que excede el limite. Evidencia medida
en este repo: **14 agentes concurrentes -> 429 inmediato**
(`subagent_tokens=0`, ningun agente llego a correr). NO hay setting en
`settings.json` para limitar concurrencia: se controla **batcheando en
el script**.

Reglas duras:

- **SIEMPRE** maximo **1 workflow a la vez**. NUNCA lanzar 2+ workflows
  concurrentes (comparten el mismo pool de rate-limit).
- **SIEMPRE** maximo **4 agentes concurrentes** por workflow cuando
  llevan contexto grande en Opus 4.8. Diseña el fan-out en **olas de
  <=4** (batching), aunque pases 100 items a `parallel`/`pipeline`.
- **SIEMPRE** si necesitas mas paralelismo real, baja esos agentes a
  Sonnet 4.6 y/o reduce el contexto que cargan; aun asi NO superes
  **~6 concurrentes**.
- **NUNCA** lanzar la herramienta `Workflow` para diagnosticar o
  documentar SOBRE workflows: re-provoca el mismo rate-limit y no es
  orquestacion.
- **NUNCA** asumir "mas agentes = mas rapido": por encima del cap, la
  rafaga pega 429 y el run entero falla con 0 tokens utiles.

> Estos numeros son empiricos (Anthropic NO publica un cap de concurrencia
> oficial para el plan Max). Son el envelope seguro medido en este repo.
> Si se observa 429 por debajo de 4 concurrentes, bajar a 3.

### Patron de batching (cap de 4 en un workflow)

```javascript
function chunk(a, n) { const o = []; for (let i = 0; i < a.length; i += n) o.push(a.slice(i, i + n)); return o }

const results = []
for (const wave of chunk(ITEMS, 4)) {                 // <=4 concurrentes
  const r = await parallel(wave.map(it => () =>
    agent(promptFor(it), {schema: SCHEMA, phase: 'Verify'})))
  results.push(...r.filter(Boolean))
}
// El `await` por ola serializa las olas; la duracion de cada ola ya
// espacia la carga. NO uses sleep/Date.now/Math.random (no existen en
// scripts de workflow y rompen el resume).
```

## Regla de oro: NO 1 agente LLM por tarea deterministica

La causa #1 de rate-limit en este repo fue lanzar **1 agente por suite de
tests**. Correr `pytest` / lint / build / typecheck es **deterministico**:
NO necesita un LLM. Patron correcto:

- Correr las suites en **Bash** o en **1-2 agentes** que ejecuten varias
  suites secuencialmente.
- Reservar los agentes LLM (y el fan-out) para lo que SI necesita juicio:
  **review adversarial**, sintesis, deteccion de bugs.

Ej: para verificar el refactor no-barrels NO usar 14 agentes (uno por
lambda). Usar 1 agente que corra `serverless tests --type=unit --lambda=<X>`
por cada lambda + shared, y un panel de 2-3 agentes para el review.

## Tabla de decision: que primitiva usar

| Primitiva | Que es | Cuando usarla |
|-----------|--------|---------------|
| **inline** (sin delegar) | El loop principal hace el trabajo | Tarea de 1-3 pasos, archivo/dato conocido, conversacional |
| **Subagente** (Agent tool) | 1 agente delegado en-sesion, model-driven, devuelve la conclusion | Buscar/leer a lo ancho de muchos archivos y querer solo la conclusion; trabajo aislado que inundaria el contexto; usar un agent type (Explore, Plan, researcher, code-reviewer) |
| **Agent type** (`.claude/agents/*.md`) | Plantilla **Markdown + frontmatter** de un rol fijo (tools + prompt) | Reutilizar un rol (researcher, code-reviewer) con tools acotadas. NO es `.yaml` |
| **Workflow** (script JS) | Orquestacion determinística en background, fan-out a N agentes | >1 fase con loops/condicionales/fan-out; verificacion cruzada (review adversarial); migracion/audit a escala; pipeline por items. SOLO con opt-in explicito del usuario |
| **Worktree** (`isolation: 'worktree'`) | Checkout git aislado por agente | Agentes que **mutan archivos en paralelo** y colisionarian. NUNCA read-only (cuesta ~200-500ms + disco; se auto-borra si no cambia nada) |
| **run_in_background** (Bash) | Comando async detached | Builds/tests/deploys largos que no deben bloquear la sesion |
| **/loop** | Re-ejecuta un prompt/comando en intervalo | Polling de estado externo (CI, deploy); tareas auto-paceadas |
| **Scheduling / routines** (CronCreate) | Agente remoto en cron | Tareas recurrentes sin sesion activa (audits periodicos) |

## Opt-in del Workflow tool

- **NUNCA** llamar la herramienta `Workflow` salvo opt-in EXPLICITO:
  el usuario escribio "workflow"/"workflows", ultracode esta activo, o
  pidio orquestacion multi-agente con sus palabras.
- Diagnosticar, investigar o **documentar SOBRE** workflows NO es opt-in:
  responder directo (o con 1 subagente), NUNCA disparar un workflow.
- Para tareas que se beneficiarian de paralelismo pero sin opt-in:
  describir brevemente el workflow posible y preguntar, o usar subagentes
  sueltos (<=4 a la vez).

## Patrones de workflow (resumen)

- `pipeline(items, ...stages)` por **DEFECTO** (sin barrera entre stages;
  wall-clock = la cadena mas lenta).
- `parallel(thunks)` SOLO si necesitas TODOS los resultados juntos (dedup
  global, early-exit, "compara con los otros hallazgos"). Es una barrera.
- Batching en olas de <=4 para el cap de concurrencia.
- `agent(prompt, {schema})` para salida estructurada validada (sin parseo).
- `agent(prompt, {isolation: 'worktree'})` solo si muta archivos en paralelo.
- Patrones de calidad: **adversarial verify** (N escepticos por hallazgo),
  **judge panel** (N angulos + jueces + sintesis), **loop-until-dry**
  (hasta K rondas sin nada nuevo), **multi-modal sweep**, **completeness
  critic**.

## Integracion con planes (plan-format)

Al crear un plan, elegir la primitiva por fase:

- **Seccion 8** (descomposicion): tareas con archivos **disjuntos** son
  candidatas a fan-out; las que tocan config transversal NO se paralelizan.
- **Seccion 10** (worktrees): primero la **base secuencial** (commits
  transversales), luego olas worktree-safe de **<=4 agentes** con
  `isolation: 'worktree'`.
- **Implementacion** de tareas independientes: workflow con un agente por
  tarea en olas de <=4, o subagentes sueltos <=4.
- **Seccion 11** (verificacion E2E): NUNCA fan-out de 1 agente por comando;
  correr la bateria en Bash o 1-2 agentes.

## Anti-patrones

| Anti-patron | Por que | Correccion |
|-------------|---------|------------|
| 14 (o >6) agentes concurrentes con contexto Opus grande | Rafaga de ITPM -> 429, run entero con 0 tokens | Olas de <=4 (batching); o Sonnet para el fan-out |
| 2+ workflows a la vez | Comparten pool de rate-limit -> 429 | 1 workflow a la vez |
| 1 agente LLM por suite de tests / lint / build | Trabajo deterministico no necesita LLM; infla fan-out y rate-limit | Bash o 1-2 agentes corriendo suites secuenciales |
| `sleep`/`Date.now()`/`Math.random()` en script de workflow | No existen / rompen el resume (lanzan error) | `await` por ola; pasar timestamps via `args` |
| `parallel()` cuando alcanzaba `pipeline()` | Barrera innecesaria desperdicia wall-clock | `pipeline()` por defecto |
| `isolation: 'worktree'` para agentes read-only | ~200-500ms + disco por nada | Solo cuando mutan archivos en paralelo |
| Disparar `Workflow` para investigar/documentar workflows | Re-provoca el rate-limit; no es orquestacion | Responder directo o 1 subagente |
| Sonnet 4.6 para architecture/plan/review final | Pierde calidad de juicio | Opus 4.8 |
| Agent type definido en `.yaml` | El formato real es `.md` + frontmatter | `.claude/agents/<rol>.md` |

## Referencias cruzadas

- Skill: [`/orchestration`](../skills/orchestration/SKILL.md) — guia
  invocable con ejemplos.
- [plan-format.md](plan-format.md) — secciones 8 (paralelizacion) y 10
  (worktrees).
- [harness-protocol.md](harness-protocol.md) — patron output-en-disco de
  subagentes, regla del 75% de contexto, feature_list.
- [verify-before-done.md](verify-before-done.md) — la bateria de
  verificacion (que NO se fan-outea).
