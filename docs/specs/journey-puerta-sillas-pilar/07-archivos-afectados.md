# 7. Archivos Afectados

Todos los paths son relativos a `apps/journey/src/`. Ningún archivo se
crea ni se elimina — todo es modificación de código existente.

### Modificar

#### Feature A — Sentarse en sillas vacías

- `engine/state.ts` — agrega `SeatTarget` + campo `playerSeat` a
  `EngineState` (inicial `null`).
  - Verificar: `pnpm --filter @portfolio/journey exec astro check`
- `engine/controls.ts` — congela `applyMovement` mientras
  `state.playerSeat`, aplica posición/rotación/pose `'sit'` de la silla,
  restaura `idle`/movimiento al soltar.
  - Verificar: smoke visual (silla → sentado → WASD sin efecto → E →
    levantarse)
- `engine/rooms/props.ts` — `officeLayout` gana `roomIndex`/`state` en
  sus opts y expone `seats: Interactable[]` en `OfficeLayout` (silla
  vacía = índice fuera de `poweredSpots`; el toggle muta
  `state.playerSeat` directo, sin acción nueva en `world.ts`);
  `infoKit`/`lecternNotebook` tocados también por la Feature B (ver
  abajo); `wallArt` tocado también por la Feature C (ver abajo).
  - Verificar: `astro check` + smoke de las 3 features que tocan este
    archivo en conjunto
- `engine/rooms/cofasa.ts`, `corpoelec.ts`, `ipasme.ts`, `iai.ts`,
  `asesoria.ts`, `goodmeal.ts`, `dibal.ts`, `destacame.ts`, `futuro.ts`
  — pasan `roomIndex`/`state` (ya disponible en su `ctx`) a su
  `officeLayout({...})` existente y agregan
  `interactables.push(...office.seats)` junto a
  `interactables.push(...laptopToggles(...))`.
  - Verificar: `astro check` + smoke en al menos 2 de estas 9 salas
- `engine/rooms/aula.ts` — registra sillas vacías para `deskSpots[1]`,
  `deskSpots[2]` y los 4 `emptySpots` (excluye la silla del profesor,
  ocupada por el NPC `profesor`).
  - Verificar: smoke visual en `aula`

#### Feature B — Pilar centrado y libro con volumen

- `engine/rooms/props.ts` — `infoKit`: `noteEntryZ` pasa a `room.z`
  (centro real); `lecternNotebook`: `rotationY: Math.PI` en la llamada +
  reconstrucción del "libro" con `cover` (BoxGeometry) + `page` (Plane
  existente, reposicionada al frente de `cover`).
  - Verificar: smoke visual en `aula` + 1 sala más (confirma que el fix
    es compartido vía `infoKit`)

#### Feature C — Contorno de `wallArt`

- `engine/rooms/props.ts` — `wallArt`: cambia `mergedBoxes(...)` por
  `outlinedMergedBoxes(...)` en la construcción del marco.
  - Verificar: smoke visual en 2 salas con cuadros + medición de draw
    calls (<100 por sala)

#### Feature D — Puerta sin túnel

- `engine/world.ts` — `buildCorridorShell` se reduce a solo
  `buildDoor(door)` (sin muros/piso/techo/letrero/luz); nuevo método
  `world.crossDoor(index)` (secuencia abrir → warp → teleport →
  `applyZone` → warp inverso → cerrar → re-registrar interactable);
  `world.init()` registra el interactable de la puerta apuntando a
  `crossDoor` en vez de `openDoor` directo (via `registerDoorInteractable`,
  reutilizada tras cada cruce).
  - Verificar: `astro check` + smoke de cruce de puerta (2 cruces
    consecutivos, incluyendo el último del recorrido)
- `engine/hud.ts` — nueva variante `'warp'` en `fade(on, mode)` + el
  `<div class="jny-warp">` y su bloque CSS (franja azul/cian +
  zoom-blur), montado junto a `dreamEl`/`fadeEl`.
  - Verificar: smoke visual del efecto al cruzar una puerta

## Archivos explícitamente NO tocados (documentar la decisión)

- `lib/layout.ts` — Zone/corridor/doors quedan como datos internos (ver
  Decisión 2, capítulo 1, y sección "Qué NO cambia" del capítulo 5).
- `lib/tour.ts` — el riel del tour guiado no depende de la geometría del
  pasillo.
- `engine/character.ts` — la pose `'sit'` ya existe y se reutiliza sin
  cambios.
- `engine/audio.ts` — se reutilizan los SFX `door`/`whoosh` existentes,
  sin agregar ninguno nuevo.
- `engine/themes.ts` — `THEMES.corridor` queda declarado sin uso dentro
  de `buildCorridorShell`; no se elimina en este plan.
