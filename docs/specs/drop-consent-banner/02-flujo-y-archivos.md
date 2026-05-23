# 02 - Flujo, ER, tests, archivos

> [README](README.md) -> [01](01-contexto-y-decision.md) -> 02 ->
> [03-descomposicion.md](03-descomposicion.md)

Cubre las secciones 4-7 del formato de plan: diagrama de flujo (antes/despues),
ER (N/A), tests requeridos por tipo, lista de archivos afectados con
comando de verificacion por archivo.

## 4. Diagrama de flujo (Antes y Despues)

### Antes

```
                            [Visitante]
                                 |
                                 v
            +----------------------------------------+
            |  SitePageLayout monta:                  |
            |    <CookieBanner strings=...>           |
            |    <TrackingPixel apiEndpoint=...>      |
            |    <Footer ... boton manage-consent>    |
            +----------------------------------------+
                                 |
                                 v
                  +------------------------------+
                  |  CookieBanner.astro init:    |
                  |    readConsent()             |
                  +------------------------------+
                                 |
        +------------------------+------------------------+
        |                                                 |
        | null (primera visita)                           | 'accepted' o 'rejected'
        v                                                 v
   [banner visible]                              [banner hidden]
        |                                                 |
        | user click Aceptar / Rechazar                   v
        v                                  TrackingPixel evalua:
   writeConsent(...)                       hasTrackingConsent()?
        |                                                 |
        | dispatch consent-changed              +---------+---------+
        v                                       | true              | false
   TrackingPixel listener:                      v                   v
   if detail.value=='accepted':            trackEvent(page_load)  return false
       emitPageLoad()                      -> POST /track         -> 0 eventos
                                           [DynamoDB tracking]    [silencio]

        Para clicks / scroll / SPA / page_exit / contact_*:
        cada trackEvent() pasa por hasTrackingConsent() primero.

        QA bypass: ?cf_track=force -> isTrackingForced() = true
        -> hasTrackingConsent() = true -> evento emitido.
```

### Despues

```
                            [Visitante]
                                 |
                                 v
            +----------------------------------------+
            |  SitePageLayout monta:                  |
            |    <TrackingPixel apiEndpoint=...>      |
            |    <Footer ... sin manage-consent>      |
            +----------------------------------------+
                                 |
                                 v
                  +------------------------------+
                  |  TrackingPixel script:       |
                  |    configureTracking(...)    |
                  |    emitPageLoad()            |
                  |      (requestIdleCallback)   |
                  +------------------------------+
                                 |
                                 v
                       trackEvent(page_load)
                                 |
                                 v
                       sendBeaconPayload(...)
                                 |
                                 v
                       POST /track
                       [DynamoDB tracking]

        Para clicks / scroll / SPA / page_exit / contact_*:
        cada trackEvent() emite directo, sin gating.

        Sin bypass QA. Tests E2E usan page.route('**/track', fulfill)
        cuando quieren capturar/silenciar el POST.
```

Cambios netos en el flujo:

- Se elimina la rama `null -> banner visible -> writeConsent -> dispatch`.
- Se elimina el evaluador `hasTrackingConsent()` entre `trackEvent` y
  `sendBeacon`.
- Se elimina el listener `portfolio:consent-changed` del `TrackingPixel`.
- Se elimina el boton "Gestionar consentimiento" del Footer y su
  despachador `REOPEN_BANNER_EVENT`.
- Se elimina el bypass `?cf_track=force` (innecesario sin gating).
- El `cf_session` en `localStorage` (UUID) se mantiene tal cual.

## 5. Diagrama ER

`N/A` — no hay cambios en data persistida. El CV (content collections,
YAML) no cambia salvo borrar las claves i18n de UI (`cookieBanner`,
`manageConsent`) que NO son entidades, son strings de UI; el DynamoDB
`tracking` no cambia; Neon no cambia.

## 6. Tests requeridos

### 6.A. TDD Flows (logica nueva)

No hay logica nueva. Lo que se hace es **simplificar**. Los TDD flows
relevantes son `WHEN <accion> THEN <resultado>` que prueban la nueva
semantica:

- **TDD-1**: WHEN se invoca `trackEvent(EVENT_TYPES.PAGE_LOAD)` con
  `localStorage` limpio y sin query params, THEN `sendBeacon` se llama con
  el payload esperado [AC-2]
