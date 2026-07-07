# 7. Archivos afectados

## Crear

- `apps/journey/src/engine/loaders.ts` — GLTFLoader/DRACOLoader/KTX2Loader
  configurados una vez, exportados como singleton.
  - Verificar: `pnpm exec tsc --noEmit` sin errores; carga manual de un
    `.glb` de prueba en `pnpm --filter @portfolio/journey run dev`.
- `apps/journey/src/engine/postfx.ts` — EffectComposer + HalftonePass +
  ChromaticAberrationPass + OutlinePass.
  - Verificar: visualmente en dev server (AC-3).
- `apps/journey/scripts/copy-loader-assets.mjs` — copia `draco/`+`basis/`
  de `node_modules/three` a `public/` en `prebuild`.
  - Verificar: `apps/journey/public/{draco,basis}/` existen tras
    `pnpm --filter @portfolio/journey run build`.
- `apps/journey/public/models/{aula,futuro,destacame,characters}/*.glb`
  — assets CC0 descargados y comprimidos (Draco+KTX2 via `gltf-transform`).
  - Verificar: tamaño documentado por archivo (referencia: journey hoy
    pesa ~0 en assets de imagen; nuevo peso se reporta en el commit).
- `apps/journey/public/models/CREDITS.md` — tabla de licencias (AC-8).

## Modificar

- `apps/journey/src/engine/character.ts` — `makeCharacter`/`makeNpc`
  cargan `.glb` + `AnimationMixer` en vez de ensamblar primitivas. Firma
  pública intacta.
  - Verificar: AC-4, AC-5 (dev server, cruzar las 3 salas, ver NPCs
    animando y hablando).
- `apps/journey/src/engine/app.ts` — instancia `loaders.ts`+`postfx.ts`,
  reemplaza `renderer.render(scene, camera)` por `composer.render()`,
  `onResize` llama `postfx.resize()`.
  - Verificar: `pnpm exec astro check` + smoke visual.
- `apps/journey/src/engine/themes.ts` — evaluar si `RoomTheme.gradient`
  necesita reinterpretarse para el material nuevo (se decide en T2/T3
  mirando el resultado, no a priori).
  - Verificar: `pnpm exec tsc --noEmit`.
- `apps/journey/src/engine/rooms/aula.ts` — reemplaza mobiliario a mano
  por Kenney Furniture Kit, preserva `infoKit`/`wallArt`/`footprint()`.
  - Verificar: dev server, AC-6.
- `apps/journey/src/engine/rooms/futuro.ts` — reemplaza props sci-fi
  procedurales por pack CC0 (pendiente T4b), preserva `futurePortal`
  shader existente.
  - Verificar: dev server, AC-6.
- `apps/journey/src/engine/rooms/destacame.ts` — reemplaza mobiliario de
  oficina + showcases por assets CC0, preserva `softwareShowcase`/
  `infoKit`/`wallArt` (paneles DOM).
  - Verificar: dev server, AC-6, AC-7.
- `apps/journey/scripts/build-public-assets.mjs` — agrega
  `allowBlobWorkers: true` a `buildHeaders()` (AC-2).
  - Verificar: `pnpm --filter @portfolio/journey run build` +
    inspeccionar `dist/_headers` contiene `worker-src`.
- `apps/journey/package.json` — encadena `copy-loader-assets.mjs` en
  `prebuild`.
  - Verificar: `pnpm --filter @portfolio/journey run build` corre ambos
    scripts sin error.

## NO modificar (confirmado por exploración de código)

- `apps/journey/src/lib/layout.ts`, `lib/rooms.ts`, `lib/collision.ts`
- `apps/journey/src/engine/controls.ts`, `hud.ts`, `dialog.ts`, `world.ts`
  (contrato preservado, sin cambios de firma ni de `buildRoomShell`)
- `.claude/rules/journey-rooms.md` (canon manga-ink vigente para las 7
  salas no tocadas; se revisa en el plan de generalización)
- `apps/journey-realistic/`, `devtools/npc_pipeline/`, rama
  `feature/journey-npc-realism` (huérfanos, fuera de alcance)
