# SPEC-013: Componentes `TrackingPixel.astro` + `CookieBanner.astro` + GDPR opt-in

**Estado**: draft
**Autor**: Pablo Contreras
**Fecha**: 2026-05-14
**Areas afectadas**: `packages/ui/src/components/`, layouts compartidos
**Dependencias**: SPEC-006 (Lambda tracking_pixel deployada), SPEC-012
**Paralelizable con**: SPEC-014

## 1. Contexto

Tracking pixel best-effort para analytics propios + banner GDPR
opt-in. El tracking NO se ejecuta sin consent explicito (decision
documentada en preguntas previas del usuario).

### Hallazgos de exploracion

- Flujo en `serverless/ARCHITECTURE.md` seccion 4 (POST /track)
- Cookie banner obligatorio por GDPR + ePrivacy
- Components compartidos en `packages/ui` (mismo patron que SPEC-012)

## 2. Solucion propuesta

Crear 7 archivos en `packages/ui/src/components/`:

```text
packages/ui/src/components/
├── tracking/
│   ├── TrackingPixel.astro      # carga client:idle si consent OK
│   ├── tracking-pixel.client.ts # signals collection + POST /track
│   └── tracking-pixel.types.ts
└── cookies/
    ├── CookieBanner.astro       # banner GDPR opt-in
    ├── cookie-banner.client.ts  # logic accept/reject + localStorage
    ├── cookie-banner.types.ts
    └── cookie-banner.css
```

Plus integracion en `packages/app-shared/src/layouts/BaseLayout.astro`
(layout compartido de los 6 apps).

### Decisiones clave

- **Decision 1: localStorage con key `cf_consent`** — vs cookie:
  localStorage NO se envia con cada request (mejor performance) y NO
  es trackeable cross-site. Persistencia idem.
- **Decision 2: Banner sticky bottom inicialmente** — vs modal
  bloqueante. UX menos intrusiva. Cerrar con X = "rechazar" (no
  tracking). Botones explicitos "Aceptar" / "Rechazar".
- **Decision 3: TrackingPixel `client:idle`** — vs `client:load`.
  Razon: NO interferir con Core Web Vitals. Tracking dispara despues
  de que la pagina sea interactive.
- **Decision 4: session_id en localStorage** — UUIDv4 generado al
  primer page view post-consent. TTL: hasta close del browser.
  Persistencia entre tabs.

## 3. Criterios de Aceptacion (AC)

- **AC-1**: Given visitante primera vez en cualquier app, When carga
  cualquier pagina, Then ve banner GDPR con texto + 2 botones
  (Aceptar / Rechazar)
- **AC-2**: Given visitante click "Rechazar", When inspecciono
  localStorage, Then `cf_consent = "rejected"` y NO se hace POST /track
- **AC-3**: Given visitante click "Aceptar", When inspecciono Network
  tab, Then POST /track ejecuta dentro de 5s con body completo
  (session_id, url, signals, etc.)
- **AC-4**: Given visitante con consent="accepted" navega entre paginas,
  When carga cada nueva pagina, Then POST /track ejecuta para cada
  vista con mismo `session_id`
- **AC-5**: Given UTM params en URL (`?utm_source=linkedin&utm_campaign=cv`),
  When POST /track, Then body incluye los utm_source + utm_campaign
- **AC-6**: Given visitante con consent rejected, When recarga la
  pagina 1 mes despues, Then banner NO reaparece (decision persistida)
- **AC-7**: Given banner visible, When inspecciono lighthouse, Then
  Performance scores no caen mas de 2 puntos vs sin banner
- **AC-8**: Given banner visible, When uso solo teclado, Then puedo
  navegar a "Aceptar" y "Rechazar" con Tab + activar con Enter
- **AC-9**: Given tracking pixel disparado, When response 204 llega,
  Then NO se hace nada en UI (silent, no UX impact)

## 4. Diagrama de Flujo

