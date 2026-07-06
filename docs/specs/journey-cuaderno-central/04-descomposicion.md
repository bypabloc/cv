# 04 — Descomposicion para paralelizacion (seccion 8)

> [<- 01 Cambios tecnicos](01-cambios-tecnicos.md) · [Commits ->](05-commits.md)

Tareas atomicas. Cada una: **Archivos** · **AC** · **Depende de** ·
**Paralelizable con** · **Verify** · **Done**. Granularidad Small (7
tareas).

## Base secuencial (helper compartido — NO paralelizable)

### T1 — Reposicionar `lecternNotebook` + nuevo collider en `infoKit`

- **Archivos**: `apps/journey/src/engine/rooms/props.ts` (funcion
  `infoKit`, ~L897-912).
- **AC**: AC-1, AC-2, AC-3, AC-4, AC-8.
- **Depende de**: —
- **Paralelizable con**: nada (todas las salas heredan de este cambio).
- **Verify**: `pnpm --filter @portfolio/journey typecheck`; arrancar dev,
  entrar a una sala cualquiera (ej. corpoelec) y confirmar que el cuaderno
  aparece en el eje central cerca de la entrada, bloqueando el paso, y que
  al acercarse + E sigue abriendo el panel de historia.
- **Done**: el helper compartido queda con la posicion + collider nuevos;
  retos/aprendizajes/grieta sin cambios.

## Ajustes por sala (worktree-safe tras T1)

Cada tarea toca un archivo de sala distinto (disjuntos). Cap de 4 en
paralelo (ver [06](06-paralelizacion-worktrees.md)).

### T2 — Escritorios: ipasme + iai (spots identicos)

- **Archivos**: `rooms/ipasme.ts`, `rooms/iai.ts`.
- **AC**: AC-6.
- **Depende de**: T1 (para verificar contra el pilar ya en su lugar).
- **Paralelizable con**: T3, T4, T5, T6.
- **Verify**: recorrido visual, entrada despejada como el aula; typecheck.
- **Done**: los 2 `deskSpots` de cada sala corridos, footprint fuera de la
  franja de 2m.

### T3 — Escritorios: asesoria + cofasa

- **Archivos**: `rooms/asesoria.ts`, `rooms/cofasa.ts`.
- **AC**: AC-6.
- **Depende de**: T1.
- **Paralelizable con**: T2, T4, T5, T6.
- **Verify**: idem T2.
- **Done**: idem T2 para estas 2 salas.

### T4 — Escritorios: dibal + goodmeal (laterales, prioridad menor)

- **Archivos**: `rooms/dibal.ts`, `rooms/goodmeal.ts`.
- **AC**: AC-6.
- **Depende de**: T1.
- **Paralelizable con**: T2, T3, T5, T6.
- **Verify**: idem T2.
- **Done**: idem T2 para estas 2 salas.

### T5 — Escritorios + NPC path: destacame (caso critico)

- **Archivos**: `rooms/destacame.ts`.
- **AC**: AC-5, AC-6.
- **Depende de**: T1.
- **Paralelizable con**: T2, T3, T4, T6.
- **Verify**: recorrido visual — desk corrido, NPC "valentina" rodea el
  pilar sin cruzarlo, sin superposicion entre desk/NPC/pilar.
- **Done**: AC-5 y AC-6 cumplidos para destacame.

### T6 — NPC path: goodmeal (daniela)

- **Archivos**: `rooms/goodmeal.ts` (mismo archivo que T4 — coordinar si
  corren en el mismo worktree, o secuenciar T4 antes de T6 si van en
  agentes separados).
- **AC**: AC-5.
- **Depende de**: T1 (y T4 si se secuencia en el mismo archivo).
- **Paralelizable con**: T2, T3, T5 (NO con T4 si comparten worktree del
  mismo archivo — ver nota de colision abajo).
- **Verify**: NPC "daniela" recorre su path sin cruzar el `footprint` del
  pilar.
- **Done**: AC-5 cumplido para goodmeal.

### T7 — Futuro: verificar coexistencia pilar + pedestal-CTA

- **Archivos**: `rooms/futuro.ts` (solo si se detecta conflicto real; de
  lo contrario, tarea de verificacion sin cambio de codigo).
- **AC**: AC-7.
- **Depende de**: T1.
- **Paralelizable con**: T2-T6.
- **Verify**: recorrido visual de futuro — pilar cerca de la entrada,
  pedestal-CTA en el muro final, sin overlap de colliders ni geometria.
- **Done**: AC-7 confirmado (con o sin cambio de codigo).

## Cierre

### T8 — Verificacion E2E (seccion 11)

- **Archivos**: `docs/specs/journey-cuaderno-central/` (`git rm` al final).
- **Depende de**: T1-T7.
- Ver [07-verificacion-e2e.md](07-verificacion-e2e.md).

## Checks de paralelizabilidad

- **File Exclusivity**: T2-T7 tocan archivos de sala disjuntos, EXCEPTO
  `rooms/goodmeal.ts` que aparece en T4 (desk) y T6 (NPC path) — si se
  paralelizan con worktrees/agentes distintos, secuenciar T4 antes de T6
  (o fusionarlas en una sola tarea "goodmeal completo" si se prefiere
  evitar la dependencia).
- **Interface Stability**: T1 (el helper) es estable antes de tocar
  cualquier sala — todas las demas tareas solo leen la posicion/collider
  nuevos para verificar contra ellos.
- **Bounded Scope**: cada tarea de sala es autocontenida (un archivo, un
  ajuste de coordenadas).

> Eleccion de primitiva + concurrencia: ver [06](06-paralelizacion-worktrees.md).
> Cap duro: <=4 agentes/worktrees simultaneos (rate-limit). NO 1 agente LLM
> por tarea deterministica (typecheck/build -> Bash).
