# SPEC-102: TrackingPixel `page_load` en las 6 apps

**Estado**: draft
**Fase**: 1
**Autor**: Pablo Contreras
**Fecha**: 2026-05-17
**Areas afectadas**: `packages/ui/`, `packages/app-shared/`, `apps/*/`,
`serverless/src/tracking_pixel/`, `serverless/src/stream_processor/`,
`tests/feature/`
**Dependencias**: SPEC-101 (`event_types` + `EVENT_TYPES.PAGE_LOAD`)
**Paralelizable con**: ninguna dentro de Fase 1 (cierra la fase)

> Anterior: [SPEC-101](SPEC-101-catalogo-event-types.md) | Siguiente: [SPEC-200](SPEC-200-mapa-de-eventos.md)

## 0. Contexto requerido

> Una sesion sin contexto previo DEBE leer esto antes de implementar.
> Esta spec depende de SPEC-101: `event_types` + `EVENT_TYPES` deben existir.

### Leer antes de empezar

| Archivo / recurso | Por que |
| ----------------- | ------- |
| [README.md](README.md) de esta carpeta | Decisiones del interview, mapa de las 2 fases |
| [SPEC-101](SPEC-101-catalogo-event-types.md) | Provee `EVENT_TYPES.PAGE_LOAD` y la columna `event_type_id` |
| `packages/ui/src/components/TrackingPixel.astro` | Componente actual a extender (payload, sendBeacon) |
| `packages/ui/src/index.ts` | Barrel de `@portfolio/ui` (se exporta el componente) |
| `packages/app-shared/src/layouts/SitePageLayout.astro` | Layout de 5 apps donde se monta el pixel |
| `apps/hub/src/layouts/PageLayout.astro` y `apps/hub/src/pages/index.astro` | hub no usa `SitePageLayout`: montar el pixel aparte |
| `serverless/src/tracking_pixel/schemas.py` | `TrackingEventInput` a extender con `event_id`/`event_type_id` |
| `serverless/src/tracking_pixel/persistence.py` | Escritura del item DynamoDB |
| `serverless/src/stream_processor/pg_writer.py` | `INSERT` a `tracking_events` (Neon) |
| `tests/feature/` (specs `smoke/`, `contact/`) | Patron de test E2E Playwright + fixtures de subdominios |

### Rules del proyecto aplicables

- `.claude/rules/astro-landing.md` — componentes Astro, TS strict, Biome
- `.claude/rules/design-system.md` — tokens del DS (si el pixel toca UI)
- `.claude/rules/python.md` — backend `tracking_pixel`/`stream_processor`
- `tests/feature/README.md` — escribir specs Playwright
- `.claude/rules/verify-before-done.md` — incluye correr la suite E2E

### Decisiones del interview que aplican

- `event_id`: UUIDv4 generado por el cliente, uno por evento (idempotencia).
- `event_type_id`: el UUID de `page_load` (ver SPEC-101 seccion 0).
- El pixel se monta pero queda inerte sin `cf_consent`; para E2E se usa el
  flag `?cf_track=force`. El `CookieBanner` NO se monta en Fase 1 (es SPEC-201).
- Re-disparo en `astro:after-swap` para trackear navegacion SPA.

## 1. Contexto

El endpoint `POST /track` esta deployado y operativo, pero el frontend nunca
lo invoca. Los componentes `TrackingPixel.astro` y `CookieBanner.astro` existen
en `packages/ui/src/components/` pero estan huerfanos.

### Hallazgos de exploracion

- `packages/ui/src/index.ts` (barrel) NO exporta `TrackingPixel` ni
  `CookieBanner`. Solo exporta funciones vanilla TS.
- `packages/app-shared/src/layouts/SitePageLayout.astro` es el layout que usan
  5 de las 6 apps (generic, fintech, architect, leader, vibe) via un
  `PageLayout.astro` thin-wrapper por app. Recibe la prop `niche`.
- `apps/hub` es la excepcion: su `index.astro` usa `BaseLayout` directo, no
  `SitePageLayout`. Hay que montar el pixel ahi por separado.
