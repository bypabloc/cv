# Plan: backend serverless — eliminar SQS, email centralizado, encoders sync

> Elimina SQS (3 colas + 3 DLQ + 3 workers) y el feature flag `ASYNC_MODE`,
> borra las referencias muertas a `stream_processor`, centraliza el envío de
> email en un Lambda `send_email` (config en DynamoDB + templates en S3 +
> Jinja2, invocado async con `InvocationType='Event'`), y deja la
> persistencia a Neon **inline y síncrona** en los encoders
> (`contact_form`, `tracking_pixel`) con psycopg3 + SnapStart. **NO** se crea
> `db_writer`. Principio rector: **error-proof, escalable y
> provider-swappable** — todo acceso AWS detrás de `shared.*`.

Escala: **Large** (1 Lambda nuevo `send_email`, 3 eliminados, 4 services
migrados, devtools tocado, 1 tabla DynamoDB + 1 bucket S3 nuevos).

## Honestidad sobre el cold start (leer primero)

Este refactor **NO reduce el cold start de los encoders** — lo aclaro porque
fue la motivación inicial. Con SnapStart (ya activo en `contact_form` y
`tracking_pixel`) el cold es el *restore* (~1s), no el import: el import ya
está en el snapshot. `contact_form` ya importaba `shared.db`. El valor real
del plan es **simplicidad** (−SQS, −3 workers, −`ASYNC_MODE`) y **flexibilidad
de emails** (config central editable sin redeploy). Ver
[01 §1](01-contexto-y-decision.md).

**Tradeoff conocido**: `tracking_pixel` deja de tocar-Neon-solo-en-sync y pasa
a escribir inline siempre → **128 MB → 256 MB** (necesita `shared.db`). Es una
regresión de memoria en el Lambda de mayor volumen, aceptada a cambio de
eliminar el worker. Mitigación opcional (write path raw psycopg3, más liviano)
documentada en [05](05-encoders-refactor.md); se evalúa sólo si la medición de
fase 7 lo justifica.

## Cuándo leer cada archivo

| Archivo | Cuándo leer |
|---------|-------------|
| [01-contexto-y-decision.md](01-contexto-y-decision.md) | Problema, solución, AC-1..AC-16 (secciones 1-3) |
| [02-shared-foundations.md](02-shared-foundations.md) | `shared.aws.lambda_invoke` (para invocar send_email) + `shared.templating` (Jinja2) |
| [03-devtools-provisioning.md](03-devtools-provisioning.md) | `uses.invokes`, `uses.buckets`, recurso S3, tabla email-config, quitar SQS |
| [04-send-email-lambda.md](04-send-email-lambda.md) | Lambda `send_email` + tabla `email-config` + templates S3 |
| [05-encoders-refactor.md](05-encoders-refactor.md) | `contact_form`/`tracking_pixel`: quitar `ASYNC_MODE`, escritura inline síncrona, invocar send_email, memoria |
| [06-migrate-callers-remove-sqs.md](06-migrate-callers-remove-sqs.md) | auth/users → send_email; borrar workers + SQS + `shared.queue` |
| [07-cleanup-stream-processor.md](07-cleanup-stream-processor.md) | Limpiar refs a `stream_processor` + promover convenciones a rules |
| [08-descomposicion.md](08-descomposicion.md) | Sección 8 — tareas atómicas + paralelización |
| [09-commits.md](09-commits.md) | Sección 9 — secuencia de commits |
| [10-paralelizacion-worktrees.md](10-paralelizacion-worktrees.md) | Sección 10 — worktrees / olas de agentes |
| [11-verificacion-e2e.md](11-verificacion-e2e.md) | Sección 11 — batería + medición de cold start (gate del PR) |

## Estado por fase

| Fase | Archivo | Estado |
|------|---------|--------|
| 0 | docs del plan | `pending` |
| 1 | Shared foundations (02) | `pending` |
| 2 | Devtools provisioning (03) | `pending` |
| 3 | Lambda `send_email` (04) | `pending` |
| 4 | Encoders refactor (05) | `pending` |
| 5 | Migrar auth/users + borrar SQS (06) | `pending` |
| 6 | Limpieza `stream_processor` (07) | `pending` |
| 7 | Verificación E2E + medición (11) | `pending` |

## Decisiones no-reabribles (confirmadas con el usuario)

1. **NO se crea `db_writer`.** La persistencia a Neon es **inline y síncrona**
   en `contact_form`/`tracking_pixel` (la investigación mostró que un INSERT
   warm pooled es ~10-25ms, imperceptible; y que en Lambda no hay
   "async fire-and-forget en proceso").
2. **Transporte de email = Lambda `InvocationType='Event'`** hacia
   `send_email`. **CERO SQS** (ni DLQ). Email best-effort.
3. **`send_email` puro**: DynamoDB (config) + S3 (template) + Jinja2 + SES.
   NO toca Neon. Tabla `email-config` (PK=`kind`), **una plantilla por kind**
   (10 kinds → 10 templates html + 10 txt en S3).
4. **Owner-email del contacto**: `contact_form` invoca `send_email` async,
   **siempre** (tras escribir el contacto inline). No idempotente.
5. **`users` ENTRA en scope** (migra sus 4 kinds a `send_email`).
6. **Bucket S3 per-env**: `portfolio-email-templates-{dev,stage,prod}`.
7. **Eliminar `ASYNC_MODE`** y el path sync legacy duplicado: queda un único
   path (escribir + responder).
8. **Provider-swappable**: AWS detrás de `shared.*`. Se crean
   `shared.aws.lambda_invoke` y `shared.templating`; se reusan
   `shared.aws.s3` (`get_object_text`, ya existe), `shared.aws.ses`,
   `shared.db`.
9. **"Consultas async" (reads multi-query con gather) FUERA de scope** — eso
   pertenece al Lambda de lectura del dashboard (otro plan). Se anota allí.
10. **`tracking_pixel` 128→256 MB** aceptado (escribe Neon inline). Mitigación
    raw-psycopg3 sólo si la medición de fase 7 la justifica.

## Reglas críticas (siempre activas)

- **SIEMPRE** los `core/**/*.py` importan AWS sólo vía `shared.*`
  (`shared.aws.lambda_invoke`, `shared.aws.s3`, `shared.aws.ses`,
  `shared.aws.dynamodb`, `shared.db`, `shared.templating`). `lint-deps` verde.
- **SIEMPRE** los `__init__.py` de `shared/*` quedan VACÍOS (sin barrels).
- **SIEMPRE** los encoders importan `shared.db` al top + `warm_db()` en INIT
  (van al snapshot de SnapStart). NO lazy si la dep es incondicional.
- **SIEMPRE** `memory`/`timeout` = MÍNIMO medido y justificado en el manifest
  (`.claude/rules/lambda-config.md`).
- **SIEMPRE** invocación async de email = `InvocationType='Event'`; el caller
  no espera; degrada a log si falla (no rompe el request).
- **SIEMPRE** TDD: test primero, asserts EXACTOS, coverage ≥80% per-file.
- **NUNCA** atribución de IA. **NUNCA** reintroducir SQS. **NUNCA** crear
  `db_writer`.

## Ciclo de vida

Carpeta **efímera**: el último commit (fase 7) la elimina con
`git rm -r`. Convenciones que sobreviven (formato `uses.invokes`/
`uses.buckets`, portadores `shared.*` nuevos, patrón send_email) se promueven
a `.claude/rules/` ANTES de borrar (fase 6).
