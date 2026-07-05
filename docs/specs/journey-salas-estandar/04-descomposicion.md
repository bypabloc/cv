# 04 — Descomposicion para paralelizacion (seccion 8)

> [<- 03 Salas](03-salas.md) · [Commits ->](05-commits.md)

Tareas atomicas. Cada una: **Archivos** · **AC** · **Depende de** ·
**Paralelizable con** · **Verify** · **Done**. Granularidad Large (20 tareas).

## Base secuencial (infra transversal — NO paralelizable)

### T1 — Infra de RoomId a 8 salas + rename `cima`->`destacame`

- **Archivos**: `lib/rooms.ts` (RoomId union, `ROOM_SPECS`, specs de las 8),
  `engine/themes.ts` (8 entradas THEMES + PAST_CAPTIONS), `engine/world.ts:116`
  (manifest WORLD con 8 entradas), `engine/audio.ts` (si mapea por RoomId).
- **AC**: AC-1, AC-2.
- **Depende de**: —
- **Paralelizable con**: nada (todo depende de esto).
- **Verify**: `pnpm --filter @portfolio/journey typecheck` — el union RoomId
  fuerza los 4 puntos; falta uno = error de tipos. Escenas nuevas pueden ser
  stubs temporales (grupo vacio) para que compile.
- **Done**: typecheck verde con 8 ids; el viejo `cima` ya no existe como id.

### T2 — Paleta paredes-blancas (themes)

- **Archivos**: `engine/themes.ts` (valores wall/floor/accent/trim/light/
  gradient/fog/sky/screen por las 8 salas, tabla de [02](02-el-canon-de-sala.md)).
- **AC**: AC-2.
- **Depende de**: T1.
- **Paralelizable con**: nada (transversal; todas las salas leen theme).
- **Verify**: arrancar dev, cada sala con pared blanca + acento correcto.
- **Done**: las 8 salas con `wall: '#f2f0eb'`.

### T3 — Helpers del canon en props.ts (+ UI action showcase)

- **Archivos**: `engine/rooms/props.ts` (`officeLayout`, `npcCoworkers`,
  `wallArt`, `softwareShowcase`), `engine/world.ts` (`openShowcase` en
  WorldActions), `engine/state.ts` (`UiPanel` += `'showcase'`),
  `engine/app.ts` + `engine/hud.ts` (glue + panel DOM del showcase).
- **AC**: AC-3, AC-6, AC-7.
- **Depende de**: T1.
- **Paralelizable con**: T2 (archivos disjuntos salvo world.ts — coordinar).
- **Verify**: una sala de prueba que invoque los 4 helpers renderiza correcto;
  el panel showcase abre/cierra con E/Esc y deshabilita controles.
- **Done**: los 4 helpers exportados + la UI action funcionando end-to-end.

### T4 — Partir pasados en `rooms/past/<id>.ts` + dispatcher

- **Archivos**: `engine/rooms/past/index.ts` (dispatcher + `buildPast` shell),
  `engine/rooms/past/aula.ts` (MOVER sin cambios), eliminar `rooms/past.ts`
  monolitico. `engine/world.ts:125` (loadPast apunta a `./rooms/past/index`).
- **AC**: (habilita AC-11, AC-13, AC-20).
- **Depende de**: T1.
- **Paralelizable con**: T2, T3.
- **Verify**: entrar al pasado de aula/corpoelec/destacame sigue funcionando
  (sin cambios de contenido aun).
- **Done**: pasados en archivos por sala, aula intacto, dispatcher OK.

## Salas worktree-safe (paralelizables entre si tras la base)

Cada sala = 1 escena presente + 1 pasado + sus dialogos. Archivos disjuntos
(cada sala su `rooms/<id>.ts`, `rooms/past/<id>.ts`, `dialogs/<id>-*.ts`). El
theme y los helpers ya existen (base). **Cap de 4 en paralelo** (ver [06](06-paralelizacion-worktrees.md)).

