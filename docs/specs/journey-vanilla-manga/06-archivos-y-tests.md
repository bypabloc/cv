# 06 — Tests (exencion) y archivos afectados

## 6. Tests requeridos

**Decision del usuario (2026-07-03): journey queda EXENTO de tests
unitarios.** No hay 6.A/6.B para este plan. Lo que SI aplica:

### 6.C. Typecheck

- `pnpm --filter @portfolio/journey run typecheck` (astro check + tsc).
- TS strict se mantiene: el motor vanilla se escribe con los mismos flags
  (`noUncheckedIndexedAccess`, `verbatimModuleSyntax`, sin `any`).

### 6.D. E2E (existente, contra dev desplegado — Parte C)

- `tests/app/test_journey_3d_mounts.py` NO se modifica: su contrato
  (canvas montado + "Cargando el mundo 3D…" desaparece) lo cumple el boot
  nuevo usando el MISMO texto de loader.
- `tests/app/test_hub_links.py` no se ve afectado (la card de journey no
  cambia).

### Mecanica de la exencion (AC-13)

- El pre-push (`.git-hooks/pre-push` → `step_unit_tests`) solo corre
  Vitest sobre `packages/*` modificados — las apps NUNCA entran ahi. NO
  hay que tocar hooks.
- `pnpm -r run test` (root) ejecuta el script `test` de cada workspace que
  lo declare: al REMOVER los scripts `test`/`test:coverage` de
  `apps/journey/package.json`, journey queda fuera de forma natural.
- devtools `test_runner` no declara modulo journey (verificado con rg) —
  nada que tocar.
- CI (`ci.yml`) corre lint + build — journey sigue cubierto por ambos.
- Se eliminan los 9 archivos de `apps/journey/tests/unit/lib/` y
  `vitest.config.ts`: la mayoria testeaba el store zustand (se borra) y
  layout/rooms/tour/tiers/collision (se conservan los modulos pero SIN
  suite, por decision del usuario).

## 7. Archivos afectados

### Crear

- `docs/specs/journey-vanilla-manga/` — esta carpeta (plan)
  - Verificar: links relativos validos, archivos < 300 lineas
- `apps/journey/src/lib/boot.ts` — entry liviano: tier + loader + mount/exit
  - Verificar: `pnpm --filter @portfolio/journey run build` genera el chunk
    del engine separado del bundle de la pagina
- `apps/journey/src/engine/app.ts` — startJourney: renderer/escena/loop
  - Verificar: typecheck + dev server monta canvas
- `apps/journey/src/engine/state.ts` — estado plano + interactables
  - Verificar: typecheck
- `apps/journey/src/engine/toon.ts` — pool toon, outline, texturas ink,
  label, screenPanel, disposeDeep
  - Verificar: typecheck; en dev, `renderer.info` estable tras recorrer salas
- `apps/journey/src/engine/themes.ts` — THEMES manga-ink por zona
  - Verificar: typecheck
- `apps/journey/src/engine/world.ts` — manifest + shells + zone manager +
  preload + puertas + teleport + past
  - Verificar: AC-3/AC-4 manual (memoria estable, fade sin salas vacias)
- `apps/journey/src/engine/character.ts` — jugador + NPCs procedurales
  - Verificar: AC-7 visual (distinguibles, parpadeo, patrulla)
- `apps/journey/src/engine/controls.ts` — 3a/POV + teclado/touch + tour
  - Verificar: AC-5/AC-8 manual
- `apps/journey/src/engine/hud.ts` — HUD DOM i18n completo
  - Verificar: AC-9/AC-11 manual en `/` y `/en/`
- `apps/journey/src/engine/audio.ts` — movido de components/three/
  - Verificar: toggle audio funciona (opt-in)
- `apps/journey/src/engine/rooms/{aula,corpoelec,cima,past}.ts` — factories
  - Verificar: cada sala monta con su contenido + chunk propio en dist

### Modificar

- `apps/journey/src/pages/index.astro` — isla React → div + script boot
  - Verificar: build + curl al dev server contiene `journey-root` y el
    fallback `#cv-fallback`
- `apps/journey/src/pages/en/index.astro` — idem en ingles
  - Verificar: idem con `data-locale="en"`
- `apps/journey/astro.config.ts` — sin `react()` ni optimizeDeps react
  - Verificar: build OK
- `apps/journey/package.json` — deps y scripts (ver
  [05-salas-hud-boot.md](05-salas-hud-boot.md)); `pnpm install` regenera
  lockfile
  - Verificar: `pnpm install` sin warnings de peer deps; `pnpm -r run test`
    no entra a journey

### Eliminar

- `apps/journey/src/components/` (Journey3D.tsx + three/ completo: 14
  archivos React/R3F)
- `apps/journey/src/lib/store.ts` (zustand)
- `apps/journey/src/types/troika-three-text.d.ts`
- `apps/journey/tests/` (9 suites) + `apps/journey/vitest.config.ts`
- `apps/journey/public/fonts/space-grotesk-latin-400-normal.woff` (solo si
  `rg -l 'space-grotesk-latin-400' apps/journey` devuelve 0 tras el swap)
- Verificar (global): `rg -l "react|@react-three|troika|zustand" apps/journey/src`
  → 0 archivos; `rg -l "components/three" apps/journey` → 0

### Se conservan sin cambios

`src/lib/{rooms,layout,collision,tiers,tour,site-config}.ts`,
`src/layouts/PageLayout.astro`, `scripts/` (pre/postbuild), `public/`
(salvo la fuente troika), `functions/` (MCP).
