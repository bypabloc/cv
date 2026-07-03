# Paralelizacion con git worktrees — MVP Propuesta A

> [<- Commits](08-commits.md) · Seccion 10 del plan-format.

## Base secuencial (NO paralelizable)

C1 -> C2 -> C3 -> C4 deben ir en orden en la rama principal de trabajo
(`feature/journey-3d-propuesta-a`): tocan archivos transversales (workspace,
config de la app, store, collision, RoomShell/Door) que toda sala consume.
Lanzar worktrees antes de C4 garantiza conflictos.

## Fases worktree-safe (despues de C4)

| Fase | Archivos (disjuntos) | Worktree |
|------|----------------------|----------|
| T5a Sala Aula | `src/components/three/rooms/aula/*` | `journey-sala-aula` |
| T5b Sala CORPOELEC | `src/components/three/rooms/corpoelec/*` | `journey-sala-corpoelec` |
| T5c Sala CIMA | `src/components/three/rooms/cima/*` | `journey-sala-cima` |

- Interfaz estable: cada sala implementa el contrato `RoomSceneProps` definido
  en C4 (`RoomShell` + datos de `rooms.ts`). Mientras el contrato no cambie,
  las 3 salas son file-exclusive y paralelizables.
- Cap de concurrencia ([orchestration.md](../../../.claude/rules/orchestration.md)):
  **<=4 agentes a la vez, 1 workflow** — las 3 salas caben en UNA ola.
- `isolation: 'worktree'` SOLO porque mutan archivos en paralelo. Cada worktree
  corre su propio `pnpm install`; si se crea con `git worktree add` manual,
  copiar los env gitignored (`cp -rn docker/env/. <worktree>/docker/env/`).

## NO se paraleliza

- C6 y C7 tocan el store, el wiring de tiers y las salas ya creadas
  (transversales). Se hacen en secuencia sobre la rama principal (C6 y C7
  pueden intercalarse entre si solo si no tocan los mismos archivos — en la
  practica ambos tocan `Journey3D.tsx`, asi que van en orden).
- C8 (verificacion E2E) es siempre secuencial y final.
- El merge de los worktrees de salas se hace en orden (aula -> corpoelec ->
  cima), rebasando cada uno sobre el resultado anterior si hiciera falta.

## Nota de ejecucion real

Si la implementacion la lleva UNA sola sesion (este caso), las salas pueden
hacerse en secuencia sin worktrees — esta seccion habilita el fan-out, no lo
exige. El plan de commits no cambia en ninguno de los dos modos.