### T5 — Aula (refactor minimo presente)

- **Archivos**: `rooms/aula.ts`, `dialogs/aula-presente.ts` (+NPCs). Pasado NO
  se toca (ya movido en T4).
- **AC**: AC-9.
- **Depende de**: T1, T3.
- **Paralelizable con**: T6-T12.
- **Verify**: profesor + compañeros nuevos conversables; pasado intacto.
- **Done**: AC-9 cumplido.

### T6 — CORPOELEC presente (refactor fuerte)

- **Archivos**: `rooms/corpoelec.ts`, `dialogs/corpoelec-presente.ts`.
- **AC**: AC-10.
- **Depende de**: T1, T2, T3.
- **Paralelizable con**: las demas salas.
- **Verify**: oficina ordenada + seccion inventario (equipos) + cascos +
  cuadros + showcase (gestion/buscador/reportes).
- **Done**: AC-10.

### T7 — CORPOELEC pasado (refactor)

- **Archivos**: `rooms/past/corpoelec.ts`, `dialogs/corpoelec-pasado.ts`.
- **AC**: AC-11, AC-20.
- **Depende de**: T4.
- **Paralelizable con**: las demas.
- **Verify**: oficinas viejas, personal frustrado, equipos regados.
- **Done**: AC-11.

### T8 — IPASME (presente + pasado + dialogos)

- **Archivos**: `rooms/ipasme.ts`, `rooms/past/ipasme.ts`,
  `dialogs/ipasme-presente.ts`, `dialogs/ipasme-pasado.ts`.
- **AC**: AC-14, AC-20.
- **Depende de**: T1, T2, T3, T4.
- **Paralelizable con**: T6, T9, T10, T11.
- **Verify**: consultorio + showcase historias clinicas + pasado carpetas
  papel.
- **Done**: AC-14 (ipasme).

### T9 — Cofasa (presente + pasado + dialogos)

- **Archivos**: `rooms/cofasa.ts`, `rooms/past/cofasa.ts`,
  `dialogs/cofasa-presente.ts`, `dialogs/cofasa-pasado.ts`.
- **AC**: AC-14, AC-20.
- **Depende de**: T1-T4.
- **Paralelizable con**: T6, T8, T10, T11.
- **Verify**: linea blisters + torre andon + showcase paradas + pasado
  planillas.
- **Done**: AC-14 (cofasa).

### T10 — Dibal (presente + pasado + dialogos)

- **Archivos**: `rooms/dibal.ts`, `rooms/past/dibal.ts`,
  `dialogs/dibal-presente.ts`, `dialogs/dibal-pasado.ts`.
- **AC**: AC-14, AC-20.
- **Depende de**: T1-T4.
- **Paralelizable con**: T6, T8, T9, T11.
- **Verify**: salon+cocina, POS+KDS+SUNAT, showcase POS, pasado comandas
  perdidas.
- **Done**: AC-14 (dibal).

### T11 — GoodMeal (presente + pasado + dialogos)

- **Archivos**: `rooms/goodmeal.ts`, `rooms/past/goodmeal.ts`,
  `dialogs/goodmeal-presente.ts`, `dialogs/goodmeal-pasado.ts`.
- **AC**: AC-14, AC-20.
- **Depende de**: T1-T4.
- **Paralelizable con**: T6, T8, T9, T10.
- **Verify**: Good Bags + app + showcase, pasado comida al tacho.
- **Done**: AC-14 (goodmeal).

### T12 — Destacame unificada (presente, ex-cima)

- **Archivos**: `rooms/destacame.ts` (renombrar/reescribir `cima.ts`),
  `dialogs/destacame-presente.ts`.
- **AC**: AC-12.
- **Depende de**: T1, T2, T3.
- **Paralelizable con**: T6, T8-T11 (pero comparte reuso de props de cima:
  hacerla tras T3). NO en el mismo worktree que T13.