- **TDD-2**: WHEN el `TrackingPixel.astro` script corre tras
  `DOMContentLoaded`, THEN `trackEvent` se invoca exactamente 1 vez para
  `page_load` [AC-2]
- **TDD-3**: WHEN se navega via `astro:after-swap`, THEN `trackEvent` se
  invoca con `event_type_id = SPA_NAVIGATION` [AC-3]
- **TDD-4**: WHEN ejecuto `document.querySelector('[data-testid="manage-consent"]')`
  tras renderizar el Footer, THEN devuelve `null` [AC-4]
- **TDD-5**: WHEN ejecuto `document.getElementById('cookie-banner')` tras
  renderizar el layout, THEN devuelve `null` [AC-1]

Aplicacion: cada uno se materializa en un test unit o E2E concreto en la
seccion 6.B / 6.D.

### 6.B. Unit tests (Vitest)

**Path mirroring** ya existente:

- `packages/ui/src/lib/track-event.ts` <-> `packages/ui/tests/unit/track-event.test.ts`
- `packages/ui/src/lib/scroll-depth.ts` <-> `packages/ui/tests/unit/scroll-depth.test.ts`
- `packages/ui/src/lib/click-tracking.ts` <-> `packages/ui/tests/unit/click-tracking.test.ts`
- `packages/ui/src/lib/cookie-consent.ts` <-> `packages/ui/tests/unit/cookie-consent.test.ts` **(borrar)**
- `packages/app-shared/src/lib/build-strings.ts` <-> `packages/app-shared/tests/unit/lib/build-strings.test.ts`

**Acciones concretas**:

- **Eliminar completo**: `packages/ui/tests/unit/cookie-consent.test.ts`
  (sin reemplazo, ya que tampoco existe el modulo).
- **`track-event.test.ts`** — eliminar:
  - El describe / bloques `hasTrackingConsent`, `isTrackingForced`,
    `gating`, `QA flag`, `cf_track`, `cf_consent`.
  - Cualquier `beforeEach` que setee `localStorage.setItem('cf_consent', ...)`
    o mockee `URLSearchParams`.
  - El test que valida `trackEvent` retornando `false` sin consentimiento.
  - Conservar tests de: `buildTrackPayload` (shape), `generateEventId`
    (forma + unicidad), `getSessionId` (lectura + creacion en localStorage
    via `cf_session`), `sendBeaconPayload` (con y sin `navigator.sendBeacon`,
    fallback fetch), `configureTracking` / `resetTrackingConfig`,
    `trackEvent` (caso happy: payload enviado, retorno `true`; caso sin
    config: retorno `false`).
- **`scroll-depth.test.ts`** — eliminar setup
  `localStorage.setItem('cf_consent', 'accepted')` que precede cada test;
  los tests deben pasar sin ese setup porque `trackEvent` ya no requiere
  consentimiento.
- **`click-tracking.test.ts`** — idem.
- **`build-strings.test.ts`** — eliminar assertions sobre las claves
  `t.components.cookieBanner.*` y `t.components.footer.manageConsent`.

**Coverage**: `track-event.ts` queda con menos lineas (eliminamos 2
funciones + 4 constantes), pero la cobertura per-file sigue >= 80% sobre
las restantes (`configureTracking`, `resetTrackingConfig`, `generateEventId`,
`getSessionId`, `buildTrackPayload`, `sendBeaconPayload`, `trackEvent`).

### 6.C. Typecheck

- `pnpm exec tsc --noEmit` — debe pasar tras eliminar:
  - el bloque `cookieBanner` del schema Zod en
    `packages/content/src/schemas.ts:392-399`
  - la clave `manageConsent` en el sub-schema `footer` (linea aprox 373-377,
    a confirmar al editar)
  - los exports de `cookie-consent` en `packages/ui/src/index.ts:14-23`

- `pnpm exec astro check` — debe pasar tras eliminar imports:
  - `SitePageLayout.astro:26` (`import CookieBanner ...`)
  - `apps/hub/src/pages/index.astro:5`, `en/index.astro:5`,
    `contact.astro:8`

Cualquier referencia residual a `t.components.cookieBanner.*` o
`t.components.footer.manageConsent` rompe `astro check` (`Property
'cookieBanner' does not exist on type 'ComponentsStrings'`) — eso garantiza
que no queda ningun lugar olvidado.

### 6.D. E2E (Playwright)

La suite vive en `tests/feature/`. Sigue siendo opt-in en CI por costo
(corre en pre-push hook localmente).