- `TrackingPixel.astro` hoy: genera `session_id` (UUIDv4 en
  `localStorage.cf_session`), arma el payload con `page_url`/`page_title`/UTMs
  y envia `POST /track` via `navigator.sendBeacon` (fallback `fetch`). Se
  dispara con `requestIdleCallback`. Respeta `localStorage.cf_consent`.
- El payload actual NO incluye `event_id` ni `event_type_id`.
- View Transitions esta activo (`ClientRouter` en `BaseLayout`). La navegacion
  SPA dispara `astro:after-swap`. El pixel actual NO re-dispara en navegacion.
- `PUBLIC_API_ENDPOINT` ya esta en `docker/env/client/.{dev,prod}`.
- Backend `tracking_pixel/schemas.py` (`TrackingEventInput`) NO acepta
  `event_id`/`event_type_id`. `persistence.py` no los escribe.
  `stream_processor/pg_writer.py` no los inserta en `tracking_events`.

## 2. Solucion propuesta

Cablear el pixel end-to-end para el evento `page_load`, con `event_id` por
evento. CookieBanner NO se monta en Fase 1 (llega en SPEC-201); para poder
verificar el pixel sin banner se agrega un flag de QA.

**Frontend:**

1. `TrackingPixel.astro`: extender el payload con `event_id` (UUIDv4 generado
   por evento) y `event_type_id` (`EVENT_TYPES.PAGE_LOAD` importado de
   `@portfolio/content`). Re-disparar el tracking en `astro:after-swap`
   (navegacion SPA) generando un `event_id` nuevo. Agregar el flag de QA
   `?cf_track=force` que permite trackear sin `cf_consent` (para E2E).
2. `packages/ui/src/index.ts`: exportar `TrackingPixel.astro`.
3. `SitePageLayout.astro`: montar `<TrackingPixel apiEndpoint={...} niche={niche} />`.
4. `apps/hub`: montar el pixel en su layout/`index.astro`.

**Backend:**

1. `tracking_pixel/schemas.py`: agregar `event_id` y `event_type_id` como
   campos UUID validados.
2. `tracking_pixel/persistence.py`: escribir `event_id` y `event_type_id` en
   el item de DynamoDB.
3. `stream_processor/pg_writer.py`: incluir `event_id`/`event_type_id` en el
   `INSERT INTO tracking_events`.

### Decisiones clave

- **Decision 1: `event_id` generado por el cliente** — UUIDv4 por evento, en
  el body. Da idempotencia: un reintento de `sendBeacon` con el mismo
  `event_id` no debe duplicar el evento downstream.
- **Decision 2: el pixel se monta pero queda inerte sin consentimiento** — en
  Fase 1 no hay banner, asi que en prod nadie da `cf_consent` y el pixel no
  envia nada. Es intencional: cumple GDPR por defecto. La verificacion E2E usa
  el flag `?cf_track=force`.
- **Decision 3: re-disparo en `astro:after-swap`** — con View Transitions, la
  navegacion no recarga la pagina; sin el listener solo se trackearia la
  primera carga. Cada navegacion = un `page_load` nuevo con `event_id` nuevo.
- **Decision 4: `event_type_id` se valida en el backend** — un body sin
  `event_type_id` o con UUID malformado responde `400`. El evento debe estar
  siempre tipado.

## 3. Criterios de Aceptacion (AC)

- **AC-1**: Given una pagina de cualquiera de las 6 apps con consentimiento
  aceptado (o `?cf_track=force`), When termina la carga, Then se envia
  `POST /track` cuyo body incluye `event_id` (UUIDv4), `event_type_id` (UUID de
  `page_load`), `session_id` y `page_url`.
- **AC-2**: Given dos cargas de pagina consecutivas en la misma sesion, When se
  inspeccionan los dos requests, Then comparten el mismo `session_id` pero
  tienen `event_id` distintos.
- **AC-3**: Given una navegacion SPA via View Transition de `/` a `/about`,
  When se completa `astro:after-swap`, Then se envia un segundo `POST /track`
  con `event_id` nuevo y `page_url` = la nueva URL.
- **AC-4**: Given el backend `tracking_pixel` recibe un body con `event_id` y
  `event_type_id` UUID validos, When valida con Pydantic, Then ambos se
  aceptan y se persisten como atributos del item en DynamoDB `TrackingTable`.
- **AC-5**: Given un body de `/track` sin `event_type_id`, When valida, Then
  responde `400` con codigo `INVALID_INPUT`.
