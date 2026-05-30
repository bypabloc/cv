# 08 — Descomposición para paralelización

[← 07 cleanup](07-cleanup-stream-processor.md) · [siguiente: 09 commits →](09-commits.md)

> Tareas atómicas. Cada una: File Exclusivity + Interface Stability + Bounded
> Scope. Orquestación: ver [orchestration.md](../../../.claude/rules/orchestration.md)
> — **≤4 agentes concurrentes**, **1 workflow a la vez**, Opus 4.8 por
> defecto. Las suites (pytest/lint/build) van por **Bash o 1-2 agentes**,
> NUNCA 1 agente por suite. **NO hay `db_writer`.**

## Leyenda

Cada tarea: **Archivos** · **AC** · **Depende de** · **Paralelizable con** ·
**Verify**.

## Base secuencial

- **T0 — Carpeta del plan + rama** · `docs/specs/serverless-sqs-to-async-invoke/**`
  · Dep: — · Verify: rama `feature/serverless-sqs-to-async-invoke` desde `dev`,
  carpeta commiteada.

## Fase 1 — Shared foundations

- **T1 — `shared.aws.lambda_invoke`** · `shared/aws/lambda_invoke.py` + 2 tests
  · AC-6 (parcial) · Dep: T0 · Paral. con T2 · Verify:
  `serverless tests --type=unit --shared` + `lint-deps --shared`
- **T2 — `shared.templating` (Jinja2)** ·
  `shared/templating/{__init__.py,jinja.py,pyproject.toml}` + tests · AC-3
  (parcial) · Dep: T0 · Paral. con T1 · Verify: idem
- **T2b — `shared.db.read_async` (patrón read concurrente, sin consumidor en
  este plan)** · `shared/db/read_async.py` + tests · AC: — (decisión del
  usuario) · Dep: T0 · Paral. con T1/T2 · Verify:
  `serverless tests --type=unit --shared` + `lint-deps --shared`

## Fase 2 — Devtools (T3/T4 paralelos; T5 tras ambos)

- **T3 — `uses.invokes` + `uses.buckets`** · `devtools/serverless/provisioner.py`
  + tests · AC-6, AC-7 · Dep: T0 · Paral. con T4 (archivo distinto) · Verify:
  `test_runner --module=devtools --type=unit`
- **T4 — recurso `s3-bucket` + tabla `email-config`** ·
  `devtools/serverless/infra_provision.py`, `resources/s3/email-templates.yaml`,
  `resources/dynamodb/email-config.yaml` + tests · AC-13 · Dep: T0 · Paral.
  con T3 · Verify: idem
- **T5 — quitar SQS de devtools** ·
  `devtools/serverless/{provisioner,infra_provision,lambda_controller,change_detector,flags,main,help}.py`
  + tests · AC-9 (parcial) · Dep: **T3, T4** · Paral. con: — · Verify: idem

## Fase 3 — Lambda `send_email`

- **T6 — `send_email` (lambda + tests)** · `services/send_email/**` · AC-3,
  AC-4, AC-12, AC-16 · Dep: T1, T2, T3, T4 · Paral. con T7/T8 (dirs distintos)
  · Verify: `serverless tests --type=unit --lambda=send_email` (≥80%) +
  `lint-deps --lambda=send_email`
- **T6b — seed templates + email_config + comando devtools** ·
  `services/send_email/seeds/**`, comando seed en devtools · AC-14 · Dep: T6,
  T4 · Verify: dry-run del seed (deploy real en fase 7)

## Fase 4 — Encoders refactor (un lambda cada uno, dirs disjuntos)

- **T7 — `contact_form`: quitar ASYNC_MODE + escritura inline + invoke send_email**
  · `services/contact_form/**` + tests · AC-1, AC-5 · Dep: T1, T6 · Paral.
  con T8 · Verify: `serverless tests --type=unit --lambda=contact_form` +
  `lint-deps --lambda=contact_form`
- **T8 — `tracking_pixel`: quitar ASYNC_MODE + escritura inline (256 MB)** ·
  `services/tracking_pixel/**` + tests · AC-2, AC-5 · Dep: T1 · Paral. con T7
  · Verify: `serverless tests --type=unit --lambda=tracking_pixel` +
  `lint-deps --lambda=tracking_pixel`

## Fase 5 — Migrar auth/users + borrar SQS

- **T9 — migrar `auth`** · `services/auth/{email_dispatch_service,manifest,pyproject}`
  · AC-10, AC-11 · Dep: T1, T6 · Paral. con T10
- **T10 — migrar `users`** · `services/users/{...}` · AC-10 · Dep: T1, T6 ·
  Paral. con T9
  - Verify (T9/T10): `serverless tests --type=unit --lambda=<X>` + `lint-deps --lambda=<X>`
- **T11 — borrar workers + shared.queue + resources/sqs** · eliminar 3 workers,
  `shared/queue/`, `resources/sqs/`; limpiar pyproject de los 4 callers · AC-9
  · Dep: **T7, T8, T9, T10** · Paral. con: — · Verify:
  `serverless tests --type=unit` (suite) + `lint-deps` + `rg "shared.queue|ASYNC_MODE"` → 0

## Fase 6 — Limpieza stream_processor + rules

- **T12 — limpiar `stream_processor`** · ver [07](07-cleanup-stream-processor.md) §7.1
  · AC-8 · Dep: T5, T11 · Paral. con T13 · Verify: `rg stream_processor`
  (fuera de `_archive/` y la carpeta del plan) → 0
- **T13 — promover convenciones a rules + CLAUDE.md + validar skills** ·
  `.claude/rules/*`, `CLAUDE.md` · Dep: T5, T11 · Paral. con T12 · Verify:
  `claude -p` 5 ángulos (`.claude/rules/claude-config-testing.md`)

## Fase 7 — Verificación E2E (NO paralelizable)

- **T14 — batería E2E + deploy dev + seed + smoke + medir cold start + borrar
  carpeta del plan** · ver [11](11-verificacion-e2e.md) · Dep: TODO

## Granularidad — olas de ≤4 agentes

- Ola A: T1, T2, T2b, T3 (4; archivos disjuntos: lambda_invoke, templating,
  db/read_async, provisioner).
- Ola A2: T4 (infra_provision) + T5 tras T3/T4 (secuencial, re-tocan provisioner).
- Ola B: T6 (+T6b tras T6).
- Ola C: T7, T8, T9, T10 (4; un lambda cada uno, dirs disjuntos).
- T11 secuencial tras Ola C.
- Ola D: T12, T13.
- T14 secuencial final.

16 tareas (Large).

[← 07 cleanup](07-cleanup-stream-processor.md) · [siguiente: 09 commits →](09-commits.md)
