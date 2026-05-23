# 01 - Contexto, solucion y AC

> [README](README.md) -> 01 -> [02-flujo-y-archivos.md](02-flujo-y-archivos.md)

Cubre las secciones 1-3 del formato de plan: contexto/problema, solucion
propuesta con decisiones, y criterios de aceptacion numerados.

## 1. Contexto / Problema

Hoy, cada vez que un visitante entra al portfolio (cualquiera de las 6 apps:
generic, hub, fintech, architect, leader, vibe), el layout
[SitePageLayout.astro:138](../../../packages/app-shared/src/layouts/SitePageLayout.astro#L138)
monta un `<CookieBanner>` que aparece como dialogo modal abajo del viewport
con el texto:

```
Este sitio usa analytics propios privacy-friendly (sin cookies de terceros,
los datos se auto-borran en 60 dias). ¿Permitis recolectar tu visita para
mejorar el contenido?
[Aceptar] [Rechazar]
```

El banner controla un opt-in GDPR persistido en
`localStorage.cf_consent` (`'accepted' | 'rejected' | null`) cuya unica
funcion practica es **gatear** la emision de eventos en
[packages/ui/src/lib/track-event.ts:111-118](../../../packages/ui/src/lib/track-event.ts#L111-L118):

```ts
export function hasTrackingConsent(): boolean {
  if (isTrackingForced()) return true
  try {
    return localStorage.getItem(STORAGE_CONSENT) === CONSENT_ACCEPTED
  } catch {
    return false
  }
}
```

Si el visitante no acepto (caso por defecto), `trackEvent()` retorna `false`
y el portfolio no envia `POST /track` ni para `page_load`, ni para
`spa_navigation`, ni para clicks, ni para scroll depth, ni para los eventos
del funnel de contacto.

### Hallazgos de exploracion

- El banner se renderea desde 4 lugares: `SitePageLayout.astro` (la unica
  fuente para 5 apps) y 3 paginas del hub (`apps/hub/src/pages/index.astro`,
  `en/index.astro`, `contact.astro`) que NO usan el layout compartido y lo
  inyectan a mano (lineas 5+112, 5+109, 8+72 respectivamente).
- La libreria `cookie-consent.ts` expone una API publica via
  [packages/ui/src/index.ts:14-23](../../../packages/ui/src/index.ts#L14-L23):
  `readConsent`, `writeConsent`, `isConsentValue`, `STORAGE_KEY`,
  `CONSENT_CHANGED_EVENT`, `REOPEN_BANNER_EVENT`, `ConsentValue`. Ningun
  consumidor externo (apps, packages) la usa fuera del propio CookieBanner +
  Footer + track-event + TrackingPixel — verificado con `grep -l`.
- El `Footer.astro` tiene un boton "Gestionar consentimiento"
  (`data-testid="manage-consent"`) que despacha `REOPEN_BANNER_EVENT` para
  reabrir el banner — UI obligatoria por GDPR cuando hay opt-in revocable,
  ahora irrelevante.
- El `TrackingPixel.astro` tiene un listener
  [TrackingPixel.astro:99-102](../../../packages/ui/src/components/TrackingPixel.astro#L99-L102)
  que re-emite `page_load` cuando el consentimiento cambia a `'accepted'`
  (caso: el usuario rechaza, luego reabre con el Footer y acepta). Sin
  banner ese flujo desaparece.
- Existe un bypass de QA: `?cf_track=force` en la URL hace
  `isTrackingForced()` -> `true` y salta el gating. Lo usan 3 specs E2E
  (`tracking/track-pageload.spec.ts`, `contact/contact-funnel.spec.ts`,
  `contact/contact-session-link.spec.ts`) para forzar eventos en CI.
- El i18n: `packages/content/src/data/i18n/elements/elements.{es,en}.yaml`
  declara `components.cookieBanner` (6 campos) y `components.footer.manageConsent`.
  `packages/content/src/schemas.ts` linea 392-399 valida `cookieBanner` con
  Zod, lo cual lo hace OBLIGATORIO en el shape `ComponentsStrings`.
- Backend: el Lambda `tracking_pixel` (en
  `serverless/lambda/services/tracking_pixel/`) acepta eventos sin asumir
  consentimiento (no consulta nada del lado del cliente). El TTL de 60 dias
  esta en la tabla DynamoDB `tracking`. Por eso este plan toca SOLO
  frontend (decision D8 en el README).
- Coverage actual: ya hay tests unit para `cookie-consent.ts`,
  `track-event.ts` (incluyendo gating), `scroll-depth.ts`,
  `click-tracking.ts` y el spec E2E `tracking/consent.spec.ts` con 8 AC.

### Por que se elimina

El usuario quiere analytics privacy-friendly **estilo Vercel**: sin cookies,
anonimo, always-on, sin opt-in visible. La existencia del banner:

1. **Mata la senal de tracking**: la inmensa mayoria de los visitantes
   nunca interactua con el banner y el `cf_consent` queda `null`, asi que
   el backend recibe 0 eventos. El sistema de analytics existe pero no se
   alimenta.
2. **Anade fricion UX innecesaria**: el banner aparece encima del contenido
   en cada primera visita, requiere decision binaria, ocupa el viewport en
   mobile.
3. **Justifica codigo y tests** (cookie-consent.ts, banner Astro,
   `hasTrackingConsent`, `isTrackingForced`, 8 AC en consent.spec.ts) que
   ya no aporta proteccion real porque el tracking es totalmente anonimo
   server-side (no PII, no fingerprinting, no cookies de terceros, TTL
   60 dias en DynamoDB).

## 2. Solucion propuesta

**Tracking always-on, sin UI de consentimiento, sin gating client-side.**
`trackEvent()` queda como wrapper directo de `sendBeaconPayload` +
`buildTrackPayload`. El backend no cambia. Privacy stance documentado en el
PR body.

### Decisiones clave

- **D1**: eliminar artefactos source de la opcionalidad — `CookieBanner.astro`,
  `cookie-consent.ts` y `cookie-consent.test.ts`. NO se mantiene shim ni
  re-export "por compatibilidad" (la API era interna del portfolio).
- **D2**: simplificar `track-event.ts` — borrar `STORAGE_CONSENT`, `QA_FLAG`,
  `QA_FLAG_VALUE`, `CONSENT_ACCEPTED` (constantes) y `isTrackingForced`,
  `hasTrackingConsent` (funciones). La firma publica de `trackEvent()` no
  cambia (`(eventTypeId, props?) => boolean`), pero su semantica:
  `false` solo si `sendBeaconPayload` reporta fallo. Las funciones puras
  `buildTrackPayload`, `generateEventId`, `getSessionId`, `sendBeaconPayload`,
  `configureTracking`, `resetTrackingConfig` quedan intactas.
- **D3**: eliminar el bypass `?cf_track=force`. Sin gating no tiene sentido.
  Los 3 specs E2E que lo usan migran a `page.goto(...)` plano. Si en el
  futuro hace falta deshabilitar tracking en algun spec puntual, se hace
  con `page.route('**/track', ...fulfill)` que ya esta en uso.
- **D4**: eliminar el boton "Gestionar consentimiento" del Footer y todo el
  `<script>` que despacha `REOPEN_BANNER_EVENT`. La key `manageConsent`
  desaparece del i18n y del schema Zod.
- **D5**: eliminar las claves YAML `cookieBanner` (es/en) + `footer.manageConsent`
  (es/en) + el bloque `cookieBanner` del schema Zod en `schemas.ts`. Cambio
  breaking en `ComponentsStrings` que es interno al monorepo — `tsc` y
  `astro check` capturan cualquier resto.
- **D6**: eliminar en `TrackingPixel.astro` el listener
  `portfolio:consent-changed`. `page_load` se emite siempre en el cold start
  via `requestIdleCallback` (codigo existente).
- **D7**: privacy stance documentado in-PR (no PII, no cookies, session_id en
  localStorage por 60 dias, backend respeta TTL). NO se agrega ningun
  banner / nota / pagina nueva. (Si el usuario decide despues que quiere un
  "Privacy" link en el Footer, va en un PR aparte.)
- **D8**: solo frontend. Lambda `tracking_pixel`, esquema DynamoDB
  `tracking`, replica analitica en Neon — todos quedan intactos.

### Lo que NO cambia

- El payload que viaja a `POST /track` (mismo `operation`, `action`,
  `session_id`, `event_id`, `event_type_id`, `page_url`, `niche`,
  `event_props?`).
- El uso de `navigator.sendBeacon` con fallback fetch keepalive y
  `Content-Type: text/plain` (CORS preflight workaround, ver
  `bot-detection-turnstile-solver.md` y comentarios en `track-event.ts`).
- El `cf_session` en `localStorage` (UUID de la sesion). Sigue siendo lo
  unico persistido del lado del cliente — clave reusada del antiguo pixel.
- Los EVENT_TYPES UUIDs en `packages/content/src/lib/event-types.ts`
  (page_load, spa_navigation, page_exit, scroll_depth, click_*, contact_*).
- El listener `astro:after-swap` para `spa_navigation` y el
  `visibilitychange` para `page_exit` en `TrackingPixel.astro`.

## 3. Criterios de aceptacion (BDD)

Numeracion estable. Cada test del plan referencia al menos un AC.

- **AC-1**: **Given** una visita inicial a cualquier subdominio del
  portfolio (generic, hub, fintech, architect, leader, vibe), **When** el
  layout termina de renderear, **Then** el DOM NO contiene ningun
  `<div id="cookie-banner">` ni elemento con `role="dialog"
  aria-label="Consentimiento de analytics"` ni la cadena de texto
  "auto-borran en 60 dias" / "auto-delete in 60 days" / "Permitis
  recolectar" / "let us collect".

- **AC-2**: **Given** una visita inicial sin `localStorage.cf_consent`
  previo, **When** la pagina termina de cargar (`requestIdleCallback`
  dispara o el `setTimeout(100)` de fallback), **Then** se envia
  exactamente 1 `POST /track` con `event_type_id` igual al UUID de
  `EVENT_TYPES.PAGE_LOAD` SIN haber requerido ningun click previo ni
  query param.

- **AC-3**: **Given** un visitante navega entre paginas SPA via
  `astro:after-swap`, **When** ocurre el swap, **Then** se emite un
  `POST /track` con `event_type_id = SPA_NAVIGATION`; idem
  `event_type_id = PAGE_EXIT` cuando `document.visibilityState === 'hidden'`.
  Ningun caso requiere consentimiento previo.

- **AC-4**: **Given** el Footer renderizado en cualquier subdominio,
  **When** inspecciono el DOM, **Then** NO existe un elemento con
  `data-testid="manage-consent"` ni un `<button data-action="reopen-consent">`,
  y el script de `Footer.astro` NO referencia `REOPEN_BANNER_EVENT`.

- **AC-5**: **Given** ejecuto `pnpm exec biome check . && pnpm exec tsc
  --noEmit && pnpm exec astro check` en el root, **When** termina, **Then**
  exit code 0 y `rg -l '<keyword>'` sobre las 10 keywords del plan da 0
  resultados (excluyendo `dist/`, `node_modules/`, `docs/specs/`):

  ```
  CookieBanner            cookie-consent         cf_consent
  cf_track                REOPEN_BANNER_EVENT    CONSENT_CHANGED_EVENT
  hasTrackingConsent      isTrackingForced       cookieBanner
  manageConsent
  ```

- **AC-6**: **Given** ejecuto `pnpm exec vitest run` recursivo, **When**
  termina, **Then** todos los tests del package `ui`, `content`, `app-shared`
  pasan; el archivo `packages/ui/tests/unit/cookie-consent.test.ts` no
  existe; los bloques que mockean `localStorage.setItem('cf_consent', ...)`
  o `URLSearchParams.get('cf_track')` en `track-event.test.ts`,
  `scroll-depth.test.ts`, `click-tracking.test.ts` fueron eliminados y los
  tests restantes pasan sin ese setup; el assertion de
  `build-strings.test.ts` sobre las claves `cookieBanner` y `manageConsent`
  fue eliminado.

- **AC-7**: **Given** ejecuto la suite Playwright E2E (`python3
  devtools/run.py test_runner --module=feature --type=feature
  --env=local`), **When** termina, **Then** el archivo
  `tests/feature/tracking/consent.spec.ts` no existe; los 3 specs restantes
  que tocaban tracking (`tracking/track-pageload.spec.ts`,
  `contact/contact-funnel.spec.ts`, `contact/contact-session-link.spec.ts`)
  NO contienen el substring `cf_track=force`, sus URLs son plano
  `page.goto('${subdomainUrl()}/')` o `subdomainUrl()/contact`, y todos
  los tests pasan validando el POST a `/track` directamente.

- **AC-8**: **Given** ejecuto `pnpm run build` para las 6 apps, **When**
  termina, **Then** las 6 `dist/` resultantes NO contienen
  `CookieBanner.*.js`, `cookie-consent.*.js`, ni la cadena de texto del
  banner (verificable con `rg -l "auto-borran en 60\|Permitis recolectar\|let us collect" apps/*/dist`),
  y `pnpm run preview` de cualquier app NO renderea el banner.

## Trazabilidad AC -> tests

| AC | Tipo de test | Donde vive |
|----|--------------|------------|
| AC-1 | E2E + assertion DOM | `tests/feature/tracking/track-pageload.spec.ts` (nuevo assertion) |
| AC-2 | E2E (POST capture) | `tests/feature/tracking/track-pageload.spec.ts` (existente, sin `?cf_track=force`) |
| AC-3 | E2E (POST capture) | `tests/feature/tracking/track-pageload.spec.ts` (existente, simplificado) |
| AC-4 | E2E + unit (Footer DOM) | E2E: `tests/feature/tracking/track-pageload.spec.ts` (nuevo) + unit: removido en `build-strings.test.ts` |
| AC-5 | Manual (bateria seccion 11 Parte A) | `06-verificacion-e2e.md` |
| AC-6 | Unit | `packages/ui/tests/unit/track-event.test.ts`, `scroll-depth.test.ts`, `click-tracking.test.ts`, `packages/app-shared/tests/unit/lib/build-strings.test.ts` |
| AC-7 | E2E (suite completa) | `tests/feature/{tracking,contact}/*.spec.ts` |
| AC-8 | Build + `rg` sobre `apps/*/dist/` | Manual (bateria seccion 11 Parte B) |

## Navegacion

- Anterior: [README](README.md)
- Siguiente: [02-flujo-y-archivos.md](02-flujo-y-archivos.md)
