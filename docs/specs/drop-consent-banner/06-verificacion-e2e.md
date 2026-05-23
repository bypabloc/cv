# 06 - Verificacion E2E iterativa (fase final)

> [README](README.md) -> [01](01-contexto-y-decision.md) ->
> [02](02-flujo-y-archivos.md) -> [03](03-descomposicion.md) ->
> [04](04-commits.md) -> [05](05-paralelizacion-worktrees.md) -> 06 ->
> [07-definition-of-done.md](07-definition-of-done.md)

Cubre la seccion 11 del formato. **Es la ultima fase del plan y el ultimo
commit (commit 10).** Consolida — no sustituye — la verificacion
incremental de cada fase. Es el **gate del PR**: el `git push` y la
creacion del PR ocurren SOLO cuando esta bateria pasa completa en verde.

## Bucle "no parar hasta que funcione"

```
ejecutar bateria
  |
  v
+-----+        falla
| ?   |---------> diagnosticar
+-----+              |
   | verde           v
   v             corregir (edit + verify especifico)
 PR ready           |
                    v
                ejecutar bateria de nuevo
                    |
                    +--> ciclar
```

NO se marca el plan como completado con:
- un comando de la bateria fallando
- un test rojo (unit o E2E)
- coverage < 80% per-file en archivos modificados
- `rg` reportando una keyword del barrido

## Parte A — Refactor de tests (cero residuos)

### A.1 — Cero referencias en source

Barrido global con `rg`. Las 10 keywords del plan NO deben aparecer en
ningun archivo de `apps/`, `packages/` ni `tests/` (excluyendo `dist/`,
`node_modules/` y `docs/specs/`):

```bash
rg -l \
  -e 'CookieBanner' \
  -e 'cookie-consent' \
  -e 'cf_consent' \
  -e 'cf_track' \
  -e 'REOPEN_BANNER_EVENT' \
  -e 'CONSENT_CHANGED_EVENT' \
  -e 'hasTrackingConsent' \
  -e 'isTrackingForced' \
  -e 'cookieBanner' \
  -e 'manageConsent' \
  -g '!dist' \
  -g '!node_modules' \
  -g '!docs/specs' \
  apps packages tests
```

**Esperado**: salida vacia (`exit 0` con 0 lineas). Si aparece algo,
ABRIR ese archivo, eliminar la referencia, re-ejecutar.

> Excepcion permitida: `docs/specs/drop-consent-banner/*.md` SI menciona
> las keywords porque es el plan que las elimina. El `-g '!docs/specs'`
> las excluye.

### A.2 — Cero referencias en builds

El barrido de produccion: ninguna `apps/*/dist/` contiene el banner ni
referencias a `cookie-consent` despues de `pnpm run build`. Aplica DESPUES
de la Parte B paso B6.

```bash
rg -l \
  -e 'CookieBanner' \
  -e 'cookie-consent' \
  -e 'auto-borran en 60' \
  -e 'auto-delete in 60' \
  -e 'Permitis recolectar' \
  -e 'let us collect' \
  -e 'Gestionar consentimiento' \
  -e 'Manage consent' \
  apps/*/dist
```

**Esperado**: salida vacia.

### A.3 — Cero test files huerfanos

- `packages/ui/tests/unit/cookie-consent.test.ts` no existe.
- `tests/feature/tracking/consent.spec.ts` no existe.

```bash
ls packages/ui/tests/unit/cookie-consent.test.ts 2>&1
ls tests/feature/tracking/consent.spec.ts 2>&1
```

**Esperado**: ambos comandos exit con "No such file or directory".

## Parte B — Bateria de comandos reales (E2E completa)

Orden estricto, no saltear. Cada paso debe pasar antes del siguiente. Si
falla, ENTRAR AL BUCLE (Parte A arriba).

### B0 — install limpio

```bash
pnpm install
```

**Esperado**: exit 0, sin warnings de `--allow-builds`, lockfile sin
cambios.

### B1 — lint + format

```bash
pnpm exec biome check .
```

**Esperado**: exit 0, 0 errors. (Warnings tolerados solo si son los que
ya existen pre-plan; el plan no introduce ninguno.)

### B2 — typecheck TypeScript

```bash
pnpm exec tsc --noEmit
```

**Esperado**: exit 0. Tras eliminar `cookieBanner` del schema y
`manageConsent` del sub-schema `footer`, ningun `t.components.*` debe
romper.

### B3 — astro check (typecheck Astro)

```bash
pnpm exec astro check
```

**Esperado**: exit 0. Si rompe por `Property 'cookieBanner' does not
exist`, es porque T4 olvido eliminar el uso del prop — arreglar y
re-ejecutar.

### B4 — unit tests con coverage

```bash
pnpm exec vitest run --coverage
```

**Esperado**: exit 0. Coverage **per-file >= 80%** en TODOS los archivos
modificados:

- `packages/ui/src/lib/track-event.ts`
- `packages/ui/src/components/TrackingPixel.astro`
- `packages/ui/src/components/Footer.astro`
- `packages/ui/src/index.ts`
- `packages/app-shared/src/layouts/SitePageLayout.astro`
- `packages/content/src/schemas.ts`

Si algun archivo cae < 80% per-file, agregar test puntual o eliminar
codigo no cubierto (preferir eliminar — el plan ya es de simplificacion).