- **AC-6**: Given un body con `event_type_id` que no es un UUID valido, When
  valida, Then responde `400 INVALID_INPUT`.
- **AC-7**: Given un item de tracking con `event_id`/`event_type_id` fluye por
  el DynamoDB Stream, When `stream_processor` lo procesa, Then el `INSERT` en
  `tracking_events` (Neon) incluye ambas columnas con sus valores.
- **AC-8**: Given una pagina SIN consentimiento y SIN el flag `?cf_track=force`,
  When carga, Then NO se envia ningun `POST /track`.
- **AC-9**: Given `packages/ui/src/index.ts`, When se importa `TrackingPixel`,
  Then el componente esta exportado.

## 4. Diagrama de Flujo (Antes y Despues)

### Antes

```text
Navegador carga pagina -> (nada)        # TrackingPixel huerfano, no montado
```

### Despues

```text
Navegador carga pagina
  TrackingPixel (montado en layout)
    consent OK  o  ?cf_track=force ?
      no -> fin (no envia)
      si -> genera event_id (UUIDv4)
            payload { event_id, event_type_id=PAGE_LOAD,
                      session_id, page_url, ... }
            sendBeacon POST /track
  navegacion SPA (astro:after-swap)
    -> nuevo event_id -> POST /track  (nueva page_url)

Backend:
  POST /track -> tracking_pixel
    valida event_id + event_type_id (UUID) -> 400 si invalido
    put_item -> DynamoDB TrackingTable (con event_id, event_type_id)
    204
  DynamoDB Stream -> stream_processor
    INSERT tracking_events (... event_id, event_type_id) -> Neon
```

## 5. Diagrama ER

```text
tracking_events  (columnas event_id, event_type_id ya creadas por SPEC-101)
DynamoDB TrackingTable: event_id y event_type_id se agregan como atributos
del item (no son keys, no requieren cambio de AttributeDefinitions).
```

## 6. Tests Requeridos

### 6.B. Unit Tests

**Backend (pytest, `serverless/tests/`):**

- `tracking_pixel/test_schemas.py`: `event_id`/`event_type_id` UUID validos
  aceptados `[AC-4]`; ausencia de `event_type_id` -> `ValidationError`
  `[AC-5]`; UUID malformado -> `ValidationError` `[AC-6]`.
- `tracking_pixel/test_persistence.py`: el item escrito en DynamoDB contiene
  `event_id` y `event_type_id` `[AC-4]`.
- `stream_processor/test_pg_writer.py` (o equivalente): el `INSERT` de
  `tracking_events` incluye las dos columnas `[AC-7]`.

### 6.C. Typecheck

- `pnpm exec tsc --noEmit` + `pnpm exec astro check` (componentes `.astro`).
- Backend: `serverless typecheck`.

### 6.D. E2E Tests (Playwright)

`tests/feature/tracking/track-pageload.spec.ts`:

- WHEN abro cada uno de los 6 subdominios con `?cf_track=force` THEN se
  observa un `POST` a `/track` con `event_type_id` presente `[AC-1][AC-8]`.
  Capturar con `page.waitForRequest` / `page.route`.
- WHEN navego de `/` a `/about` THEN se observa un segundo `POST /track` con
  `page_url` nueva `[AC-3]`.
- WHEN abro una pagina sin el flag y sin consentimiento THEN NO hay request a
  `/track` `[AC-8]`.

## 7. Archivos Afectados

### Crear

- `tests/feature/tracking/track-pageload.spec.ts` — E2E del pixel en los 6
  subdominios + navegacion SPA + caso sin consentimiento.
  - Por que: verificar el cableado end-to-end contra el stack local.
  - Verificar: `python devtools/run.py test_runner --module=feature
    --type=feature --env=local`.
- Tests backend nuevos (`test_schemas.py` ampliado, `test_persistence.py`
  ampliado, test de `pg_writer`).
  - Verificar: test runner de `serverless`.

### Modificar

