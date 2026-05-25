# Plan: lambdas-async-sqs

> Desacoplar los endpoints `/contact` y `/track` de la escritura sincronica
> a Neon (causa del cold-start de 10s percibido por el cliente) introduciendo
> 2 colas SQS + 2 workers Lambda dedicados (`contact_worker`, `tracking_worker`).
> Las Lambdas HTTP existentes pasan a ser **encoders** ligeros: validan,
> rate-limit, Turnstile (solo `/contact`), encolan y responden 202 inmediato.
> Los workers consumen SQS y hacen el trabajo pesado (Neon + SES) fuera del
> path de la respuesta HTTP.

## Estado de fases

| # | Fase | Tipo | Archivo | Estado |
|---|------|------|---------|--------|
| 0 | Contexto + Solucion + AC | Diseno | [01-contexto-y-decision.md](01-contexto-y-decision.md) | pending |
| 1 | Recursos SQS + CloudWatch (YAMLs) | Infra | [02-resources-sqs-cloudwatch.md](02-resources-sqs-cloudwatch.md) | pending |
| 2 | Extensiones devtools (provisioner) | Tooling | [03-devtools-extensions.md](03-devtools-extensions.md) | pending |
| 3 | Helper `shared/queue/` (publisher SQS) | Codigo | [04-shared-queue-publisher.md](04-shared-queue-publisher.md) | pending |
| 4 | Idempotencia ORM (`ON CONFLICT`) | Codigo | [09-idempotencia-orm.md](09-idempotencia-orm.md) | pending |
| 5 | Worker `contact_worker` | Codigo | [05-contact-worker.md](05-contact-worker.md) | pending |
| 6 | Worker `tracking_worker` | Codigo | [06-tracking-worker.md](06-tracking-worker.md) | pending |
| 7 | Refactor `contact_form` (encoder) | Codigo | [07-refactor-contact-form-encoder.md](07-refactor-contact-form-encoder.md) | pending |
| 8 | Refactor `tracking_pixel` (encoder) | Codigo | [08-refactor-tracking-pixel-encoder.md](08-refactor-tracking-pixel-encoder.md) | pending |
| 9 | Lista de commits | Ejecucion | [10-commits.md](10-commits.md) | pending |
| 10 | Paralelizacion con git worktrees | Ejecucion | [11-paralelizacion-worktrees.md](11-paralelizacion-worktrees.md) | pending |
| 11 | Verificacion E2E iterativa | Ejecucion | [12-verificacion-e2e.md](12-verificacion-e2e.md) | pending |

## Decisiones tomadas (no reabrir)

| # | Decision | Razon |
|---|----------|-------|
| 1 | **SQS enqueue + worker** (no async Lambda invoke, no keep-warm) | Patron estandar AWS, DLQ + retry nativos, observabilidad, $0/mes free tier. |
| 2 | **2 colas separadas** (una por endpoint) + 2 workers | Aisla fallos; tracking puede caer sin afectar contact emails. |
| 3 | **Rate-limit + Turnstile + auto-blacklist en la Lambda HTTP** (antes de encolar) | Protege la cola y al worker del spam; rechazo inmediato 429/403. |
| 4 | **`/contact` responde `202 Accepted` + `contact_id` UUIDv7 pre-generado** | Cliente recibe id de tracking; permite mostrar "tu mensaje #ABC esta procesandose". |
| 5 | **`/track` responde `202 Accepted`** (antes 204) | 202 expresa correctamente "encolado para procesar". |
| 6 | **Batch size 10 + `ReportBatchItemFailures` para tracking; 1 para contact** | tracking comparte cold-start de Neon entre eventos; contact necesita aislamiento de email failures. |
| 7 | **Idempotencia via UUIDv7 PK + `ON CONFLICT DO NOTHING`** | contact: PK `id`; tracking: PK compuesta `(created_at, visit_id, page_id)` — pre-generamos lo posible en la HTTP. |
| 8 | **DLQ + retry x3 + CloudWatch alarm** (en el mismo PR) | Observabilidad desde dia 1. |
| 9 | **Feature flag `ASYNC_MODE=true/false` env var** | Rollback rapido sin redeploy ante imprevistos. |
| 10 | **Local dev: modo direct (sin LocalStack)** | Consistente con como ya operamos los otros lambdas; el worker es funcion Python normal. |
| 11 | **Naming: `contact_worker` / `tracking_worker`** | Corto y separa producer/consumer. |
| 12 | **Latencia del email del owner**: 5-15s post-submit es OK | Patron normal de forms de contacto. |
| 13 | **Branch**: `feature/lambdas-async-sqs` desde `dev`. PR a `dev` | Estandar del repo. |

