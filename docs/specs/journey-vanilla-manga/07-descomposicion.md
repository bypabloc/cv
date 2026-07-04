# 07 — Seccion 8: descomposicion para paralelizacion

> Tareas atomicas con file-exclusivity. Escala: Large (motor completo +
> 4 factories + HUD). Cada tarea lista Archivos / AC / Depende de /
> Paralelizable con / Verify / Done.

## T1 — Exencion de tests + limpieza de suites

- **Archivos**: `apps/journey/package.json` (scripts test), borra
  `apps/journey/tests/`, `apps/journey/vitest.config.ts`; `pnpm-lock.yaml`
  NO se toca aqui (las deps se quitan en T9 para no romper el codigo React
  aun vivo).
- **AC**: AC-13. **Depende de**: —. **Paralelizable con**: T2.
- **Verify**: `pnpm -r run test` no ejecuta journey; `pnpm run lint` verde.
- **Done**: repo verde sin suites de journey.

## T2 — Base visual del motor: toon + themes + state

- **Archivos**: `engine/toon.ts`, `engine/themes.ts`, `engine/state.ts`
  (nuevos, aun sin referenciar — el build sigue verde).
- **AC**: AC-6 (materiales), AC-10 (texturas <= 512).
- **Depende de**: —. **Paralelizable con**: T1, T3.
- **Verify**: typecheck; lint.
- **Done**: pool toon cacheado, outline helper, texturas ink deterministas,
  labels canvas, disposeDeep con guard `userData.shared`.

## T3 — Personajes procedurales

- **Archivos**: `engine/character.ts` (nuevo).
- **AC**: AC-7. **Depende de**: T2 (usa toon/outline).
- **Paralelizable con**: T4, T5 (archivos disjuntos).
- **Verify**: typecheck; luego visual en T10.
- **Done**: makeCharacter + makeNpc con 4 estilos de pelo, caras canvas con
  parpadeo, walk/idle/patrulla, blob shadow, accesorios.

## T4 — Mundo: shells + zone manager + preload + puertas + past

- **Archivos**: `engine/world.ts` (nuevo).
- **AC**: AC-3, AC-4. **Depende de**: T2 (texturas/temas), lib existentes.
- **Paralelizable con**: T3, T5.
- **Verify**: typecheck; AC-3 manual en T10 (memoria estable).
- **Done**: manifest WORLD, shells cacheados por zona, reglas de
  mount/dispose de la tabla de [02](02-motor-y-carga.md), preload con
  renderer.compile, fade hooks, teleport y enter/exitPast.

## T5 — Controles: 3a persona/POV + input + touch + tour

- **Archivos**: `engine/controls.ts` (nuevo).
- **AC**: AC-5, AC-8. **Depende de**: T2 (state), T3 (CharacterHandle).
- **Paralelizable con**: T4, T6.
- **Verify**: typecheck; manual en T10.
- **Done**: modos third/pov con V, drag/joystick, colision identica ambos
  modos, clamp de camara por zona, tour sobre el jugador.

## T6 — HUD DOM

- **Archivos**: `engine/hud.ts` (nuevo).
- **AC**: AC-9, AC-11. **Depende de**: T2 (state types).
- **Paralelizable con**: T4, T5, T7.
- **Verify**: typecheck; manual es/en en T10.
- **Done**: todos los paneles/strings portados + fade + loader + touch
  controls + botones (audio/camara/mapa/tour/salir).

## T7 — Factories de salas (4 tareas hermanas, disjuntas entre si)

- **T7a** `engine/rooms/aula.ts` · **T7b** `engine/rooms/corpoelec.ts` ·
  **T7c** `engine/rooms/cima.ts` · **T7d** `engine/rooms/past.ts`
- **AC**: AC-7, AC-9. **Depende de**: T2, T3, T4 (contratos RoomCtx).
- **Paralelizables entre si** (archivos disjuntos; los props compartidos ya
  viven en toon.ts desde T2).
- **Verify**: typecheck; cada sala monta en T10 con su chunk propio.
- **Done**: contenido narrativo portado 1:1 + micro-interacciones + NPCs.

## T8 — app.ts + audio + boot (integracion interna del motor)

- **Archivos**: `engine/app.ts`, `engine/audio.ts` (move), `lib/boot.ts`.
- **AC**: AC-1, AC-2, AC-12, AC-14. **Depende de**: T2-T7 (los cablea).
- **Paralelizable con**: —.
- **Verify**: typecheck; dev server monta el canvas y el loader desaparece.
- **Done**: RAF unico, tiers aplicados al renderer, degradacion automatica,
  log de presupuesto en DEV, exit/re-entrada.

## T9 — Swap Astro + limpieza de deps React/R3F

- **Archivos**: `pages/index.astro`, `pages/en/index.astro`,
  `astro.config.ts`, `package.json` + lockfile; BORRA `src/components/`,
  `src/lib/store.ts`, `src/types/troika-three-text.d.ts`, fuente troika.
- **AC**: AC-2, AC-12, AC-13. **Depende de**: T8.
- **Paralelizable con**: —.
- **Verify**: `pnpm install` + build + `rg` de restos (ver
  [06-archivos-y-tests.md](06-archivos-y-tests.md)).
- **Done**: cero React en journey; build verde.

## T10 — Verificacion E2E iterativa (fase final)

- Ver [10-verificacion-e2e.md](10-verificacion-e2e.md). **Depende de**: T9.

## Grafo de dependencias

```text
T1 ----------------------------\
T2 --> T3 --> T5 ----\          \
  \--> T4 -----------+--> T8 --> T9 --> T10
  \--> T6 ----------/
  \--> T7a..T7d ----/   (T7 tras T2+T3+T4 por contratos)
```

Checks de paralelizabilidad: cada tarea toca archivos exclusivos
(File Exclusivity OK); los contratos (RoomCtx, CharacterHandle, Hud,
EngineState) se congelan en T2/T3/T4 antes del fan-out (Interface
Stability OK); ninguna tarea excede ~1 archivo grande (Bounded Scope OK).
