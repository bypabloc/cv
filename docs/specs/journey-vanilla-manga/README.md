# journey-vanilla-manga — refactor del mundo 3D a vanilla + manga-ink

> Reescritura de la experiencia 3D de `apps/journey` (Propuesta A ya
> implementada con R3F): motor Three.js VANILLA (sin React/R3F/drei/zustand/
> troika), carga por esclusa de pasillo + fade (solo la sala activa en
> memoria), estetica manga-ink (cel shading + contornos de tinta), personaje
> procedural anime en 3a persona con toggle a POV, joystick tactil + tour
> opcional en movil. Journey queda EXENTO de tests unitarios por decision
> del usuario.

## Estado

| Fase | Estado |
|------|--------|
| Investigacion (guia + prototipo) | HECHO — `docs/progress/outputs/{guia-arquitectura-mundo-inmersivo.md,prototipo-mundo-inmersivo.html,brief-para-ia.md}` |
| Decisiones del usuario (8 respuestas) | HECHO (2026-07-03) — ver abajo, NO reabrir |
| Plan detallado (esta carpeta) | HECHO |
| Implementacion | PENDIENTE |
| Verificacion E2E + deploy | PENDIENTE |

## Decisiones cerradas (2026-07-03 — no reabrir sin el usuario)

1. **Perf**: atacar los 3 sintomas — carga inicial + FPS desktop + FPS movil.
2. **Stack**: reescritura COMPLETA a Three.js vanilla segun la guia de
   `docs/progress/outputs/`. Sin React en el 3D. Ademas journey queda
   EXENTO de tests (se eliminan `tests/`, scripts y deps de Vitest).
3. **Transicion**: HIBRIDO esclusa + fade — el pasillo libera (dispose) la
   sala anterior y precarga la siguiente; fade breve solo si la precarga no
   termino al cruzar la puerta. Coordenadas encadenadas en +Z se mantienen.
4. **Camara**: 3a persona DEFAULT; tecla V (o boton HUD) alterna a POV.
5. **Estilo**: MANGA-INK trazo marcado — MeshToonMaterial + gradient map de
   pocos escalones, contornos negros gruesos (inverted hull), colores
   planos, texturas canvas con trazos "a mano". CERO realismo (fuera
   IBL/PMREM/AgX/MeshStandardMaterial).
6. **Personajes**: SOLO PROCEDURAL (sin pipeline GLB) — jugador + NPCs por
   codigo, estilo anime/chibi, caras dibujadas en CanvasTexture,
   distinguibles entre si.
7. **Movil (tier reduced)**: joystick tactil 3a persona + boton "tour
   automatico" opcional (reemplaza el GuidedTour-only).
8. **Alcance**: 3 salas del MVP (aula/corpoelec/cima + portal al pasado) con
   WORLD manifest + THEMES data-driven; SIN stubs de salas futuras.

## Cuando leer cada archivo

| Archivo | Cuando leer |
|---------|-------------|
| [01-contexto-y-decision.md](01-contexto-y-decision.md) | Secciones 1-3: problema, solucion, criterios de aceptacion (AC-1..AC-14) |
| [02-motor-y-carga.md](02-motor-y-carga.md) | Seccion 4 (flujos antes/despues) + arquitectura del motor vanilla + zone manager + presupuesto perf |
| [03-estilo-manga-ink.md](03-estilo-manga-ink.md) | Direccion de arte: toon shading, outlines, texturas ink, THEMES, overlays |
| [04-personajes-y-controles.md](04-personajes-y-controles.md) | Generador de personajes anime, camaras 3a/POV, input desktop/touch, tour |
| [05-salas-hud-boot.md](05-salas-hud-boot.md) | Factories de salas, HUD DOM, boot/integracion Astro, audio |
| [06-archivos-y-tests.md](06-archivos-y-tests.md) | Seccion 6 (exencion de tests) + seccion 7 (archivos afectados con verify) |
| [07-descomposicion.md](07-descomposicion.md) | Seccion 8: tareas atomicas paralelizables |
| [08-commits.md](08-commits.md) | Seccion 9: secuencia de commits C1-C8 |
| [09-paralelizacion-worktrees.md](09-paralelizacion-worktrees.md) | Seccion 10: base secuencial + fases worktree-safe |
| [10-verificacion-e2e.md](10-verificacion-e2e.md) | Seccion 11 (Partes A/B/C) + seccion 12 (DoD) |

## Reglas criticas (heredadas + nuevas)

- El CV canonico/ATS/SEO sigue siendo el fallback 2D en el HTML
  (`#cv-fallback` + CvSections). El 3D es capa opt-in. NUNCA texto del CV
  como pixeles WebGL: las fichas retos/aprendizajes siguen siendo DOM.
- El chunk 3D se separa del HTML por dynamic import (igual que hoy) y cada
  sala mantiene su chunk propio (dynamic import por factory).
- Contrato E2E vigente (`tests/app/test_journey_3d_mounts.py`): el canvas
  monta y el texto exacto "Cargando el mundo 3D…" desaparece. El loader
  del boot nuevo DEBE usar ese mismo texto.
- Sistema de tiers intacto: Full / Reduced / Static con la misma logica
  pura de `lib/tiers.ts`.
- Presupuesto por zona activa (guia): < 100 draw calls, DPR <= 2 (desktop)
  / 1.5 (movil), 0-1 luces dinamicas con sombra, texturas canvas <= 512.
- `dispose()` completo al descargar una sala (geometrias + materiales
  propios + texturas). Los materiales toon COMPARTIDOS del pool global NO
  se disponen por sala.
- Rama de trabajo: `refactor/journey-vanilla-manga` desde `dev`. Push/PR
  solo con la bateria de [10-verificacion-e2e.md](10-verificacion-e2e.md)
  en verde (sin tests unit de journey: exento).

## Matriz de verificacion (resumen)

| Gate | Comando |
|------|---------|
| Lint | `pnpm run lint` (root, Biome) |
| Typecheck | `pnpm --filter @portfolio/journey run typecheck` |
| Build | `pnpm --filter @portfolio/journey run build` |
| Sin restos R3F | `rg -l "react\|zustand\|troika\|@react-three" apps/journey/src` → 0 archivos |
| Runtime | dev server + verificacion manual (FPS, draw calls, memoria, estetica) |
| E2E app (post-deploy) | `python devtools/run.py e2e --module=app --env=dev` |

## Fuentes

- Guia tecnica: `docs/progress/outputs/guia-arquitectura-mundo-inmersivo.md`
- Prototipo ejecutable: `docs/progress/outputs/prototipo-mundo-inmersivo.html`
- Brief IA: `docs/progress/outputs/brief-para-ia.md`
- Plan padre (implementado, se elimina al mergear este):
  [../journey-3d-cv/README.md](../journey-3d-cv/README.md)