**Acciones**:

- **Eliminar completo**: `tests/feature/tracking/consent.spec.ts` (8 tests
  de AC-1..AC-8 del banner viejo). Sin reemplazo: los AC del banner ya no
  aplican.
- **`tests/feature/tracking/track-pageload.spec.ts`**: quitar `?cf_track=force`
  de todas las URLs (`subdomainUrl()/?cf_track=force` -> `subdomainUrl()/`,
  etc.). Quitar el ultimo test que valida "sin consent y sin flag NO emite"
  (lineas 178-... aprox, a confirmar al editar) porque la semantica
  cambia. Agregar un nuevo test que valide AC-1 + AC-4: el banner y el
  boton manage-consent NO estan en el DOM.
- **`tests/feature/contact/contact-funnel.spec.ts`**: quitar `?cf_track=force`
  de las URLs (lineas 86, 108, 116, ...).
- **`tests/feature/contact/contact-session-link.spec.ts`**: quitar
  `?cf_track=force` (lineas 153, 188-189). El bloque que limpia
  `localStorage.cf_consent` (linea 189) se elimina (ya no existe la key).

Nuevo test en `track-pageload.spec.ts` (esbozo):

```ts
test('Given carga inicial Then NO existe el banner ni el boton manage-consent [AC-1, AC-4]', async ({ page }) => {
  await page.goto(`${subdomainUrl()}/`, { waitUntil: 'domcontentloaded' })
  await expect(page.getByRole('dialog', { name: /Consentimiento de analytics|Analytics consent/i })).toHaveCount(0)
  await expect(page.locator('[data-testid="manage-consent"]')).toHaveCount(0)
})

test('Given carga inicial sin opt-in Then se emite page_load automaticamente [AC-2]', async ({ page }) => {
  await disableSendBeacon(page)
  const captured = await captureTrackRequests(page)
  await page.goto(`${subdomainUrl()}/`, { waitUntil: 'domcontentloaded' })
  await expect.poll(() => captured.length, { timeout: 5000 }).toBe(1)
  expect(captured[0].event_type_id).toBe(PAGE_LOAD_TYPE)
})
```

Las helpers `disableSendBeacon`, `captureTrackRequests` y la constante
`PAGE_LOAD_TYPE` ya existen en `consent.spec.ts`; se mueven a una helper
compartida o se duplican en `track-pageload.spec.ts` (preferir mover a
`tests/feature/fixtures/track-helpers.ts` si no existe ya — al editar se
decide). El refactor de las helpers NO es bloqueante: el plan permite
duplicarlas inline si la helper compartida no existe.

## 7. Archivos afectados

### Eliminar

- `packages/ui/src/components/CookieBanner.astro`
  - Verificar: `pnpm exec astro check` (sin imports rotos) + `rg -l "CookieBanner.astro" apps packages` (0 resultados)
- `packages/ui/src/lib/cookie-consent.ts`
  - Verificar: `pnpm exec tsc --noEmit` (sin imports rotos) + `rg -l "cookie-consent" apps packages` (0 resultados excluyendo tests borrados)
- `packages/ui/tests/unit/cookie-consent.test.ts`
  - Verificar: `pnpm --filter @portfolio/ui exec vitest run` (la suite no falla por archivo faltante)
- `tests/feature/tracking/consent.spec.ts`
  - Verificar: `python3 devtools/run.py test_runner --module=feature --type=feature --env=local` (Playwright no reporta archivo faltante)

### Modificar (frontend source)

- `packages/ui/src/index.ts` — borrar las 2 lineas de `export type` /
  `export` de cookie-consent (lineas 15-23).
  - Verificar: `pnpm exec tsc --noEmit`
- `packages/ui/src/lib/track-event.ts` — borrar `STORAGE_CONSENT`, `QA_FLAG`,
  `QA_FLAG_VALUE`, `CONSENT_ACCEPTED` (constantes), `isTrackingForced()`,
  `hasTrackingConsent()`; `trackEvent()` queda
  `const payload = buildTrackPayload(eventTypeId, props); return sendBeaconPayload(payload)`.
  Actualizar el docstring del modulo (quitar "GATING").
  - Verificar: `pnpm --filter @portfolio/ui exec vitest run track-event`
