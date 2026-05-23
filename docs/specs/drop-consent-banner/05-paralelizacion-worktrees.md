# 05 - Paralelizacion con git worktrees

> [README](README.md) -> [01](01-contexto-y-decision.md) ->
> [02](02-flujo-y-archivos.md) -> [03](03-descomposicion.md) ->
> [04](04-commits.md) -> 05 -> [06](06-verificacion-e2e.md)

Cubre la seccion 10 del formato. Define la **base secuencial** (commits que
todos los worktrees necesitan o que tocan archivos transversales), la tabla
de fases **worktree-safe** (archivos disjuntos), lo que NO se paraleliza
y como lanzar cada worktree.

## Base secuencial obligatoria

Estos commits van en la rama principal del plan antes de abrir worktrees.
NO se paralelizan porque o son el plan en si o son la unica tarea actual.

| # | Commit | Por que es base |
|---|--------|------------------|
| 1 | `docs(specs): documenta plan drop-consent-banner` | Crea la carpeta del plan; todos los worktrees parten de aqui. |

Tambien forman parte de la "base operativa" pero NO se commitean en la rama
principal antes de abrir worktrees — son los **puntos de sincronizacion**
intermedios:

- Despues del commit 5 (T4: layout + paginas hub), las claves
  `cookieBanner` / `manageConsent` quedan dead code en YAMLs / schema; el
  commit 7 (T5) las elimina. **Sincronizar todos los worktrees a la rama
  principal antes del commit 6** (asi el resto del trabajo paralelo ya
  esta fusionado y la limpieza no rompe nada).

## Tabla de fases worktree-safe

| Fase | Worktree | Commits | Archivos exclusivos | Paralelizable con |
|------|----------|---------|---------------------|-------------------|
| 1 | `wt-track-event` | 2 (T2), 8 (T7 parcial: track-event tests) | `packages/ui/src/lib/track-event.ts`, `packages/ui/tests/unit/track-event.test.ts`, `packages/ui/src/index.ts` (solo el bloque exports cookie-consent y hasTrackingConsent/isTrackingForced) | `wt-ui-cleanup`, `wt-hub-layout` |
| 2 | `wt-ui-cleanup` | 3 (T3a), 4 (T3b) | `packages/ui/src/components/TrackingPixel.astro`, `packages/ui/src/components/Footer.astro` | `wt-track-event`, `wt-hub-layout` |
| 3 | `wt-hub-layout` | 5 (T4) | `packages/app-shared/src/layouts/SitePageLayout.astro`, `apps/hub/src/pages/index.astro`, `apps/hub/src/pages/en/index.astro`, `apps/hub/src/pages/contact.astro` | `wt-track-event`, `wt-ui-cleanup` |

Las 3 fases tocan **archivos disjuntos** (verificado contra
[03-descomposicion.md](03-descomposicion.md) y [02-flujo-y-archivos.md](02-flujo-y-archivos.md)).

### Punto de sincronizacion 1 (despues de fase 1-3)

Cuando los 3 worktrees terminaron y mergearon a `feature/drop-consent-banner`,
en la rama principal se hacen estos commits **secuenciales**:

| # | Commit | Tarea | Por que NO paraleliza |
|---|--------|-------|------------------------|
| 6 | `refactor(ui): elimina CookieBanner.astro y cookie-consent.ts` | T1 | Depende de los 3 worktrees anteriores (no quedan consumidores). Toca `packages/ui/src/index.ts` que ya fue modificado en commit 2. |
| 7 | `refactor(content): elimina claves cookieBanner y footer.manageConsent` | T5 | Depende del commit 5 (paginas hub ya no leen las claves) y del commit 6 (Footer + CookieBanner no existen). Cambio breaking en `ComponentsStrings`. |

Estos 2 NO se paralelizan: comparten dependencia con T1+T5 y son
secuenciales por interface-stability (T5 rompe `ComponentsStrings`, T1
borra el modulo).

### Fase 4 — tests (paralelizable)

| Fase | Worktree | Commit | Archivos exclusivos | Paralelizable con |
|------|----------|--------|---------------------|-------------------|
| 4a | `wt-unit-tests` | 8 (T7) | `packages/ui/tests/unit/scroll-depth.test.ts`, `packages/ui/tests/unit/click-tracking.test.ts`, `packages/app-shared/tests/unit/lib/build-strings.test.ts` | `wt-e2e-tests` |
| 4b | `wt-e2e-tests` | 9 (T6) | `tests/feature/tracking/consent.spec.ts` (borrar), `tests/feature/tracking/track-pageload.spec.ts`, `tests/feature/contact/contact-funnel.spec.ts`, `tests/feature/contact/contact-session-link.spec.ts` | `wt-unit-tests` |

Ambos worktrees parten del commit 7 (claves YAML/schema ya borradas) y
mergean a `feature/drop-consent-banner` antes del commit 10.

### Punto de sincronizacion 2 (despues de fase 4)

Commit 10 secuencial en la rama principal (bateria completa + limpieza del
plan). NO se paraleliza:

| # | Commit | Por que NO paraleliza |
|---|--------|------------------------|
| 10 | `chore(plan): cierra drop-consent-banner y elimina la carpeta del plan` | Es la verificacion E2E final + `git rm -r docs/specs/drop-consent-banner/`. Necesita TODO mergeado para que la bateria valide el estado real. |

