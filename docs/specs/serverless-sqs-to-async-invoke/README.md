# Plan: backend serverless — cold start, eliminar SQS, email centralizado

> Reorienta el backend serverless con foco en **latencia real** (medida con
> datos duros de CloudWatch), además de eliminar SQS (3 colas + 3 DLQ),
> eliminar `ASYNC_MODE`, eliminar el Lambda real `stream_processor`, y
> centralizar el email en un Lambda `send_email` (config DynamoDB + templates
> S3 + Jinja2, invocado async con `InvocationType='Event'`). El async que
> sobrevive NO usa SQS: usa **invoke Lambda async**. Principio rector:
> **provider-swappable** — todo acceso AWS detrás de `shared.*`.

Escala: **Large**.

## Diagnóstico que reorienta el plan (leer PRIMERO)

La motivación inicial era "cold start lento". Una auditoría (workflow de 7
agentes + medición en vivo de CloudWatch/Lambda API, dev) probó con **datos
duros** que la causa NO es la que se creía:

| Hecho medido (CloudWatch dev) | Implicación |
|---|---|
| **SnapStart YA restaura** (`OptimizationStatus: On` en alias `:live` de los 5; `Restore Duration` cv 1.2-1.4s, auth 1.2s, users 0.9s) | Los **imports ya están en el snapshot**. El Init no es el cuello. |
| **cv.get tarda 7.3s INCLUSO caliente** (Handler Duration warm) | No es cold start: es la **query** (fan-out de 11 secciones a Neon). |
| cv cold 10.1s handler vs 7.3s warm → el cold agrega solo ~2.8s | Ese ~2.8s = **wake de Neon scale-to-zero** + connect SSL. |
| Roundtrip api_e2e cv 13.9s = 1.2s restore + 10.1s handler + ~2.6s red | ~2.6s es **red WSL2(Chile)→us-east-1** del harness, NO del Lambda. |
| `tracking_pixel` (sin Neon) cold 3.7s — el mejor | Confirma: sin Neon, no hay cold de 2 dígitos. |

**Conclusión central**: lo que se llamaba "cold start" es, en su mayoría, **(a)
una query lenta de cv + (b) el wake de Neon**. Los **lazy imports tienen ROI
~nulo** (y pueden EMPEORAR: sacar imports del module-scope los saca del
snapshot de SnapStart → se pagan en el handler CPU-starved). El detalle en
[02-fase-0](02-fase-0-medicion-coldstart.md) y
`tmp/cold-start-analysis/08-diagnostico-final-datos-duros.md`.

→ El foco del plan se **reorienta**: de "lazy imports" a **cache de reads
(cv) + reducir el toque a Neon + verificar SnapStart**, manteniendo los
objetivos previos (−SQS, send_email, −ASYNC_MODE, −stream_processor).

## Cuándo leer cada archivo

| Archivo | Cuándo leer |
|---------|-------------|
| [01-contexto-y-decision.md](01-contexto-y-decision.md) | Problema, diagnóstico, solución, AC-1..AC-20 |
| [02-fase-0-medicion-coldstart.md](02-fase-0-medicion-coldstart.md) | **Fase 0 (bloqueante)**: medir SnapStart + descomponer el cold + after_restore hook |
| [03-shared-foundations.md](03-shared-foundations.md) | `shared.aws.lambda_invoke` (invoke async) + `shared.templating` (Jinja2) |
| [04-devtools-provisioning.md](04-devtools-provisioning.md) | `uses.invokes`, `uses.buckets`, recurso S3, tabla email-config, quitar SQS |
| [05-send-email-lambda.md](05-send-email-lambda.md) | Lambda `send_email` + tabla `email-config` + templates S3 |
| [06-encoders-refactor.md](06-encoders-refactor.md) | `contact_form` inline + `tracking_pixel` async-via-invoke (preserva su cold) |
| [07-cv-cache.md](07-cv-cache.md) | **cv @cached DynamoDB** (el mayor impacto absoluto) + query fan-out |
| [08-migrate-callers-remove-sqs.md](08-migrate-callers-remove-sqs.md) | auth/users → send_email; borrar colas SQS + `shared.queue`; convertir workers |
| [09-cleanup-stream-processor.md](09-cleanup-stream-processor.md) | **Eliminar el Lambda real `stream_processor`** (existe en stage/prod) + rules |
| [10-descomposicion.md](10-descomposicion.md) | Sección 8 — tareas atómicas + paralelización |
| [11-commits.md](11-commits.md) | Sección 9 — secuencia de commits |
| [12-paralelizacion-worktrees.md](12-paralelizacion-worktrees.md) | Sección 10 — worktrees / olas de agentes |
| [13-verificacion-e2e.md](13-verificacion-e2e.md) | Sección 11 — batería + gate de cold (medido en CloudWatch) |