- `packages/ui/src/components/Footer.astro` — borrar el `<li>` con el
  `<button data-action="reopen-consent">` (lineas 47-55 aprox), el `<script>`
  completo (lineas 60-81 aprox) y el import `REOPEN_BANNER_EVENT`.
  El campo `manageConsent` del `Props.strings` ya no existe (lo elimina T5
  en `schemas.ts`).
  - Verificar: `pnpm exec astro check`
- `packages/ui/src/components/TrackingPixel.astro` — borrar el listener
  `portfolio:consent-changed` (lineas 99-102).
  - Verificar: `pnpm exec astro check` + grep manual del archivo
- `packages/app-shared/src/layouts/SitePageLayout.astro` — borrar el
  `import CookieBanner ...` (linea 26) y el `<CookieBanner ... />` (linea
  138). El prop `strings` que llega al Footer YA no tiene `cookieBanner`
  porque T5 lo elimina del schema.
  - Verificar: `pnpm exec astro check` + `pnpm run build` (de cualquier app
    que use el layout)
- `apps/hub/src/pages/index.astro` — borrar `import CookieBanner` (linea
  5) y `<CookieBanner ... />` (linea 112).
  - Verificar: `pnpm --filter @portfolio/hub run build`
- `apps/hub/src/pages/en/index.astro` — idem (lineas 5, 109).
  - Verificar: `pnpm --filter @portfolio/hub run build`
- `apps/hub/src/pages/contact.astro` — idem (lineas 8, 72).
  - Verificar: `pnpm --filter @portfolio/hub run build`

### Modificar (data + schema)

- `packages/content/src/schemas.ts` — borrar el bloque
  `cookieBanner: z.object({ ... })` (lineas 392-399) y la propiedad
  `manageConsent` dentro del sub-schema `footer` (linea aprox 373-377).
  - Verificar: `pnpm --filter @portfolio/content run typecheck`
- `packages/content/src/data/i18n/elements/elements.es.yaml` — borrar el
  bloque `cookieBanner:` (lineas 132-138) y la clave `manageConsent` del
  bloque `footer` (linea 122).
  - Verificar: `pnpm --filter @portfolio/content exec vitest run` (los
    tests cargan el YAML y Zod lo valida; el shape debe estar sincronizado
    con `schemas.ts`)
- `packages/content/src/data/i18n/elements/elements.en.yaml` — idem
  (mismas lineas aproximadas).
  - Verificar: `pnpm --filter @portfolio/content exec vitest run`

### Modificar (tests existentes)

- `packages/ui/tests/unit/track-event.test.ts` — eliminar bloques de
  gating + flag QA (ver detalle en 6.B).
  - Verificar: `pnpm --filter @portfolio/ui exec vitest run track-event`
- `packages/ui/tests/unit/scroll-depth.test.ts` — eliminar setup de
  `localStorage.cf_consent`.
  - Verificar: `pnpm --filter @portfolio/ui exec vitest run scroll-depth`
- `packages/ui/tests/unit/click-tracking.test.ts` — idem.
  - Verificar: `pnpm --filter @portfolio/ui exec vitest run click-tracking`
- `packages/app-shared/tests/unit/lib/build-strings.test.ts` — eliminar
  assertions sobre `cookieBanner.*` y `footer.manageConsent`.
  - Verificar: `pnpm --filter @portfolio/app-shared exec vitest run build-strings`
- `tests/feature/tracking/track-pageload.spec.ts` — quitar todas las
  apariciones de `?cf_track=force` (lineas 87, 95, 118, 122, 140, 150,
  152, 180 aprox); agregar el nuevo test AC-1+AC-4 + el nuevo test AC-2
  sin flag (ver 6.D).
  - Verificar: `python3 devtools/run.py test_runner --module=feature --type=feature --env=local`
- `tests/feature/contact/contact-funnel.spec.ts` — quitar `?cf_track=force`
  (lineas 86, 108, 116, ...).
  - Verificar: idem
- `tests/feature/contact/contact-session-link.spec.ts` — quitar
  `?cf_track=force` (linea 153) y el bloque que limpia
  `localStorage.cf_consent` (linea 188-189).
  - Verificar: idem

### Crear (carpeta del plan + final)

- `docs/specs/drop-consent-banner/{README.md,01..07}.md` — esta carpeta.
  Se commitea en el commit 1 y se elimina en el commit 10.

## Navegacion

- Anterior: [01-contexto-y-decision.md](01-contexto-y-decision.md)
- Siguiente: [03-descomposicion.md](03-descomposicion.md)
