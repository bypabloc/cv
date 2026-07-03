# Implementacion MVP — Propuesta A (habitaciones)

> [<- README](README.md) · Secciones 3 (AC) y 8 (descomposicion) del
> plan-format para el MVP de la Propuesta A. Commits en
> [08-commits.md](08-commits.md), worktrees en
> [09-paralelizacion-worktrees.md](09-paralelizacion-worktrees.md),
> verificacion en [10-verificacion-e2e.md](10-verificacion-e2e.md).

## Decisiones cerradas (usuario, 2026-07-02 — no reabrir)

| Decision | Valor |
|----------|-------|
| Alcance | MVP del plan + Sala 0: **3 salas** (Aula, CORPOELEC, CIMA) |
| Extras incluidos | NPCs low-poly, tour guiado (tier Reduced movil), audio ambiente opt-in |
| Ruta | `/` de `apps/journey` ES la experiencia 3D; fallback CV 2D en el mismo HTML |
| Deploy | Solo local. Provisioning Cloudflare en un PR posterior |
| Estetica | Low-poly **procedural-first** (leccion Sidi Bou Said): primitivas + texturas Canvas + InstancedMesh + luz |
| NPCs | Humanoides **procedurales** animados por codigo como v1 (coherente con procedural-first, cero asset externo); swap a .glb CC0 (Quaternius) como mejora posterior si se quiere mas fidelidad |
| Stack | `three` + `@react-three/fiber@8` + `@react-three/drei@9` (React 18.3, mismo de generic) + `zustand`. SIN Rapier, SIN GSAP/Lenis, SIN nipplejs en el MVP |

## Mapeo salas <- datos reales (`@portfolio/content`)

| Sala | Slug(s) experience | Seniority | Epoca |
|------|--------------------|-----------|-------|
| 0 — Aula/Universidad | `iai` + `projects-degrees` | intern (academico) | 2015 |
| 1 — CORPOELEC | `corpoelec` | intern | 2013 |
| 8 — CIMA (Destacame Fullstack/Lider) | `destacame-architect` | lead | 2022-hoy |

Derivacion de textos (regla del plan): **RETOS** <- `summary` +
`responsibilities`; **APRENDIZAJES** <- `achievements` + `skillsTechnical`/
`skillsSoft`. Ambos idiomas (`BiLang` es/en). Orden narrativo por `start`
ascendente; el pasillo entre salas muestra el año.

## 3. Criterios de aceptacion (AC)

- **AC-1**: Given desktop con WebGL2, When carga `/`, Then se monta la isla 3D
  (tier Full) y el fallback 2D se oculta.
- **AC-2**: Given browser sin WebGL o `prefers-reduced-motion`, When carga `/`,
  Then NO se descarga el chunk de three y el CV 2D (CvSections) queda visible.
- **AC-3**: Given el HTML del build, Then contiene el texto real del CV
  (achievements) — indexable SEO/ATS sin ejecutar JS.
- **AC-4**: Given tier Full, When WASD/flechas + mouse-look, Then la camara
  camina con colisiones AABB (no atraviesa paredes ni props solidos).
- **AC-5**: Given proximidad a una puerta, When interactuo (tecla E / click),
  Then la puerta anima su apertura, la sala destino carga bajo `Suspense` y el
  paso es bidireccional (puedo volver).
- **AC-6**: Given una sala, When me acerco al cuaderno/pizarra y activo
  "Leer", Then se abre una ficha HTML (`<Html>` drei, DOM real) con RETOS y
  APRENDIZAJES derivados de los campos reales de la experience (es/en).
- **AC-7**: Given una sala, When cruzo la puerta-portal al pasado, Then la
  mini-escena "antes" se renderiza con estetica sepia/desaturada + glitch y
  puedo regresar al presente (la escena recupera color).
- **AC-8**: Given cualquier sala, When presiono `M` (o el boton de mapa), Then
  se abre el menu de teletransporte y saltar a otra sala hace
  fade-out -> carga -> fade-in.
- **AC-9**: Given cada sala del MVP, Then expone al menos 1 micro-interaccion
  tematica opcional (1 accion -> 1 animacion) que no bloquea el recorrido.
- **AC-10**: Given tier Reduced (movil con WebGL), When carga `/`, Then corre
  el tour guiado (camara sobre riel CatmullRom) con los textos de cada etapa,
  sin joystick; el menu de teletransporte sigue disponible.
- **AC-11**: Given el audio ambiente, Then arranca SIEMPRE silenciado y solo
  suena tras un gesto explicito del usuario (toggle) — politica de autoplay.
