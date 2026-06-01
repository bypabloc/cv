---
name: orchestration
description: >
  Orchestration primitives reference for Claude Code in this repo: when and
  how to use the Workflow tool (deterministic JS multi-agent script), subagents
  (Agent/Task tool), agent types (.claude/agents/*.md), git worktrees
  (isolation), background tasks, and /loop. Includes the empirical concurrency
  CAPS to avoid the "Server is temporarily limiting requests (not your usage
  limit)" rate-limit (max 4 concurrent agents per workflow, 1 workflow at a
  time), the model policy (Opus 4.8 default everywhere, Sonnet 4.6 only for
  high-concurrency mechanical fan-outs), and how to pick a primitive when
  building a plan. ALWAYS invoke this skill BEFORE running a workflow, designing
  a fan-out, or deciding inline vs subagent vs workflow vs worktree. NEVER fire
  the Workflow tool just to investigate or document workflows — it re-triggers
  the rate-limit.
  Use when the user says "workflow", "workflows", "dynamic workflow", "subagent",
  "subagents", "subagente", "agent", "agente", "agentes", "agent type",
  "worktree", "worktrees", "isolation", "paralelizar", "en paralelo", "fan-out",
  "fan out", "orquestar", "orquestacion", "orchestrate", "olas de agentes",
  "concurrencia agentes", "rate limit workflow", "server is temporarily limiting
  requests", "cuantos agentes", "cuantos workflows", "ultracode", "background
  task", "run in background", "que modelo uso", "opus o sonnet".
user-invocable: true
allowed-tools: Read, Glob, Grep
argument-hint: "que quiero orquestar o que primitiva evaluar"
---

# Orquestacion en Claude Code

> Como elegir y operar workflow / subagents / agents / worktree en este
> repo, sin pegar el rate-limit. La regla dura vive en
> [.claude/rules/orchestration.md](../../rules/orchestration.md); esta skill
> es la guia invocable con ejemplos.

## Arbol de decision

```
¿La tarea es de 1-3 pasos con archivos/datos conocidos?
  SI -> inline (el loop principal lo hace)

¿Necesito buscar/leer a lo ancho de muchos archivos y solo quiero la conclusion?
  SI -> Subagente (Agent tool: Explore / Plan / researcher / general-purpose)

¿Es un rol reutilizable (review, research) con tools acotadas?
  SI -> Agent type (.claude/agents/<rol>.md) via Agent tool

¿Es deterministico (pytest, lint, build, typecheck)?
  SI -> Bash (o 1-2 agentes corriendo suites). NUNCA 1 agente por suite.

¿>1 fase con loops/condicionales/fan-out, verificacion cruzada, o audit/migracion a escala?
  Y ¿el usuario hizo opt-in explicito ("workflow", ultracode, pedido directo)?
    SI -> Workflow (script JS), con olas de <=4 agentes

¿Los agentes mutan archivos en paralelo y colisionarian?
  SI -> isolation: 'worktree'

¿Comando largo que no debe bloquear (build/deploy)?
  SI -> run_in_background

¿Polling de estado externo / recurrente?
  SI -> /loop (sesion) o routines/CronCreate (sin sesion)
```

## Caps de concurrencia (memoriza esto)

El rate-limit `Server is temporarily limiting requests (not your usage
limit)` NO es tu cuota: es un throttle per-minuto/capacidad disparado por
una rafaga de agentes con contexto grande. Medido: **14 concurrentes ->
429** (`subagent_tokens=0`).

- **1 workflow a la vez.** Nunca 2+ en paralelo.
- **<=4 agentes concurrentes** por workflow en Opus 4.8 (contexto grande).
- Mas paralelismo real -> Sonnet 4.6 y/o menos contexto; nunca >6.
- NO hay setting de concurrencia: se batchea en el script.

## Politica de modelos

- **Opus 4.8** (`claude-opus-4-8`) por DEFECTO en todo lo que pide juicio:
  loop principal, plan, review, sintesis, debugging. La suscripcion Max
  $200 alcanza.
- Omitir `model` en `agent()` -> hereda Opus de la sesion (correcto).
- **Sonnet 4.6** (`claude-sonnet-4-6`) SOLO en fan-outs de alta
  concurrencia o trabajo mecanico (busquedas amplias, scaffolding,
  transforms): `agent(prompt, {model: 'sonnet'})`. Tambien alivia el
  rate-limit del pool de Opus.

## Anatomia minima de un workflow

```javascript
export const meta = {
  name: 'verify-refactor',
  description: 'Corre suites por lambda + review adversarial',
  phases: [{ title: 'Tests' }, { title: 'Review' }],
}

// Tests: NO 1 agente por suite. 1 agente que corre todo via Bash.
phase('Tests')
const testReport = await agent(
  'Corre `python devtools/run.py serverless tests --type=unit` para cada ' +
  'lambda + shared, secuencialmente. Devuelve un resumen por suite.',
  { phase: 'Tests' },   // hereda Opus; o {model:'sonnet'} si es puramente mecanico
)

// Review: panel chico (<=4), adversarial, en una ola
phase('Review')
const DIMENSIONS = ['imports concretos', 'inits vacios', 'cross-domain FK']
const reviews = await parallel(DIMENSIONS.map(d => () =>
  agent(`Revisa adversarialmente el refactor no-barrels en la dimension: ${d}. ` +
        `Intenta REFUTAR que esta bien. Reporta hallazgos reales.`,
        { label: `review:${d}`, phase: 'Review', schema: FINDINGS })))

return { testReport, findings: reviews.filter(Boolean).flatMap(r => r.findings) }
```

## Patrones de calidad

- **Adversarial verify**: N escepticos por hallazgo; matas si la mayoria refuta.
- **Judge panel**: N intentos por angulos distintos + jueces + sintesis.
- **Loop-until-dry**: seguir buscando hasta K rondas sin nada nuevo.
- **Multi-modal sweep**: cada agente busca por un eje distinto.
- **Completeness critic**: agente final que pregunta "¿que falta?".

## Reglas que NO se rompen

- `pipeline()` por defecto; `parallel()` solo si necesitas todos juntos.
- NUNCA `sleep`/`Date.now()`/`Math.random()` en el script (rompen resume).
- NUNCA disparar `Workflow` para investigar/documentar workflows.
- NUNCA fan-outear la bateria de verificacion (1 agente por comando).
- `isolation: 'worktree'` solo si mutan archivos en paralelo.

## Referencias

- Regla dura: [.claude/rules/orchestration.md](../../rules/orchestration.md)
- Planes: [.claude/rules/plan-format.md](../../rules/plan-format.md) (sec. 8 y 10)
- Harness: [.claude/rules/harness-protocol.md](../../rules/harness-protocol.md)
