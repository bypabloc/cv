---
title: drop-cloudfront-meta — plan
description: Eliminar columna cloudfront_meta de tracking_events + contacts y expires_at de tracking_events (Neon)
status: pending
---

# drop-cloudfront-meta

> Elimina 6 columnas huerfanas en Neon:
> - `tracking_events`: `cloudfront_meta` (JSONB), `expires_at` (TIMESTAMPTZ),
>   `page_url` (TEXT NOT NULL), `page_title` (TEXT), `referrer` (TEXT)
> - `contacts`: `cloudfront_meta` (JSONB)
>
> Tambien dropea el indice `idx_tracking_referrer` (parcial sobre referrer).
> Mantiene vivos: el helper `extract_cloudfront_meta`, la inyeccion en
> `_meta` del `http_dispatch`, y los campos Pydantic
> (`RequestMeta.cloudfront_meta`, `TrackEventModel.page_url/page_title/
> referrer`). El frontend sigue enviando todo; solo se elimina la
> persistencia downstream + las columnas + el indice. Drop forward,
> downgrade reversible.

## Cuando leer

| Archivo | Cuando leer |
|---|---|
| [01-contexto-y-decision.md](01-contexto-y-decision.md) | Contexto del cambio, solucion propuesta, criterios de aceptacion |
| [02-implementacion.md](02-implementacion.md) | Diagrama ER antes/despues, tests requeridos, archivos afectados con verificacion por archivo |
| [03-commits.md](03-commits.md) | Listado de commits incrementales con mensajes Conventional Commits |
| [04-paralelizacion-worktrees.md](04-paralelizacion-worktrees.md) | Paralelizacion (N/A — cambio secuencial) |
| [05-verificacion-e2e.md](05-verificacion-e2e.md) | Bateria final que precede al push + PR |

## Estado por fase

| Fase | Estado |
|---|---|
| 0 — Crear rama `feature/drop-cloudfront-meta` + commit del plan | pending |
| 1 — Migracion Alembic `drop_cloudfront_meta_and_expires_at` | pending |
| 2 — Drop columnas en modelos SQLAlchemy | pending |
| 3 — Drop persistencia + parametros en services/controllers | pending |
| 4 — Actualizar unit tests afectados | pending |
| 5 — Verificacion E2E + cleanup del plan | pending |

## Decisiones no-reabribles

1. **Drop directo** (no backup ni archive). Volumen acumulado en
   dev/prod es minimo. Migration con `upgrade=drop_column` +
   `downgrade=add_column` nullable.
2. **Scope de columnas borradas** (6 columnas + 1 indice):
   - `tracking_events`: `cloudfront_meta`, `expires_at`, `page_url`,
     `page_title`, `referrer`
   - `contacts`: `cloudfront_meta`
   - Indice: `idx_tracking_referrer` (parcial)
3. **Que NO se toca**:
   - `expires_at` en DynamoDB cache + `TrackingEventItem` (fixture
     legacy) + `RateLimitBucketItem` — TTL real con consumer activo.
   - `page_path` en `tracking_events` (sigue NOT NULL + indice
     `idx_tracking_page_path`).
   - Indices de tracking_events restantes: `idx_tracking_session_created`,
     `idx_tracking_created_brin`, `idx_tracking_page_path`,
     `idx_tracking_utm_source`, `idx_tracking_country`,
     `idx_tracking_device_type`, `idx_tracking_niche_created`,
     `idx_tracking_event_type`.
4. **Pydantic + frontend permanecen**: los modelos
   `TrackEventModel` (campos `page_url`, `page_title`, `referrer`),
   `RequestMeta.cloudfront_meta` y `TrackEventMeta.cloudfront_meta`
   siguen aceptando los valores que envia el frontend. El frontend
   (`build-track-payload`, `TrackingPixel.astro`) NO cambia. Solo se
   elimina la persistencia downstream + las columnas + el indice.
5. **Helper `extract_cloudfront_meta` + inyeccion `_meta.cloudfront_meta`
   en `shared.lambda_kit.http_dispatch`** se mantienen. Sus tests
   existentes se mantienen verdes.
6. **Forward-only en CI**: la migracion se aplica via la Lambda `db`
   contra dev/stage/prod (en ese orden). NO se downgradea en prod salvo
   incidente; el `downgrade()` se prueba en un branch Neon antes del
   deploy.

## Reglas criticas

- **SIEMPRE** probar `upgrade head` + `downgrade -1` + `upgrade head` en
  un branch Neon de prueba antes de tocar dev.
- **SIEMPRE** un solo PR `feature/drop-cloudfront-meta -> dev`. Promocion
  a stage/main sigue el flujo en cadena estandar.
- **SIEMPRE** dropear el indice `idx_tracking_referrer` ANTES de la
  columna `referrer` en `upgrade()`. En `downgrade()` recrear la
  columna ANTES del indice.
- **NUNCA** editar la migracion `b2c3d4e5f6a7` ya aplicada en
  dev/stage/prod — crear migracion nueva con `down_revision =
  'b2c3d4e5f6a7'`.
- **NUNCA** tocar la columna `expires_at` en `shared/dynamodb/models/`
  (TrackingEventItem fixture + cache + rate_limit_bucket usan TTL real
  de DDB, distinto al `expires_at` huerfano de Neon).
- **NUNCA** tocar `shared.http.ip_extractor.extract_cloudfront_meta`,
  el bloque de `http_dispatch.py` que inyecta `cloudfront_meta` en
  `_meta`, ni los campos Pydantic
  (`RequestMeta.cloudfront_meta`,
  `TrackEventMeta.cloudfront_meta`, `TrackEventModel.page_url/
  page_title/referrer`).
- **NUNCA** tocar el frontend (`build-track-payload.ts`,
  `TrackingPixel.astro`, `contact` form): siguen enviando todos los
  campos.
- **NUNCA** dropear `page_path` (sigue NOT NULL y con indice
  `idx_tracking_page_path` para queries por seccion).

## Matriz de verificacion (resumen)

| Comando | Cuando | Donde |
|---|---|---|
| Alembic upgrade/downgrade en branch Neon prueba | Antes de aplicar a dev | local |
| `serverless tests --type=unit --lambda=tracking_pixel` | Cada commit que toca tracking_pixel | local |
| `serverless tests --type=unit --lambda=contact_form` | Cada commit que toca contact_form | local |
| `serverless tests --type=unit --lambda=db` | Tras tocar shared/db | local |
| `serverless tests --type=integration --lambda=tracking_pixel` | Fase 5 | local |
| `serverless tests --type=integration --lambda=contact_form` | Fase 5 | local |
| `serverless run --stage=dev --lambda=db --event=events/migrate.json` | Tras mergear el PR a dev | dev (AWS) |

Detalle de cada comando en
[05-verificacion-e2e.md](05-verificacion-e2e.md).

## Navegacion

- Inicio: [01-contexto-y-decision.md](01-contexto-y-decision.md)
- Reglas del formato: [.claude/rules/plan-format.md](../../../.claude/rules/plan-format.md)
