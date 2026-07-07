# 11. Verificación E2E iterativa (fase final) + 12. Definition of Done

## Parte A — Refactor de tests

N/A en sentido estricto (la app no tiene tests unit — ver
[06-tests-requeridos.md](06-tests-requeridos.md)). Verificación
equivalente:

- Barrido `rg -l "mergedBoxes\(" apps/journey/src/engine/rooms/props.ts`
  para confirmar que el `wallArt` ya no usa `mergedBoxes` directo en su
  marco (feature C).
- Barrido `rg -l "openDoor" apps/journey/src` para confirmar que ya no
  queda ninguna referencia al método viejo si se decide renombrarlo (o
  que sigue existiendo como paso interno de `crossDoor`, según cómo se
  implemente — documentar la decisión real en el commit).
- Confirmar que ningún archivo de sala quedó con una `officeLayout({...})`
  sin el nuevo `roomIndex`/`state` (typecheck ya lo garantiza si son
  campos obligatorios).

## Parte B — Batería de comandos reales

Ejecutar en orden, sin parar hasta que TODO pase (bucle
ejecutar → si falla, diagnosticar → corregir → re-ejecutar):

```bash
# 1. Lint + format
pnpm exec biome check apps/journey

# 2. Typecheck
pnpm --filter @portfolio/journey exec astro check
pnpm --filter @portfolio/journey exec tsc --noEmit

# 3. Build estatico
pnpm --filter @portfolio/journey run build

# 4. Build del resto del monorepo (packages compartidos no deben romperse)
pnpm run build

# 5. Dev server para el smoke visual
pnpm --filter @portfolio/journey run dev   # puerto 4327
```

Con el dev server arriba, recorrer el checklist de smoke de
[06-tests-requeridos.md](06-tests-requeridos.md) (12 escenarios,
AC-1 a AC-14). Método sugerido: script Python + Playwright
headless/headed (patrón ya usado en el cierre C15 de
`journey-salas-estandar`), leyendo `window.__journeyDebug` para
posición/pose/draw-calls y capturando pantallas en los puntos clave.
El script vive en `./tmp/` (efímero, no se commitea).

Medición de performance (no debe haber regresión):

```js
// en devtools del navegador, o desde el script headless
window.__journeyDebug.info.render.calls // <100 por sala, ver journey-rooms.md
```

Ninguno de los 4 features agrega geometría suficiente para acercarse al
límite (feature C suma 1 draw call por sala con `wallArt`; feature B
suma 1 draw call por sala vía el `cover` del libro; features A y D no
agregan geometría nueva de bulto — solo interactables y lógica de
estado).

## Parte C — Verificación de despliegue REAL

N/A para este plan: `apps/journey` es local-first (ver
[README.md](README.md), decisión 4) — no se hace deploy como parte del
cierre de este plan. El "listo" de este plan es: batería de la Parte B
en verde + confirmación visual del usuario en
`pnpm --filter @portfolio/journey dev`. Si en una sesión futura se
decide llevar estos cambios a `dev`/producción, esa es una decisión
explícita y separada del usuario (push + PR + deploy), no automática al
cerrar este plan.

## Definition of Done

**Pre-implementación**:

- [ ] Los 14 AC están numerados y cada uno es verificable con un
      escenario de smoke concreto (tabla en 06-tests-requeridos.md).
- [ ] Confirmada la ubicación exacta de cada fix (líneas citadas en los
      capítulos 02-05) contra el estado actual del código antes de
      escribir el primer diff.

**Definition of Done**:

- [ ] Los 14 AC tienen su escenario de smoke ejecutado y pasando.
- [ ] `astro check` + `tsc --noEmit` sin errores.
- [ ] `biome check` sin errores/warnings nuevos.
- [ ] `pnpm --filter @portfolio/journey run build` exitoso.
- [ ] `pnpm run build` (monorepo completo) exitoso — packages
      compartidos no rotos.
- [ ] Draw calls por sala siguen <100 en al menos 3 salas medidas
      (`aula` + 2 con `officeLayout`/`wallArt`).
- [ ] Verificación visual manual/scripted de los 12 escenarios de la
      tabla de smoke.
- [ ] El usuario probó el resultado en `pnpm --filter @portfolio/journey
      dev` y confirmó antes de cualquier push/PR.
- [ ] Carpeta `docs/specs/journey-puerta-sillas-pilar/` eliminada en el
      commit de cierre (tras la confirmación del usuario, no antes).
