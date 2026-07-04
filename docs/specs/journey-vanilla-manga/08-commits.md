# 08 — Seccion 9: commits

> Rama `refactor/journey-vanilla-manga` desde `dev`. Cada commit deja el
> repo VERDE (lint + typecheck + build). Estrategia: el motor nuevo se
> construye en archivos NUEVOS no referenciados (C3-C6, el build no los
> ejecuta), y el swap real ocurre en C7. Un solo PR
> `refactor/journey-vanilla-manga -> dev`.

## C1 — plan

```text
docs(specs): plan journey-vanilla-manga — motor vanilla + manga-ink

- Agrega docs/specs/journey-vanilla-manga/ con las decisiones cerradas del
  usuario (vanilla, esclusa+fade, 3a persona default, manga-ink,
  personajes procedurales, joystick+tour, 3 salas, sin tests)
- Documenta arquitectura del motor, direccion de arte, descomposicion,
  commits, worktrees y verificacion E2E
```

- Cubre: contexto. Verificacion incremental: links del README validos.

## C2 — exencion de tests (T1)

```text
chore(journey): exime journey de tests unitarios

- Elimina apps/journey/tests/ (9 suites) y vitest.config.ts
- Remueve los scripts test/test:coverage del package (pnpm -r test deja de
  incluir journey; el pre-push solo corre Vitest en packages/*)
- Decision del usuario 2026-07-03 (plan journey-vanilla-manga)
```

- Cubre: AC-13. Verify: `pnpm run lint` + `pnpm -r run test` sin journey.

## C3 — base visual del motor (T2)

```text
feat(journey): base del motor vanilla — toon manga-ink, themes y estado

- engine/toon.ts: pool de MeshToonMaterial cacheado, gradientes de 3
  escalones, outline inverted hull, texturas canvas ink deterministas,
  labels con lettering de tinta, screenPanel y disposeDeep
- engine/themes.ts: paletas manga-ink por sala/pasillo/pasado
- engine/state.ts: estado plano del motor + registro de interactables
- Archivos aun no referenciados por la isla (el swap llega al final)
```

- Cubre: AC-6 (materiales). Verify: typecheck + lint.

## C4 — mundo y carga por esclusa (T4)

```text
feat(journey): world manager — shells, esclusa de pasillo y preload

- engine/world.ts: manifest WORLD data-driven (chunk por sala via dynamic
  import), shells cacheados por zona, dispose del contenido de la sala
  anterior al entrar al pasillo, preload de la siguiente con
  renderer.compile, fade si la precarga no llego, teleport y portal al
  pasado
```

- Cubre: AC-3, AC-4 (estructura). Verify: typecheck + lint.

## C5 — personajes y controles (T3 + T5)

```text
feat(journey): personajes procedurales anime + camara 3a persona/POV

- engine/character.ts: generador chibi (pelo por estilo, cara canvas con
  parpadeo, walk/idle/patrulla, accesorios, blob shadow) para jugador y
  NPCs distinguibles
- engine/controls.ts: 3a persona default con drag/joystick + POV con
  pointer-lock (tecla V), colision compartida, clamp de camara por zona,
  tour opcional sobre el riel existente
```

- Cubre: AC-5, AC-7, AC-8 (logica). Verify: typecheck + lint.

## C6 — salas y HUD (T6 + T7)

```text
feat(journey): salas manga-ink, pasado y HUD DOM

- engine/rooms/{aula,corpoelec,cima,past}.ts: contenido narrativo portado
  1:1 (props, micro-interacciones, fichas, portales, NPCs por sala)
- engine/hud.ts: HUD DOM i18n completo (zona, prompt, fichas HTML,
  contacto, teletransporte, fade, loader, overlays screentone/sepia,
  controles tactiles)
- engine/audio.ts: audio ambiente procedural movido desde components/
```

- Cubre: AC-9, AC-11 (logica). Verify: typecheck + lint.

## C7 — swap a vanilla + limpieza React (T8 + T9)

```text
refactor(journey): swap de la isla React al motor vanilla

- engine/app.ts: startJourney (renderer por tier, RAF unico, degradacion
  automatica, log de presupuesto en dev) cablea world/controls/hud/audio
- lib/boot.ts: entry liviano (tier, loader con el texto del contrato E2E,
  chunk 3D por dynamic import, exit/re-entrada)
- pages/{index,en/index}.astro: div#journey-root + script boot (fuera la
  isla client:only)
- Elimina src/components/, lib/store.ts, types de troika y la fuente woff
- package.json + astro.config: fuera react/react-dom/@astrojs/react,
  @react-three/*, troika-three-text, zustand, vitest y happy-dom
```

- Cubre: AC-1, AC-2, AC-12, AC-14. Verify: `pnpm install` + build +
  `rg` de restos + dev server manual.

## C8 — verificacion final (T10) + cierre

```text
docs(journey): verificacion E2E del refactor vanilla + limpieza de specs

- Ejecuta la bateria completa (Partes A y B de la seccion 11) y ajusta lo
  que falle
- Elimina docs/specs/journey-vanilla-manga/ y docs/specs/journey-3d-cv/
  (planes implementados: la carpeta de spec es efimera)
```

- El `git rm -r` de AMBAS carpetas de spec va aqui (journey-3d-cv quedo
  viva tras su merge y tambien corresponde retirarla).
- Verify: bateria completa de [10-verificacion-e2e.md](10-verificacion-e2e.md)
  Partes A+B en verde ANTES del push. Parte C tras el merge/deploy.

## Resumen de secuencia

| Commit | Tareas | Gate |
|--------|--------|------|
| C1 | plan | links |
| C2 | T1 | lint + `pnpm -r test` |
| C3 | T2 | typecheck + lint |
| C4 | T4 | typecheck + lint |
| C5 | T3+T5 | typecheck + lint |
| C6 | T6+T7 | typecheck + lint |
| C7 | T8+T9 | install + build + rg + manual |
| C8 | T10 | bateria completa |
