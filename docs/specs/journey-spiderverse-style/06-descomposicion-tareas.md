# 8. Descomposición para paralelización

Checks de paralelizabilidad: **File Exclusivity** (archivos disjuntos),
**Interface Stability** (contratos preservados: `RoomFactory`,
`CharacterHandle`/`NpcHandle`), **Bounded Scope** (una tarea no requiere
terminar otra fuera de sus dependencias declaradas).

## T1 — Loaders + CSP

- **Archivos**: `engine/loaders.ts` (nuevo), `scripts/copy-loader-assets.mjs`
  (nuevo), `scripts/build-public-assets.mjs` (modificar), `package.json`
  (modificar `prebuild`).
- **AC referenciados**: AC-1, AC-2.
- **Depende de**: nada (primera tarea).
- **Paralelizable con**: nada (base secuencial).
- **Verify**: `pnpm --filter @portfolio/journey run build` genera
  `public/draco/`+`public/basis/`; `dist/_headers` contiene `worker-src`.
- **Done**: build sin error, headers confirmados.

## T2 — Postprocesado (halftone + aberración + outline)

- **Archivos**: `engine/postfx.ts` (nuevo), `engine/app.ts` (modificar:
  wireado del composer + resize).
- **AC referenciados**: AC-3.
- **Depende de**: T1 (necesita el renderer ya con loaders disponibles
  para el smoke visual, aunque técnicamente postfx no usa GLTFLoader
  directo).
- **Paralelizable con**: nada (base secuencial; toca `app.ts` que T3
  también toca).
- **Verify**: dev server, ver el halftone/contorno/aberración sobre la
  escena actual (incluso con geometría manga-ink vieja, antes de migrar
  ninguna sala — valida el pipeline de postfx en aislado).
- **Done**: efecto visible, sin regresión de FPS catastrófica (sin
  métrica formal, juicio visual).

## T3 — Sistema de personajes

- **Archivos**: `engine/character.ts` (modificar, implementación
  interna), `engine/app.ts` (modificar: instanciar loader de personaje).
- **AC referenciados**: AC-4, AC-5.
- **Depende de**: T1 (loaders), T2 (postfx con `OutlinePass` para
  validar el contorno sobre `SkinnedMesh`).
- **Paralelizable con**: nada (base secuencial; las 3 salas dependen de
  esto).
- **Verify**: dev server, un NPC de prueba camina/habla con contorno
  correcto durante la animación.
- **Done**: `CharacterHandle`/`NpcHandle` preservado, 1 `.glb` real
  cargando y animando.

## T4a — Migrar `rooms/aula.ts`

- **Archivos**: `engine/rooms/aula.ts` (modificar),
  `public/models/aula/*.glb` (nuevos).
- **AC referenciados**: AC-6, AC-7.
- **Depende de**: T1, T2, T3 (base secuencial completa).
- **Paralelizable con**: T4b, T4c (archivos disjuntos, ≤3 agentes/
  worktrees simultáneos).
- **Verify**: dev server, sala aula completa (infoKit, wallArt, NPCs,
  colisión).
- **Done**: sala navegable, sin regresión de fichas/diálogos.

## T4b — Migrar `rooms/futuro.ts`

- **Archivos**: `engine/rooms/futuro.ts` (modificar),
  `public/models/futuro/*.glb` (nuevos).
- **AC referenciados**: AC-6, AC-7.
- **Depende de**: T1, T2, T3.
- **Paralelizable con**: T4a, T4c.
- **Verify**: dev server, sala futuro completa (incluye validar que
  `futurePortal` shader sigue andando).
- **Done**: sala navegable; si el pack sci-fi no se resolvió, plan B
  documentado en 05 aplicado.

## T4c — Migrar `rooms/destacame.ts`

- **Archivos**: `engine/rooms/destacame.ts` (modificar),
  `public/models/destacame/*.glb` (nuevos).
- **AC referenciados**: AC-6, AC-7.
- **Depende de**: T1, T2, T3.
- **Paralelizable con**: T4a, T4b.
- **Verify**: dev server, sala destacame completa (2 showcases +
  infoKit + wallArt + mobiliario).
- **Done**: sala navegable, sin regresión de showcases DOM.

## T5 — Créditos de licencias

- **Archivos**: `public/models/CREDITS.md` (nuevo).
- **AC referenciados**: AC-8.
- **Depende de**: T4a, T4b, T4c (necesita la lista final de assets
  usados).
- **Paralelizable con**: nada (cierre).
- **Verify**: tabla completa pack/URL/licencia por asset usado.
- **Done**: archivo commiteado.

## T6 — Verificación E2E manual + gate local-first

- **Archivos**: ninguno (solo verificación).
- **AC referenciados**: AC-6, AC-7, AC-9.
- **Depende de**: T4a, T4b, T4c, T5.
- **Paralelizable con**: nada (cierre).
- **Verify**: ver [09-verificacion-e2e.md](09-verificacion-e2e.md).
- **Done**: batería completa en verde, sin push/PR/deploy.