- `packages/ui/src/components/TrackingPixel.astro` — agregar `event_id`
  (UUIDv4 por evento) y `event_type_id` (`EVENT_TYPES.PAGE_LOAD`) al payload;
  importar `EVENT_TYPES` de `@portfolio/content`; re-disparar en
  `astro:after-swap` con `event_id` nuevo; soportar `?cf_track=force` como
  bypass de `cf_consent` para QA.
  - Por que: el pixel debe identificar cada evento y trackear navegacion SPA.
  - Verificar: `pnpm exec astro check`; E2E `[AC-1..AC-3][AC-8]`.
- `packages/ui/src/index.ts` — exportar `TrackingPixel.astro`.
  - Por que: que los layouts puedan importarlo desde `@portfolio/ui`.
  - Verificar: `pnpm exec tsc --noEmit`; `[AC-9]`.
- `packages/app-shared/src/layouts/SitePageLayout.astro` — montar
  `<TrackingPixel apiEndpoint={import.meta.env.PUBLIC_API_ENDPOINT}
  niche={niche} />`.
  - Por que: cubre 5 de las 6 apps con un solo cambio.
  - Verificar: `pnpm run build`; E2E en 5 subdominios.
- `apps/hub/src/layouts/PageLayout.astro` (o `apps/hub/src/pages/index.astro`,
  segun donde monte hub su shell) — montar `<TrackingPixel>`.
  - Por que: hub no usa `SitePageLayout`, queda fuera del cambio anterior.
  - Verificar: `pnpm run build`; E2E en `hub.localhost`.
- `serverless/src/tracking_pixel/schemas.py` — agregar a `TrackingEventInput`
  los campos `event_id` y `event_type_id` (tipo UUID, validados; `event_type_id`
  requerido).
  - Por que: el backend debe aceptar y validar los identificadores.
  - Verificar: `test_schemas.py` `[AC-4..AC-6]`.
- `serverless/src/tracking_pixel/persistence.py` — escribir `event_id` y
  `event_type_id` en el item de `TrackingTable`.
  - Por que: persistir los identificadores en DynamoDB.
  - Verificar: `test_persistence.py` `[AC-4]`.
- `serverless/src/stream_processor/pg_writer.py` — agregar `event_id` y
  `event_type_id` al `INSERT INTO tracking_events`.
  - Por que: replicar los identificadores a Neon para analitica.
  - Verificar: test de `pg_writer` `[AC-7]`.

## 8. Descomposicion para Paralelizacion

| Tarea | Archivos | AC | Depende de | Paralelizable con |
| ------- | ---------- | ----- | ------------ | ------------------- |
| T1 | `tracking_pixel/schemas.py` + `persistence.py` + tests | AC-4,5,6 | SPEC-101 | T2, T3 |
| T2 | `stream_processor/pg_writer.py` + test | AC-7 | SPEC-101 | T1, T3 |
| T3 | `TrackingPixel.astro` + `ui/index.ts` | AC-1,2,3,8,9 | SPEC-101 | T1, T2 |
| T4 | `SitePageLayout.astro` + `hub` layout | AC-1 | T3 | — |
| T5 | `track-pageload.spec.ts` (E2E) | AC-1,2,3,8 | T1,T3,T4 | — |

## 9. Validacion y Definition of Done

### Pre-implementacion

- [ ] SPEC-101 en `dev` (tabla `event_types` + `EVENT_TYPES` disponibles)
- [ ] Stack local levantado (`docker up --env=local`)
- [ ] Tests TDD escritos y fallando (Red)

### Definition of Done

- [ ] AC-1 a AC-9 cubiertos por tests que pasan
- [ ] Coverage >= 80% per-file en archivos backend modificados
- [ ] `pnpm exec tsc --noEmit` + `pnpm exec astro check` sin errores
- [ ] `pnpm exec biome check .` sin errores
- [ ] `pnpm run build` de las 6 apps exitoso
- [ ] `serverless` lint/format/typecheck/validate pasan
- [ ] E2E `track-pageload.spec.ts` verde contra el stack local
- [ ] Smoke en dev: cargar una pagina con `?cf_track=force` -> evento visible
  en DynamoDB `TrackingTable` y replicado en `tracking_events` (Neon)
- [ ] Tras merge `dev` -> `stage` -> `main`: verificacion en prod

> Anterior: [SPEC-101](SPEC-101-catalogo-event-types.md) | Siguiente: [SPEC-200](SPEC-200-mapa-de-eventos.md)
