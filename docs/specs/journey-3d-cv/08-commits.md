# Commits — MVP Propuesta A

> [<- Implementacion](07-implementacion-mvp.md) · Seccion 9 del plan-format.
> Cada commit deja el repo verde (lint + typecheck + tests del scope) y ejecuta
> su verificacion ANTES de commitear. Un solo PR
> `feature/journey-3d-propuesta-a -> dev`.

## Secuencia

### C1 — `docs(specs): agrega plan de ejecucion del MVP propuesta A (journey-3d-cv)`

- Contenido: la carpeta `docs/specs/journey-3d-cv/` completa (aun untracked) +
  los archivos 07-10 nuevos + README actualizado (estado, decisiones).
- Cubre: — (documentacion del plan).
- Verificacion: `python devtools/run.py verify --staged` (markdown OK).

### C2 — `feat(journey): scaffold de apps/journey con fallback CV 2D`

- Contenido: T1 — app nueva `@portfolio/journey` clonada de la estructura de
  generic (config, layout, site-config, pages es/en con CvSections en HTML,
  prebuild fetch-cache), deps three/R3F/drei/zustand declaradas, vitest setup.
- Cubre: AC-2, AC-3 (parcial: el fallback existe y es indexable).
- Verificacion: `pnpm install` + `pnpm --filter @portfolio/journey run build` +
  `pnpm --filter @portfolio/journey run typecheck`.

### C3 — `feat(journey): lib de salas data-driven y deteccion de tiers`

- Contenido: T2 + T3 (TDD: tests primero) — `rooms.ts` (mapeo experiences ->
  salas con retos/aprendizajes es/en + params de seniority) y `tiers.ts`
  (Full/Reduced/Static inyectable).
- Cubre: AC-6 (datos), AC-12 (params), AC-1/AC-2/AC-10 (deteccion).
- Verificacion: `pnpm --filter @portfolio/journey exec vitest run --coverage`
  (>=80% per-file) + typecheck.

### C4 — `feat(journey): isla 3D con walking-sim (camara, colisiones, puertas)`

- Contenido: T4 — `Journey3D.tsx` (isla client:only + dynamic import + montaje
  por tier), store zustand, `collision.ts` (AABB, con tests), PlayerControls
  (WASD + PointerLock), RoomShell procedural (paredes/piso/techo + texturas
  Canvas), Door con animacion + `Suspense`, Corridor con timeline de años.
- Cubre: AC-1, AC-4, AC-5, AC-14.
- Verificacion: vitest + `astro check` + build + preview manual (caminar y
  cruzar una puerta).

### C5 — `feat(journey): salas aula, corpoelec y cima ambientadas con portales al pasado`

- Contenido: T5a+T5b+T5c — las 3 salas procedurales (props firma, paleta,
  luz por seniority), ficha retos/aprendizajes (`<Html>` + raycast), portal al
  pasado (mini-escena sepia/glitch), 1+ micro-interaccion por sala, puerta
  "Proximamente" en la CIMA, CTA de contacto en la CIMA.
- Cubre: AC-6, AC-7, AC-9, AC-12.
- Verificacion: build + preview manual del loop completo por sala.

### C6 — `feat(journey): teletransporte, npcs procedurales y audio ambiente`

- Contenido: T6 — TeleportMenu (tecla M + boton, fade-out/in), NPCs humanoides
  low-poly procedurales con idle/walk por codigo (>=2 por sala), audio ambiente
  opt-in por sala (arranca en silencio, toggle persistente).
- Cubre: AC-8, AC-11, AC-13.
- Verificacion: build + preview manual.

### C7 — `feat(journey): tour guiado como tier reduced para movil`

- Contenido: T7 — `tour.ts` (CatmullRom + sampling, con tests), GuidedTour
  (camara sobre riel + textos por etapa), wiring del tier Reduced.
- Cubre: AC-10.
- Verificacion: vitest + build + preview con emulacion movil (DevTools).

### C8 — `test(journey): verificacion E2E del MVP y ajustes finales`

- Contenido: T8 — Parte A (barrido de referencias muertas) + Parte B (bateria
  completa) + fixes que surjan. Actualiza el estado en el README del plan.
- Cubre: cierre de todos los AC.
- Verificacion: la bateria completa de [10-verificacion-e2e.md](10-verificacion-e2e.md).

## Nota sobre el ciclo de vida de la carpeta del plan

La carpeta `docs/specs/journey-3d-cv/` **NO se elimina** al mergear este PR:
el plan cubre propuestas aun no construidas (B scroll-journey y variantes).
Solo se actualiza su README (estado: A implementada — MVP). La carpeta se
eliminara cuando el plan completo se cierre (regla de plan-format: la
eliminacion aplica al cerrar el plan completo, no a una fase).

## Gate de cierre

`git push` + PR SOLO con la bateria de la seccion 11 en verde (Partes A y B).
Parte C: N/A en este PR (sin deploy — decision del usuario).
