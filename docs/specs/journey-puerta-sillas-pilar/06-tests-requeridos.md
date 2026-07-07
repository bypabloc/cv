# 6. Tests Requeridos

> `apps/journey` está EXENTA de tests unit (PR #306, cross-ref en
> `.claude/rules/journey-rooms.md` → `.claude/rules/astro-landing.md`):
> es Three.js vanilla sin componentes testeables por Vitest/happy-dom de
> forma útil. La verificación de este plan es **typecheck + Biome +
> build + smoke visual/perf**, NUNCA Vitest ni Playwright del harness
> `tests/app/` (ese módulo cubre las 6 apps Astro con niche, no
> `apps/journey`).

## 6.A. TDD Flows

N/A — sin lógica pura nueva en `src/lib/` que amerite TDD (los cambios
son geometría 3D, estado de motor y wiring de interactables dentro de
`apps/journey/src/engine/`).

## 6.B. Unit Tests (Vitest)

N/A — exención de la app (ver nota arriba). Si en el futuro se decide
extraer lógica pura (ej. `resolveEmptySeats(spots, powered)` como
función testeable fuera de `officeLayout`), sería una mejora posterior,
fuera de alcance de este plan.

## 6.C. Typecheck

- `pnpm --filter @portfolio/journey exec astro check` — 0 errores.
- `pnpm --filter @portfolio/journey exec tsc --noEmit` (si el script
  existe separado de `astro check`; si no, `astro check` ya cubre TS).
- Biome: `pnpm exec biome check apps/journey` (o `biome check .` desde
  la raíz) — 0 errores/warnings nuevos.

## 6.D. Tests E2E / Smoke visual (reemplaza Playwright para esta app)

Cada feature (A-D) tiene su propia lista de verificación manual/scripted
en su capítulo (`02` a `05`). Consolidado aquí como checklist único de
smoke antes de cerrar el plan (Parte B de la sección 11):

| # | Escenario | AC cubiertos |
|---|-----------|---------------|
| 1 | Sentarse en silla vacía + levantarse, en 2 salas con `officeLayout` | AC-1, AC-2 |
| 2 | Silla con NPC no ofrece "sentarse" | AC-3 |
| 3 | Sentarse en un pupitre vacío del `aula` | AC-4 |
| 4 | Sentado, cruzar de sala → llega de pie a la sala nueva | AC-5 |
| 5 | Pilar centrado visualmente en `aula` y en 1 sala más | AC-6 |
| 6 | Libro legible de frente al entrar | AC-7 |
| 7 | Libro visible (portada/lomo) rodeándolo por detrás | AC-8 |
| 8 | Libro con volumen (no lámina) en cualquier ángulo | AC-9 |
| 9 | Contorno de `wallArt` alineado en 2 salas distintas | AC-10 |
| 10 | Cruce de puerta: abre, warp, aparece en la sala siguiente, cierra | AC-11 |
| 11 | Tramo entre salas sin muros/techo de pasillo visibles | AC-12, AC-13 |
| 12 | Puerta cerrada e interactuable tras un cruce previo | AC-14 |

Método sugerido (mismo patrón usado en el cierre C15 de
`journey-salas-estandar`): script Python + Playwright headless/headed
contra `pnpm --filter @portfolio/journey dev` (puerto 4327), leyendo
`window.__journeyDebug` para posición/pose del jugador y draw calls, más
capturas de pantalla en los puntos clave (silla, pilar, cuadro, puerta).
No se commitea el script (vive en `./tmp/`, efímero).