## Estado por fase

| Fase | Archivo | Estado |
|------|---------|--------|
| 0 | Medición + SnapStart (02) | `pending` |
| 1 | Shared foundations (03) | `pending` |
| 2 | Devtools provisioning (04) | `pending` |
| 3 | Lambda `send_email` (05) | `pending` |
| 4 | Encoders refactor (06) | `pending` |
| 5 | cv cache (07) | `pending` |
| 6 | Migrar auth/users + borrar SQS (08) | `pending` |
| 7 | Eliminar `stream_processor` + rules (09) | `pending` |
| 8 | Verificación E2E + gate de cold (13) | `pending` |

## Decisiones no-reabribles (confirmadas con el usuario)

1. **Fase 0 bloqueante**: medir SnapStart en runtime + descomponer el cold
   (Init/Restore vs Neon wake vs query) con CloudWatch ANTES de tocar el
   refactor. No optimizar a ciegas.
2. **NO lazy imports como foco.** Los datos prueban ROI ~nulo con SnapStart
   activo; el lazy correcto (fido2/argon2 por acción, `__init__` vacíos) ya
   está aplicado. Sólo se tocan imports eager redundantes puntuales SI la
   medición confirma que no empeoran el restore.
3. **NUNCA subir memoria.** El cuello es Neon I/O, no CPU. Subir memoria no
   toca el wake de Neon ni la query.
4. **`contact_form` → escritura inline síncrona** (form, baja frecuencia, el
   usuario espera la respuesta igual) + invoca `send_email` async siempre.
5. **`tracking_pixel` → async SIN SQS**: invoca async (`InvocationType='Event'`)
   a un writer Lambda (el `tracking_worker` reconvertido de SQS-consumer a
   invoke-target). **Preserva su cold de 3.7s** (no toca Neon en el request).
   Fire-and-forget (sendBeacon: el browser no espera).
6. **`cv` → `@cached` DynamoDB** (módulo `shared/cache/` ya existe). Cache hit
   no toca Neon → cv pasa de 13.9s/7.3s a ~restore/~GetItem. Mayor impacto
   absoluto. Incluido en este plan.
7. **Eliminar SQS** (3 colas + 3 DLQ) + `shared.queue` + `ASYNC_MODE`.
8. **`send_email` puro**: DynamoDB (config) + S3 (template) + Jinja2 + SES. NO
   toca Neon. Tabla `email-config` (PK=`kind`), una plantilla por kind (10).
9. **`stream_processor` SE ELIMINA de verdad**: existe como Lambda en stage y
   prod (consume DynamoDB Streams de `contacts` + `tracking`). Es un `destroy`
   real, no sólo borrar refs de código.
10. **Provider-swappable**: AWS detrás de `shared.*`. Nuevos:
    `shared.aws.lambda_invoke`, `shared.templating`. Reusados: `shared.aws.s3`,
    `shared.aws.ses`, `shared.db`, `shared.cache`.

## Reglas críticas (siempre activas)

- **SIEMPRE** medir el cold con `Restore Duration`/`Init Duration`/`Duration`
  de la REPORT line de CloudWatch — NUNCA con el roundtrip httpx del harness
  (incluye red WSL2→us-east-1).
- **SIEMPRE** verificar SnapStart con `--qualifier live` (el alias que invoca
  API GW). Sin `--qualifier` consulta `$LATEST` que SIEMPRE da `Off`.
- **SIEMPRE** los `core/**/*.py` importan AWS sólo vía `shared.*`. `lint-deps`
  verde. Los `__init__.py` de `shared/*` quedan VACÍOS.
- **SIEMPRE** los imports incondicionales van al top del módulo (snapshot de
  SnapStart), NO al `preload()` ni al handler.
- **SIEMPRE** invocación async = `InvocationType='Event'`; el caller no espera;
  degrada a log si falla (no rompe el request).
- **SIEMPRE** `memory`/`timeout` = MÍNIMO medido (`.claude/rules/lambda-config.md`).
- **SIEMPRE** TDD: test primero, asserts EXACTOS, coverage ≥80% per-file.
- **NUNCA** atribución de IA. **NUNCA** reintroducir SQS. **NUNCA** subir
  memoria para enmascarar latencia. **NUNCA** `db_writer` genérico (el writer
  de tracking es específico y async-via-invoke, no un slave genérico).

## Ciclo de vida

Carpeta **efímera**: el último commit (fase 8) la elimina con `git rm -r`. Las
convenciones que sobreviven (formato `uses.invokes`/`uses.buckets`, portadores
`shared.*` nuevos, patrón send_email, hallazgos de cold start) se promueven a
`.claude/rules/` ANTES de borrar (fase 7).