### B5 — build estatico de las 6 apps

```bash
pnpm run build
```

**Esperado**: las 6 apps construyen sin error. Inspeccionar el output:

```bash
ls apps/generic/dist/index.html
ls apps/hub/dist/index.html
ls apps/fintech/dist/index.html
ls apps/architect/dist/index.html
ls apps/leader/dist/index.html
ls apps/vibe/dist/index.html
```

### B6 — barrido `rg` sobre dist (re-ejecutar A.2 aqui)

Ver Parte A.2 arriba. Es despues del build.

### B7 — preview visual (manual, 1 minuto por app)

```bash
pnpm --filter @portfolio/generic exec astro preview --port 4321 &
PID=$!
sleep 2
# Abrir en browser: http://localhost:4321/
# Verificar visual: NO hay banner abajo, hay Footer normal, hay copyright + linkedin + github
# (sin "Gestionar consentimiento")
kill $PID
```

Repetir para `@portfolio/hub`, `@portfolio/fintech`, `@portfolio/architect`,
`@portfolio/leader`, `@portfolio/vibe`. (En el hub validar
`/`, `/en/` y `/contact`.)

### B8 — Playwright E2E contra stack local

```bash
# Stack arriba (Docker compose con dev server HMR)
python3 devtools/run.py docker up --env=local

# Esperar a que las 6 apps respondan (devtools docker ps lo muestra)
python3 devtools/run.py docker ps --env=local

# Suite Playwright completa contra el stack
python3 devtools/run.py test_runner --module=feature --type=feature --env=local
```

**Esperado**: todos los tests pasan. Si falla:

- Si falla "el banner no aparece" en un test viejo: el test no se
  actualizo en commit 9. Corregir.
- Si falla "POST /track no llega" en cold start: revisar que
  `TrackingPixel.astro` emita `page_load` sin esperar consent (commit 3
  debe haber quitado el listener).
- Si falla "manage-consent no existe": el test viejo asumia el boton.
  Corregir el spec.
- Si falla un test del funnel de contacto: `?cf_track=force` debe haber
  sido removido (commit 9).

### B9 — bajar stack (opcional)

```bash
python3 devtools/run.py docker down --env=local
```

## Reglas de cierre

- TODOS los pasos B0-B8 deben pasar en una sola ejecucion en cadena, sin
  comentarios de "esto ya lo verifique antes".
- Si entre paso N y paso N+1 hubo que hacer una correccion, **re-ejecutar
  TODA la bateria desde B0** (no incrementalmente). El motivo: una
  correccion puede introducir un side-effect que solo se ve corriendo
  todo.
- El push (`git push origin feature/drop-consent-banner`) y la creacion
  del PR (`gh pr create --base dev --head feature/drop-consent-banner`)
  ocurren SOLO despues de B8 verde.

## Diagnostico de fallas comunes

| Sintoma | Causa probable | Fix |
|---------|----------------|-----|
| `astro check`: `Property 'cookieBanner' does not exist` | T4 dejo un `t.components.cookieBanner` en alguna pagina hub | Buscar con `grep -rn "components.cookieBanner" apps packages -l` y eliminar |
| `astro check`: `Property 'manageConsent' does not exist` | T3b dejo un `strings.manageConsent` en Footer.astro | Eliminar la referencia residual |
| `vitest`: `Cannot find module '../lib/cookie-consent'` | Tests que importaban el modulo eliminado | Eliminar el import + bloque de test |
| Playwright: `expect(...).toHaveCount(0)` falla con count 1 | El banner sigue mostrandose porque un commit anterior no se aplico | `git log --oneline` en la rama; verificar que el commit T1/T4 esta presente |
| Playwright: el POST /track no llega | El nuevo test no espera bien o `TrackingPixel` no emite en cold start | Verificar que `TrackingPixel.astro` no tiene `if (consent)` previo al `trackEvent` |
| `pnpm run build` falla solo en hub | T4 olvido uno de los 3 archivos (`/`, `/en/`, `/contact`) | Buscar `import CookieBanner` en `apps/hub/src/pages/` |
| Coverage < 80% en `track-event.ts` | Sobra codigo no cubierto | Verificar que se eliminaron las 4 constantes y 2 funciones; lo que quede sin test es codigo muerto |
| Coverage < 80% en `Footer.astro` | El script viejo tenia tests indirectos via consent.spec.ts (E2E); ahora pkg-ui no lo cubre | Astro components no se cubren por unit; el coverage del 80% aplica a `.ts` cambiados — confirmar que el reporte excluye `.astro` o aceptar |

## Gate del PR (recordatorio)

```
verde toda la bateria
  ->  git push origin feature/drop-consent-banner
  ->  gh pr create --base dev --head feature/drop-consent-banner \
        --title "refactor(ui): elimina banner GDPR y deja tracking always-on" \
        --body "<seccion Problema/Solucion/Como probar/TODO>"
  ->  Esperar CI del repo (quality-gates + e2e-tests)
  ->  CI verde -> gh pr merge --merge --delete-branch
```

## Navegacion

- Anterior: [05-paralelizacion-worktrees.md](05-paralelizacion-worktrees.md)
- Siguiente: [07-definition-of-done.md](07-definition-of-done.md)