- **Verify**: SIN Chile/Mexico, oficina real, 2 areas (PagaloAqui x3 +
  destacame x2), guiños DS/microservicios/vibe, kit + proximamente + CTA.
- **Done**: AC-12.

### T13 — Destacame pasado (deudas)

- **Archivos**: `rooms/past/destacame.ts`, `dialogs/destacame-pasado.ts`.
- **AC**: AC-13, AC-20.
- **Depende de**: T4.
- **Paralelizable con**: las demas.
- **Verify**: gente triste con deudas, procesos manuales.
- **Done**: AC-13.

### T14 — Sala Futuro (sintetica)

- **Archivos**: `rooms/futuro.ts`, `dialogs/futuro-presente.ts` (si lleva
  NPC), spec sintetico en `lib/rooms.ts` (textos literales).
- **AC**: AC-15.
- **Depende de**: T1, T2, T3.
- **Paralelizable con**: las demas.
- **Verify**: roadmap + proximamente + CTA; build OK sin slug.
- **Done**: AC-15.

## Cierre (post-salas)

### T15 — Mockups del showcase por sala (Canvas + panel HTML)

- **Archivos**: los mockups viven en cada `rooms/<id>.ts` (draw + panel), pero
  se pueden centralizar helpers de dibujo en `engine/rooms/mockups.ts`.
- **AC**: AC-6.
- **Depende de**: T3 + la sala respectiva.
- **Nota**: se hace junto con cada sala (T6-T12); esta tarea agrupa el diseño
  de branding de las webs oficiales (pagaloaqui, destacame, etc).

### T16 — Audio ambiente de las salas nuevas

- **Archivos**: `engine/audio.ts` (clips por RoomId), assets CC0.
- **AC**: AC-19.
- **Depende de**: T1.
- **Paralelizable con**: salas.
- **Verify**: cada sala suena su clip (opt-in, respeta mute).

### T17 — Verificar teleport + tour + fallback Static a 8 salas

- **Archivos**: (ninguno esperado — data-driven; verificar `hud.ts`,
  `lib/tour.ts`, `CvSections.astro` no requieren cambio).
- **AC**: AC-16, AC-17, AC-18.
- **Depende de**: todas las salas.
- **Verify**: M lista 8 salas; tour recorre 8; Static muestra CV completo.

### T18 — Perf: medir <100 draw calls/sala + optimizar

- **Archivos**: las salas que excedan.
- **AC**: AC-4.
- **Depende de**: todas las salas.
- **Verify**: `renderer.info.render.calls < 100` por sala en tier full.
- **Done**: todas <100.

### T19 — Rule del estandar

- **Archivos**: `.claude/rules/journey-rooms.md` (nueva).
- **AC**: (doc del estandar).
- **Depende de**: T3 (helpers finales).
- **Verify**: rule validada con `claude -p` (ver claude-config-testing.md).

### T20 — Verificacion E2E (seccion 11)

- **Archivos**: `docs/specs/journey-salas-estandar/` (git rm al final).
- **Depende de**: todo.
- Ver [07-verificacion-e2e.md](07-verificacion-e2e.md).

## Checks de paralelizabilidad

- **File Exclusivity**: T5-T14 tocan archivos disjuntos (1 sala = sus
  `rooms/<id>.ts` + `past/<id>.ts` + `dialogs/<id>-*.ts`). ✓
- **Interface Stability**: los helpers (T3) + theme (T2) son estables antes de
  las salas -> las salas solo consumen. ✓
- **Bounded Scope**: cada sala es autocontenida tras la base. ✓
- **Excepcion**: `world.ts` (manifest) y `lib/rooms.ts` (specs) los toca T1
  para las 8 de una vez (base secuencial), no cada sala -> sin colision.

> Eleccion de primitiva + concurrencia: ver [06](06-paralelizacion-worktrees.md).
> Cap duro: <=4 agentes/worktrees simultaneos (rate-limit). NO 1 agente LLM
> por tarea deterministica (typecheck/build -> Bash).
