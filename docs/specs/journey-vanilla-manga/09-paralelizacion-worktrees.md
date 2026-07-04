# 09 — Seccion 10: paralelizacion con git worktrees

> Que se puede correr en paralelo (worktrees/subagentes) y desde que
> commit. Caps de [orchestration.md](../../../.claude/rules/orchestration.md):
> maximo 4 agentes concurrentes, 1 workflow a la vez, olas de <= 4.

## Base secuencial (NO paralelizar)

Commits C1-C4 son la base: el plan, la exencion de tests y — critico —
los CONTRATOS que congelan las interfaces (`toon.ts`, `themes.ts`,
`state.ts` en C3; `world.ts` con `RoomCtx`/`RoomBuild` en C4). Hasta que
esos tipos esten commiteados, cualquier fan-out produce colisiones de
interfaz.

Tambien secuenciales (tocan archivos transversales): C7 (swap de paginas,
package.json, astro.config, borrado de components/) y C8 (verificacion).

## Fases worktree-safe (tras C4)

| Ola | Tareas | Archivos (disjuntos) |
|-----|--------|----------------------|
| Ola 1 (<= 4) | T3 personajes · T5 controles · T6 HUD | `engine/character.ts` · `engine/controls.ts` · `engine/hud.ts` |
| Ola 2 (<= 4) | T7a aula · T7b corpoelec · T7c cima · T7d past | `engine/rooms/*.ts` (1 archivo por tarea) |

- T5 consume `CharacterHandle` (T3): si se corre en la MISMA ola, el
  contrato debe fijarse antes en un stub dentro de C4 o arrancar T5 tras
  T3. Opcion simple: Ola 1 = T3+T6, Ola 2 = T5+T7a+T7b+T7c, Ola 3 = T7d.
- `isolation: 'worktree'` SOLO si los agentes mutan archivos en paralelo
  (aqui cada tarea escribe SU archivo — un worktree por agente evita
  lockfiles/dist compartidos, pero como los archivos son disjuntos tambien
  es valido correrlos como subagentes sobre el mismo checkout SIN builds
  concurrentes). Preferencia: subagentes en el mismo checkout, builds solo
  en el orquestador.

## Lo que NO se paraleliza

- C7 (swap Astro + deps + borrados) — transversal.
- La verificacion (C8): la bateria corre en Bash secuencial (regla de oro:
  NO 1 agente LLM por comando deterministico).
- `pnpm install` (lockfile compartido) — solo el orquestador.

## Como lanzar (si se usa fan-out)

```text
1. Orquestador commitea C1-C4 en refactor/journey-vanilla-manga
2. Ola de <= 4 subagentes, cada uno con su tarea del 07 (archivo unico,
   contrato congelado, prompt con el capitulo del plan correspondiente)
3. El orquestador integra, corre typecheck/lint, commitea C5/C6
4. C7 y C8 los hace el orquestador inline
```

La implementacion inline (sin fan-out) tambien es valida: el volumen es
~10 archivos nuevos y el acoplamiento alto en app.ts favorece un solo
autor. El fan-out solo compra tiempo en la Ola 2 (salas).