## Reglas criticas

- **SIEMPRE** la Lambda HTTP responde con `2xx` ANTES de tocar Neon. La unica
  excepcion son rate-limit (429) y Turnstile invalido (403) — esos se rechazan
  antes de encolar.
- **SIEMPRE** los UUIDv7 (`contact_id`, `page_id`) se generan en la Lambda
  HTTP y viajan en el mensaje SQS. El worker NUNCA los regenera.
- **SIEMPRE** los workers son idempotentes: si SQS re-entrega el mismo
  mensaje, el INSERT a Neon es no-op (`ON CONFLICT DO NOTHING`).
- **SIEMPRE** Turnstile + auto-blacklist corren en la Lambda HTTP. Esto
  preserva la deteccion "3+ tokens validos en 60s" antes del encolado.
- **SIEMPRE** el feature flag `ASYNC_MODE` mapea a 2 branches: `true` =
  encoder + cola; `false` = comportamiento sync actual (rollback).
- **SIEMPRE** el `manifest.yaml` de los workers declara `trigger.type: sqs`
  con `function_response_types: [ReportBatchItemFailures]`.
- **NUNCA** un worker hace `time.sleep` esperando que Neon despierte — el
  cold-start es parte del costo aceptado; lo que importa es que el cliente
  no lo vea.
- **NUNCA** se logea el `cf_token` ni el `bypass_secret` (ya cubierto por
  el handler HTTP actual; mantener al portar al encoder).
- **NUNCA** el worker reintenta indefinidamente. SQS retry x3 -> DLQ.
- **NUNCA** se commitea el state local (`.state/` esta gitignored).

## Matriz de verificacion incremental

| Fase | Verificacion antes de commitear |
|------|--------------------------------|
| 1 | `python -c "from serverless.infra_resources import RESOURCES_DIR; ..."` (catalogo carga limpio) |
| 2 | `pytest devtools/tests/serverless/test_infra_provision.py` (provisioner cubre `sqs-queue` con redrive + `cloudwatch-alarm`) |
| 3 | `pytest serverless/lambda/shared/queue/tests/` (helper publish + serializacion + tests) |
| 4 | `pytest serverless/lambda/shared/db/tests/test_repository_idempotent.py` |
| 5 | `serverless tests --type=unit --lambda=contact_worker` |
| 6 | `serverless tests --type=unit --lambda=tracking_worker` |
| 7 | `serverless tests --type=unit --lambda=contact_form` (encoder + flag) |
| 8 | `serverless tests --type=unit --lambda=tracking_pixel` (encoder + flag) |
| Final | seccion 11 (lint + typecheck + unit + integration + e2e + deploy dev + smoke contra api.portfolio.dev) |

## Costo estimado

| Recurso | Coste/mes |
|---------|-----------|
| SQS 4 colas (2 main + 2 DLQ) | $0 (free tier: 1M req/mes; estimado <50k) |
| 2 nuevos Lambda workers | $0 (free tier: 1M invocaciones; estimado <50k) |
| CloudWatch 2 alarmas | $0.20 (10 alarmas free) |
| CloudWatch logs extra | <$0.10 (retention 7d) |
| **Total incremental** | **<$0.30/mes** |

## Anti-patrones del plan

| Anti-patron | Por que |
|-------------|---------|
| Hacer el worker "async" con `async def` (asyncio) | NO arregla cold-start de Neon; agrega complejidad sin beneficio |
| Pasar el `cf_token` al worker para validar Turnstile alla | Encola spam, gasta SQS, expone tokens fuera del fast-path |
| Generar `contact_id` en el worker | Imposible devolver al cliente; rompe idempotencia |
| Usar Powertools `@idempotent` en vez de `ON CONFLICT` | Suma costo DynamoDB innecesario; UUIDv7 + PK ya garantiza unicidad |
| Compartir 1 sola cola para los 2 endpoints | Acopla criterios de retry/batch; impacto cruzado en fallas |
| Mergear el plan sin la alarma CloudWatch | Deja DLQ sin observabilidad; bug silencioso |
| Saltar el feature flag | Bloquea rollback rapido; cualquier issue obliga a redeploy |

## TODO post-merge

- [ ] Tras 1-2 semanas de async en prod sin issues, eliminar el feature flag
  `ASYNC_MODE` y la rama sync (commit de cleanup en PR aparte).
- [ ] Considerar promover a una rule `.claude/rules/sqs-worker-pattern.md` el
  patron de "Lambda HTTP encoder + worker SQS" si se aplica a futuros
  endpoints (ej. `/cv` si crece).
