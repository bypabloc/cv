# contact-form-latency-optim

> Plan compuesto de optimizaciones de latencia del Lambda `contact_form` en
> los 3 envs (dev/stage/prod). Ataca el handler post-SnapStart, hoy en
> 2.5-4s, con 3 quick wins: paralelizar las 4 DDB del rate_limit con
> `ThreadPoolExecutor`, pre-calentar handshakes TLS de boto3 en un
> `beforeCheckpoint` SnapStart hook generico opt-in via manifest, y dejar
> el orden actual de validaciones (`rate_limit -> Turnstile -> auto_blacklist`)
> tal cual.

## Cuando leer

| Tema | Archivo |
|------|---------|
| Contexto + decisiones + AC | [01-contexto-y-decision.md](01-contexto-y-decision.md) |
| Fase A: paralelizar rate_limit | [02-fase-a-paralelizar-rate-limit.md](02-fase-a-paralelizar-rate-limit.md) |
| Fase B: SnapStart warmup hook generico | [03-fase-b-snap-start-warmup.md](03-fase-b-snap-start-warmup.md) |
| Fase C: wire contact_form al kit shared | [04-fase-c-wire-contact-form.md](04-fase-c-wire-contact-form.md) |
| Commits (10 commits incrementales) | [05-commits.md](05-commits.md) |
| Paralelizacion con git worktrees (2 worktrees) | [06-paralelizacion-worktrees.md](06-paralelizacion-worktrees.md) |
| Verificacion E2E iterativa + tabla metricas | [07-verificacion-e2e.md](07-verificacion-e2e.md) |

## Estado por fase

| Fase | Archivos clave | Estado |
|------|----------------|--------|
| A: rate_limit paralelo | `shared/rate_limit/check.py` + tests | pending |
| B: SnapStart warmup hook | `shared/lambda_kit/snap_start_warmup.py` (NUEVO) + tests | pending |
| C: wire contact_form | `services/contact_form/core/handler.py` + `manifest.yaml` | pending |

## Decisiones no-reabribles

| # | Decision | Razon |
|---|----------|-------|
| 1 | **Scope: solo contact_form** | tracking_pixel NO usa Turnstile; el cold start no es bloqueante alli (sendBeacon es fire-and-forget client-side). |
| 2 | **Orden validaciones SIN CAMBIO**: rate_limit -> Turnstile -> auto_blacklist | Rate_limit protege Turnstile de DoS (un GetItem cuesta $0.0000025; el verify HTTP a Cloudflare cuesta ~500ms + es la API de un 3er actor). Cambiar el orden NO esta en scope. |
| 3 | **Paralelizacion DDB: las 4 siempre, con ThreadPoolExecutor(max_workers=4)** | Lanzar las 4 lookups (ip_rule, country_rule, endpoint_rule, effective_count) en paralelo y aplicar la logica condicional sobre los 4 resultados. Si la IP esta blacklisteada gastamos 3 DDB reads "inutiles" (~$0.0000001 cada uno — irrelevante). Beneficio: latencia = max(4) en vez de sum(4). |
| 4 | **auto_blacklist queda en el encoder, secuencial al final** | El INCREMENT post-Turnstile-valido se mantiene en el path HTTP del encoder. NO se mueve al worker. NO se paraleliza con el SQS publish (riesgo de inconsistencia si SQS falla). |
| 5 | **SnapStart warmup hook GENERICO en shared/lambda_kit, opt-in via manifest** | `register_warmup(clients=['sqs','dynamodb','ssm'])` se invoca en el INIT de cada lambda que lo necesite. `contact_form` lo activa via `manifest.snap_start_warmup: [sqs, dynamodb, ssm]`. Otros lambdas pueden adoptarlo despues sin tocar shared. |
| 6 | **Warmup calls: handshake TLS con metodos read-only AWS (NO recursos del proyecto)** | `ssm list_parameters --max-items=1`, `dynamodb describe_endpoints`, `sqs list_queues --max-items=1`. Si alguno falla, fallback silencioso (try/except, log WARNING, no propaga). Evita race condition de deploy nuevo donde el recurso aun no existe. |
| 7 | **Concurrency: concurrent.futures.ThreadPoolExecutor** | Sync API, boto3 es thread-safe, sin asyncio, sin deps nuevas. Test facil con mocks. |
| 8 | **1 PR atomico** | Las 3 optimizaciones atacan el mismo problema (cold start). Mas facil correlacionar speedup en logs con un solo deploy. Promocion dev->stage->main una sola vez. |
| 9 | **Worktrees: 2** | Worktree A: shared/ (rate_limit paralelo + snap_start_warmup hook + tests). Worktree B: contact_form/ (handler wirea el hook + manifest). B depende de A pero ambos pueden avanzar tras commitear la base secuencial. |
| 10 | **Verificacion E2E es GATE con tabla metricas** | Antes de mergear, capturar 10 mediciones del estado actual de prod. Tras deploy de cada env, capturar 10 mas. El ultimo commit (verify E2E) requiere la tabla `dev|stage|prod | Restore | Validate | Execute | Total` en verde como evidencia. Sin tabla, el plan NO esta listo para mergear. |

## Reglas criticas

- **SIEMPRE** correr los tests de `shared/rate_limit/` y `shared/lambda_kit/` antes de wirearlo en el lambda. Si la version paralela rompe el contrato, lo agarra el test, no el smoke en prod.
- **SIEMPRE** el SnapStart warmup hook tiene `try/except Exception` que loguea WARNING y continua. NUNCA debe abortar el INIT del lambda — si el handshake falla, la lambda arranca normal y la primera invocacion paga el TLS cost (degradacion graceful).
- **SIEMPRE** el `ThreadPoolExecutor` del rate_limit usa `max_workers=4` (matchea la cantidad de lookups) y se construye DENTRO de `check_or_raise` por request (no module-scope — los handles del executor no son SnapStart-safe).
- **NUNCA** cambiar el orden actual (rate_limit -> Turnstile -> auto_blacklist).
- **NUNCA** mover auto_blacklist al worker.
- **NUNCA** introducir asyncio/aioboto3 — el patron de este repo es sync boto3 con `concurrent.futures` cuando hace falta paralelizar.

## Matriz de verificacion

| Cambio | Test unitario | Test integracion | Smoke real |
|--------|---------------|------------------|------------|
| rate_limit paralelo | `tests/unit/.../test_check.py` (4 nuevos casos) | `tests/integration/.../test_check_parallel.py` (DDB local moto) | Smoke `/contact` dev con bypass: HTTP 202 + Restore Duration |
| SnapStart warmup hook | `tests/unit/.../test_snap_start_warmup.py` (4 casos: success, partial fail, total fail, fallback silencioso) | N/A (boto3 mock suficiente) | CloudWatch: ver `[warmup]` log lines en RESTORE_REPORT del cold start |
| contact_form wire | N/A (test del controller existente sigue verde) | N/A | Smoke `/contact` los 3 envs + tabla antes/despues |