```text
Page load (any of the 6 apps)
    |
    v
BaseLayout.astro renderiza
    |
    +-- localStorage.cf_consent existe?
    |       |
    |       +-- "accepted" -> render TrackingPixel client:idle
    |       +-- "rejected" -> nada
    |       +-- undefined -> render CookieBanner
    |
    v
Usuario interactua:
    |
    +-- click Aceptar -> set cf_consent=accepted + dismiss banner + load TrackingPixel
    +-- click Rechazar -> set cf_consent=rejected + dismiss banner
    |
    v
TrackingPixel (si activado):
    |
    +-- generate/get session_id (localStorage)
    +-- collect signals (UA, screen, lang, etc.)
    +-- get/skip Turnstile invisible token (opt-in)
    +-- fetch POST /track (no-cors OK, ignore response 204)
```

## 5. Diagrama ER

N/A — frontend.

## 6. Tests Requeridos

### 6.A. TDD Flows

- WHEN consent undefined THEN banner shown [AC-1]
- WHEN consent rejected THEN no POST /track [AC-2]
- WHEN consent accepted THEN POST /track in <5s [AC-3]
- WHEN navigate to new page THEN otro POST /track [AC-4]
- WHEN URL has UTM THEN body include utm_* [AC-5]

### 6.B. Unit Tests (Vitest)

- `tests/unit/components/tracking/test_tracking_pixel_client.ts`
- `tests/unit/components/cookies/test_cookie_banner_client.ts`

### 6.D. E2E (Playwright)

- `tests/feature/tracking/cookie-banner-flow.feature`:
  - Aceptar y verificar request POST /track
  - Rechazar y verificar NO hay request
  - Cierra X y verifica = rechazar

## 7. Archivos Afectados

### Crear

- `packages/ui/src/components/tracking/TrackingPixel.astro`
- `packages/ui/src/components/tracking/tracking-pixel.client.ts`
- `packages/ui/src/components/tracking/tracking-pixel.types.ts`
- `packages/ui/src/components/cookies/CookieBanner.astro`
- `packages/ui/src/components/cookies/cookie-banner.client.ts`
- `packages/ui/src/components/cookies/cookie-banner.types.ts`
- `packages/ui/src/components/cookies/cookie-banner.css`
- `tests/feature/tracking/cookie-banner-flow.feature`
- `tests/feature/tracking/cookie_banner_steps.ts`

### Modificar

- `packages/app-shared/src/layouts/BaseLayout.astro` — incluir
  `<CookieBanner />` antes del `</body>` + condicionalmente
  `<TrackingPixel />` segun consent
- `packages/ui/src/index.ts` — exportar nuevos componentes
- `apps/*/src/env.d.ts` — verificar
  `ImportMetaEnv.PUBLIC_API_ENDPOINT` ya esta (de SPEC-012)

## 8. Descomposicion para Paralelizacion

| Task | Archivos | Depende de | Paralelizable con |
|------|----------|------------|-------------------|
| T1 | cookie-banner.types.ts + cookie-banner.css | — | T2 |
| T2 | cookie-banner.client.ts | T1 | T1 |
| T3 | CookieBanner.astro | T1, T2 | T4 |
| T4 | tracking-pixel.{types,client}.ts + TrackingPixel.astro | — | T3 |
| T5 | BaseLayout integration | T3, T4 | — |
| T6 | Playwright tests | T5 | — |

## 9. Validacion y Definition of Done

### Pre-implementacion

- [ ] SPEC-006 done (Lambda tracking_pixel operacional)
- [ ] SPEC-012 done (precedente, mismo patron)

### Definition of Done

- [ ] AC-1 a AC-9 cumplidos
- [ ] Tests Vitest >= 80% coverage en TS
- [ ] Tests Playwright pasan en 6 apps
- [ ] Lighthouse Performance score sin degradacion significativa
- [ ] Manual testing: aceptar -> verificar DynamoDB tracking tiene
      row con session_id consistente entre paginas
- [ ] GDPR compliance: leer `.claude/docs/cloudflare-turnstile/`
      sobre privacy + consent