- **AC-12**: Given las 3 salas, Then la progresion de seniority se percibe:
  tamaño de sala, riqueza de luz y densidad de props crecen del Aula a la CIMA.
- **AC-13**: Given cada sala, Then hay >= 2 NPCs low-poly con animacion
  idle/walk que no obstruyen el recorrido.
- **AC-14**: Given el bundle del build, Then three/R3F viven en un chunk
  separado cargado por dynamic import; la pagina en tier Static no lo descarga.

## 8. Descomposicion para paralelizacion

Checks aplicados: File Exclusivity / Interface Stability / Bounded Scope.

### T1 — Scaffold `apps/journey`

- **Archivos**: `apps/journey/{package.json,astro.config.ts,tsconfig.json}`,
  `src/layouts/PageLayout.astro`, `src/lib/site-config.ts`,
  `src/pages/{index,en/index}.astro`, `public/`, `scripts/vite.config.ts`
- **AC**: AC-2, AC-3 (fallback en HTML)
- **Depende de**: — · **Paralelizable con**: —
- **Verify**: `pnpm install` sin warnings + `pnpm --filter @portfolio/journey build`
- **Done**: build estatico con CvSections en el HTML

### T2 — Lib de salas data-driven (TDD)

- **Archivos**: `apps/journey/src/lib/rooms.ts`,
  `apps/journey/tests/unit/lib/rooms.test.ts`
- **AC**: AC-6, AC-12 (mapeo seniority -> escala/luz)
- **Depende de**: T1 · **Paralelizable con**: T3
- **Verify**: `pnpm --filter @portfolio/journey exec vitest run` (>=80% file)
- **Done**: `buildRooms()` retorna las 3 salas con retos/aprendizajes es/en

### T3 — Deteccion de tiers (TDD)

- **Archivos**: `apps/journey/src/lib/tiers.ts`,
  `apps/journey/tests/unit/lib/tiers.test.ts`
- **AC**: AC-1, AC-2, AC-10
- **Depende de**: T1 · **Paralelizable con**: T2
- **Verify**: vitest run (>=80% per-file)
- **Done**: `detectTier()` puro (inyecta navigator/matchMedia/WebGL check)

### T4 — Isla 3D + nucleo walking-sim

- **Archivos**: `src/components/Journey3D.tsx` (isla + dynamic import),
  `src/components/three/{JourneyApp,PlayerControls,RoomShell,Door,Corridor}.tsx`,
  `src/lib/{store.ts,collision.ts}`, `tests/unit/lib/collision.test.ts`
- **AC**: AC-1, AC-4, AC-5, AC-14
- **Depende de**: T2, T3 · **Paralelizable con**: —
- **Verify**: vitest (collision) + `astro check` + build + preview manual
- **Done**: caminar entre 2 room-shells vacios por una puerta con carga

### T5a/T5b/T5c — Salas ambientadas (una tarea por sala)

- **Archivos** (disjuntos): `src/components/three/rooms/{aula,corpoelec,cima}/*`
  (escena, portal-al-pasado, micro-interaccion, guiños)
- **AC**: AC-6, AC-7, AC-9, AC-12
- **Depende de**: T4 · **Paralelizables entre si** (archivos disjuntos)
- **Verify**: build + preview manual por sala
- **Done**: sala con ambiente, ficha, portal sepia/glitch, 1+ micro-interaccion

### T6 — Teletransporte + NPCs + audio

- **Archivos**: `src/components/three/{TeleportMenu,Npc}.tsx`,
  `src/lib/audio.ts`, `src/components/three/rooms/*` (props npcs/audio por sala)
- **AC**: AC-8, AC-11, AC-13
- **Depende de**: T5 · **Paralelizable con**: T7
- **Verify**: build + preview manual
- **Done**: M abre menu, salto con fade; NPCs idle/walk; audio opt-in

### T7 — Tour guiado (tier Reduced)

- **Archivos**: `src/components/three/GuidedTour.tsx`, `src/lib/tour.ts`,
  `tests/unit/lib/tour.test.ts`
- **AC**: AC-10
- **Depende de**: T4 (+T5 para que haya que mostrar) · **Paralelizable con**: T6
- **Verify**: vitest (sampling de curva) + preview con emulacion movil
- **Done**: riel recorre las 3 salas con textos por etapa

### T8 — Verificacion E2E final

- Ver [10-verificacion-e2e.md](10-verificacion-e2e.md). No paralelizable.
