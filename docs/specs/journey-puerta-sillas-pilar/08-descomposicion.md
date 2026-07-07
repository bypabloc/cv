# 8. Descomposición para Paralelización

> Ver la elección de primitiva (subagente vs. workflow vs. worktree) y el
> cap de concurrencia en `.claude/rules/orchestration.md`: máx. **4
> agentes concurrentes** por ola, **1 workflow a la vez**.

## Tareas

### T1 — Estado del jugador

- **Archivos**: `apps/journey/src/engine/state.ts`
- **AC referenciados**: AC-1, AC-2, AC-5
- **Depende de**: ninguna
- **Paralelizable con**: T6
- **Verify**: `pnpm --filter @portfolio/journey exec astro check`
- **Done**: `SeatTarget` + `EngineState.playerSeat` (inicial `null`)
  compilan sin errores.

### T2 — `props.ts`: las 3 fixes compartidos (officeLayout.seats +
   pilar/libro + contorno de wallArt)

- **Archivos**: `apps/journey/src/engine/rooms/props.ts`
- **AC referenciados**: AC-1, AC-3, AC-6, AC-7, AC-8, AC-9, AC-10
- **Depende de**: T1 (usa el tipo `EngineState`/`SeatTarget`)
- **Paralelizable con**: T3, T5, T6 (archivos distintos)
- **Verify**: `astro check` + Biome + smoke visual de pilar/libro/cuadro
  en `aula`
- **Done**: `officeLayout` expone `seats`; `infoKit` centra el pilar y
  gira el libro; `lecternNotebook` tiene volumen; `wallArt` usa
  `outlinedMergedBoxes`.

> Las 3 fixes comparten archivo (`props.ts`): NO se paralelizan entre sí
> (fallarían el check de File Exclusivity). Se implementan como 1 tarea,
> aunque puedan ser 3 commits secuenciales dentro de ella (ver
> [09-commits.md](09-commits.md)).

### T3 — Congelar movimiento + pose sentado

- **Archivos**: `apps/journey/src/engine/controls.ts`
- **AC referenciados**: AC-1, AC-2, AC-5
- **Depende de**: T1
- **Paralelizable con**: T2, T5, T6
- **Verify**: `astro check` + smoke (silla → sentado → WASD sin efecto)
- **Done**: `applyMovement` retorna temprano si `state.playerSeat`;
  posición/rotación/pose se aplican mientras dure.

### T4 — Wiring de sillas en las 9 salas con `officeLayout`

- **Archivos** (9, cada uno independiente): `engine/rooms/cofasa.ts`,
  `corpoelec.ts`, `ipasme.ts`, `iai.ts`, `asesoria.ts`, `goodmeal.ts`,
  `dibal.ts`, `destacame.ts`, `futuro.ts`
- **AC referenciados**: AC-1, AC-3
- **Depende de**: T2 (necesita `office.seats`)
- **Paralelizable con**: entre sí (archivos disjuntos) y con T5
- **Verify**: `astro check` por archivo + smoke en 2 de las 9 salas
- **Done**: cada sala pasa `roomIndex`/`state` a su `officeLayout` y
  registra `office.seats` en sus `interactables`.

### T5 — Sillas vacías del `aula`

- **Archivos**: `apps/journey/src/engine/rooms/aula.ts`
- **AC referenciados**: AC-4
- **Depende de**: T1 (tipo `SeatTarget`); NO depende de T2 (aula no usa
  `officeLayout`)
- **Paralelizable con**: T2, T3, T4, T6
- **Verify**: `astro check` + smoke visual en `aula`
- **Done**: `deskSpots[1]`, `deskSpots[2]` y los 4 `emptySpots` son
  sentables; la silla del profesor NO lo es.

### T6 — Puerta sin túnel + efecto "viaje al futuro"

- **Archivos**: `apps/journey/src/engine/world.ts`,
  `apps/journey/src/engine/hud.ts`
- **AC referenciados**: AC-11, AC-12, AC-13, AC-14
- **Depende de**: ninguna (feature totalmente independiente de A/B/C)
- **Paralelizable con**: T1, T2, T3, T4, T5 (archivos distintos)
- **Verify**: `astro check` + smoke de 2 cruces de puerta consecutivos
- **Done**: `buildCorridorShell` solo monta la puerta; `crossDoor(index)`
  hace abrir→warp→teleport→applyZone→warp→cerrar→re-registrar; `hud.fade`
  soporta `'warp'`.

## Granularidad

6 tareas (Large: 10-20 esperadas, pero T4 se subdivide en 9 archivos
independientes si se paraleliza al máximo, dando ~14 unidades de trabajo
reales). Ver nota de recomendación en
[10-paralelizacion-worktrees.md](10-paralelizacion-worktrees.md) sobre si
vale la pena paralelizar T4 dado su tamaño trivial por archivo.
