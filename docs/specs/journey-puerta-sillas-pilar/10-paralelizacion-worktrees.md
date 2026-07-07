# 10. Paralelización con git worktrees

> Elección de primitiva y caps de concurrencia: ver
> `.claude/rules/orchestration.md` (máx. 4 agentes concurrentes, 1
> workflow a la vez) y `.claude/rules/parallel-sessions.md` (worktrees
> solo cuando hay mutación paralela real de archivos).

## Base secuencial

- **Commit 2** (T1, `engine/state.ts`) es la base: T2, T3 y T5 dependen
  del tipo `SeatTarget`/campo `playerSeat`. Se hace primero, en la
  sesión principal (sin worktree — es un cambio de 1 archivo, trivial).
- **Commits 3-5** (T2, `props.ts`) son la segunda base secuencial: T4
  depende de que `officeLayout` ya exponga `seats`. También se hacen en
  la sesión principal (los 3 fixes comparten archivo, no tiene sentido
  aislarlos en worktrees distintos).

## Fases worktree-safe (archivos disjuntos)

| Ola | Tareas | Archivos | Worktree |
|-----|--------|----------|----------|
| 1 | T6 | `world.ts`, `hud.ts` | Opcional — puede correr en paralelo con T1 desde el inicio (0 dependencias) |
| 2 | T3, T5 | `controls.ts`, `aula.ts` | Opcional — ambas dependen solo de T1 |
| 3 | T4 (grupo 1/3) | `cofasa.ts`, `corpoelec.ts`, `ipasme.ts`, `iai.ts` | Solo si se paraleliza T4 |
| 3 | T4 (grupo 2/3) | `asesoria.ts`, `goodmeal.ts`, `dibal.ts`, `destacame.ts` | Solo si se paraleliza T4 |
| 3 | T4 (grupo 3/3) | `futuro.ts` | Solo si se paraleliza T4 |

`isolation: 'worktree'` solo se justifica si van a correr agentes
mutando estos archivos EN PARALELO. Si la implementación la hace una
sola sesión de forma secuencial (recomendado, ver nota abajo), ningún
worktree es necesario — todo el plan cabe en una sola rama de trabajo.

## Recomendación: NO vale la pena paralelizar aquí

Dado el tamaño real de las tareas (T3/T5/T6 son cambios de 1-2 archivos
con lógica acoplada al resto del motor; T4 son 9 diffs de 2-3 líneas
cada uno, mecánicos y casi idénticos entre sí), el overhead de crear
hasta 3 worktrees + coordinar su merge probablemente supera el tiempo
que ahorran. Se recomienda implementar TODO el plan de forma secuencial
en una sola sesión/rama, en el orden de
[09-commits.md](09-commits.md). La tabla de arriba queda documentada
por si en el futuro se decide paralelizar (ej. delegar T4 a un
sub-agente que edite las 9 salas en batch), pero no es el camino por
defecto de este plan.

## Lo que NO se paraleliza nunca

- Los 3 fixes de `props.ts` (T2) entre sí — mismo archivo.
- La sección 11 (verificación E2E final) — siempre corre al final,
  sobre el resultado consolidado de todas las tareas.
- La limpieza de la carpeta del plan (commit de cierre).