## Lo que NO se paraleliza

- **Commit 1** (plan): es base obligatoria.
- **Commit 6 (T1)** y **commit 7 (T5)**: secuenciales por
  interface-stability (rompen interfaces que otros consumen).
- **Commit 10**: gate final del PR.
- **Configuracion central** (NO hay en este plan): no se tocan
  `astro.config.ts`, `biome.json`, `tsconfig.json`, `vitest.config.ts`,
  `package.json`, lockfile. Si un worktree pretende tocar uno, sale del
  scope del plan.
- **La grilla de comandos** (verify-before-done.md) NO se paraleliza:
  cada verificacion la corre el worktree dueno del archivo.

## Como lanzar cada worktree

Convencion: `../portfolio-wt-<nombre>` (al mismo nivel que el repo, no
dentro). Si la maquina tiene poco disco, usar `~/.cache/portfolio-wt-*` y
ajustar.

### Worktree wt-track-event (commit 2 + parte del 8)

```bash
# Desde la raiz del repo, parado en feature/drop-consent-banner
git worktree add ../portfolio-wt-track-event feature/drop-consent-banner
cd ../portfolio-wt-track-event
git checkout -b wt-track-event
pnpm install   # comparte node_modules via pnpm store
# trabajar commit 2; al terminar:
#   git push origin wt-track-event
#   gh pr create --base feature/drop-consent-banner --head wt-track-event
#   o merge directo: git checkout feature/drop-consent-banner && git merge --no-ff wt-track-event
cd -
git worktree remove ../portfolio-wt-track-event
```

### Worktree wt-ui-cleanup (commits 3 + 4)

```bash
git worktree add ../portfolio-wt-ui-cleanup feature/drop-consent-banner
cd ../portfolio-wt-ui-cleanup
git checkout -b wt-ui-cleanup
pnpm install
# commits 3 y 4 aqui
```

### Worktree wt-hub-layout (commit 5)

```bash
git worktree add ../portfolio-wt-hub-layout feature/drop-consent-banner
cd ../portfolio-wt-hub-layout
git checkout -b wt-hub-layout
pnpm install
# commit 5
```

### Worktree wt-unit-tests (commit 8)

```bash
# IMPORTANTE: parte de feature/drop-consent-banner DESPUES del commit 7.
# Si todavia no esta el commit 7, esperar.
git worktree add ../portfolio-wt-unit-tests feature/drop-consent-banner
cd ../portfolio-wt-unit-tests
git checkout -b wt-unit-tests
pnpm install
# commit 8
```

### Worktree wt-e2e-tests (commit 9)

```bash
git worktree add ../portfolio-wt-e2e-tests feature/drop-consent-banner
cd ../portfolio-wt-e2e-tests
git checkout -b wt-e2e-tests
pnpm install
# commit 9
```

## Tabla de colisiones (verificacion)

Cruz roja = NO se paraleliza por colision. Marca verde = OK.

|              | track-event | ui-cleanup | hub-layout | unit-tests | e2e-tests |
|--------------|-------------|------------|------------|------------|-----------|
| `track-event.ts`         | X | OK | OK | OK | OK |
| `track-event.test.ts`    | X | OK | OK | OK | OK |
| `index.ts` (pkg ui)      | X | OK | OK | OK | OK |
| `TrackingPixel.astro`    | OK | X | OK | OK | OK |
| `Footer.astro`           | OK | X | OK | OK | OK |
| `SitePageLayout.astro`   | OK | OK | X | OK | OK |
| `hub/pages/*.astro`      | OK | OK | X | OK | OK |
| `scroll-depth.test.ts`   | OK | OK | OK | X | OK |
| `click-tracking.test.ts` | OK | OK | OK | X | OK |
| `build-strings.test.ts`  | OK | OK | OK | X | OK |
| `tracking/*.spec.ts`     | OK | OK | OK | OK | X |
| `contact/*.spec.ts`      | OK | OK | OK | OK | X |

Toda celda con X es exclusiva al worktree de su columna. Sin colisiones
cruzadas.

## Limite practico

5 worktrees concurrentes maximo (track-event, ui-cleanup, hub-layout
juntos; despues unit-tests + e2e-tests juntos). Dentro del limite del
proyecto (5-7 agentes concurrentes).

## Anti-patrones

- Abrir un worktree antes del commit 1 (no hay carpeta del plan donde
  documentar el progreso parcial).
- Abrir wt-unit-tests / wt-e2e-tests antes del commit 7 (sus tests asumen
  el shape recortado y van a romper).
- Tocar `packages/ui/src/index.ts` en un worktree distinto al de
  `wt-track-event` despues del commit 2 — el commit 6 lo revisa y deja
  limpio, pero entre 2 y 6 cualquier edicion paralela rompe el merge.
- Lanzar Playwright concurrente desde dos worktrees contra el mismo
  `--env=local` (compiten por el puerto 9970). Si hace falta paralelo de
  E2E, cada uno levanta su stack con un puerto distinto (env custom) o
  uno espera al otro.

## Navegacion

- Anterior: [04-commits.md](04-commits.md)
- Siguiente: [06-verificacion-e2e.md](06-verificacion-e2e.md)
