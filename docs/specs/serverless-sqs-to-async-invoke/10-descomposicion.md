# 10 — Descomposición para paralelización

[← 09 cleanup](09-cleanup-stream-processor.md) · [siguiente: 11 commits →](11-commits.md)

> Tareas atómicas. Cada una: File Exclusivity + Interface Stability + Bounded
> Scope. Orquestación: ver [orchestration.md](../../../.claude/rules/orchestration.md)
> — **≤4 agentes concurrentes**, **1 workflow a la vez**, Opus 4.8 por
> defecto. Suites (pytest/lint/build) por **Bash o 1-2 agentes**, NUNCA 1
> agente por suite. **NO hay `db_writer`** (el writer de tracking es específico).

## Leyenda

Cada tarea: **Archivos** · **AC** · **Depende de** · **Paralelizable con** ·
**Verify**.

## Base secuencial

- **T0 — Carpeta del plan + rama** · `docs/specs/serverless-sqs-to-async-invoke/**`
  · Dep: — · Verify: rama `feature/serverless-sqs-to-async-invoke` desde `dev`.

## Fase 0 — Medición (BLOQUEANTE, secuencial)

- **T1 — Baseline cold + SnapStart + after_restore hook** ·
  `shared/db/{warmup,snapstart}.py` + tests + doc de descomposición ·
  AC-1, AC-2 · Dep: T0 · Paral. con: — (gate del resto) · Verify:
  `serverless tests --type=unit --shared` + medición CloudWatch documentada.

## Fase 1 — Shared foundations

- **T2 — `shared.aws.lambda_invoke`** · `shared/aws/lambda_invoke.py` + 2 tests
  · AC-12 (parcial) · Dep: T1 · Paral. con T3 · Verify:
  `serverless tests --type=unit --shared` + `lint-deps --shared`
- **T3 — `shared.templating` (Jinja2)** ·
  `shared/templating/{__init__.py,jinja.py,pyproject.toml}` + tests · AC-9
  (parcial) · Dep: T1 · Paral. con T2 · Verify: idem

## Fase 2 — Devtools (T4/T5 paralelos; T6 tras ambos)

- **T4 — `uses.invokes` + `uses.buckets`** · `devtools/serverless/provisioner.py`
  + tests · AC-12, AC-13 · Dep: T1 · Paral. con T5 · Verify:
  `test_runner --module=devtools --type=unit`
- **T5 — recurso `s3-bucket` + tabla `email-config`** ·
  `devtools/serverless/infra_provision.py`, `resources/s3/email-templates.yaml`,
  `resources/dynamodb/email-config.yaml` + tests · AC-18 · Dep: T1 · Paral.
  con T4 · Verify: idem
- **T6 — quitar SQS de devtools** ·
  `devtools/serverless/{provisioner,infra_provision,lambda_controller,change_detector,flags,main,help}.py`
  + tests · AC-15 (parcial) · Dep: **T4, T5** · Verify: idem

## Fase 3 — Lambda `send_email`

- **T7 — `send_email` (lambda + tests)** · `services/send_email/**` · AC-9,
  AC-10, AC-16, AC-20 · Dep: T2, T3, T4, T5 · Paral. con T8/T9/T10 · Verify:
  `serverless tests --type=unit --lambda=send_email` (≥80%) +
  `lint-deps --lambda=send_email`
- **T7b — seed templates + email_config + comando devtools** ·
  `services/send_email/seeds/**`, comando seed en devtools · AC-19 · Dep: T7,
  T5 · Verify: dry-run del seed (deploy real en fase 8)

## Fase 4 — Encoders (un lambda cada uno, dirs disjuntos)

- **T8 — `contact_form`: quitar ASYNC_MODE + inline + invoke send_email** ·
  `services/contact_form/**` + tests · AC-6 · Dep: T2, T7 · Paral. con T9/T10 ·
  Verify: `serverless tests --type=unit --lambda=contact_form` + `lint-deps`
- **T9 — `tracking_pixel`: async-via-invoke (preserva 128 MB / cold 3.7s)** ·
  `services/tracking_pixel/**` + tests · AC-7 · Dep: T2 · Paral. con T8/T10 ·
  Verify: `serverless tests --type=unit --lambda=tracking_pixel` + `lint-deps`
- **T10 — `tracking_writer` (reconvertir worker SQS → invoke-target)** ·
  `services/tracking_worker/` → `tracking_writer/` (manifest direct + handler) +
  tests · AC-8 · Dep: T2 · Paral. con T8/T9 · Verify:
  `serverless tests --type=unit --lambda=tracking_writer` + `lint-deps`

## Fase 5 — cv cache

- **T11 — cv `@cached` DynamoDB + invalidación en seed** ·
  `services/cv/core/services/cv_service.py`, controllers cv.*, `db/seed_service`
  + tests · AC-3, AC-4 · Dep: T1 · Paral. con Fase 3/4 (dir cv disjunto) ·
  Verify: `serverless tests --type=unit --lambda=cv` (≥80%) + `lint-deps`

## Fase 6 — Migrar auth/users + borrar SQS

- **T12 — migrar `auth`** · `services/auth/{email_dispatch_service,manifest,pyproject}`
  · AC-16, AC-17 · Dep: T2, T7 · Paral. con T13
- **T13 — migrar `users`** · `services/users/{...}` · AC-16 · Dep: T2, T7 ·
  Paral. con T12 · Verify (T12/T13): `--lambda=<X>` + `lint-deps`
- **T14 — borrar colas SQS + shared.queue + 2 workers (NO tracking_worker)** ·
  eliminar `auth_email_worker`, `contact_worker`, `shared/queue/`,
  `resources/sqs/`; limpiar pyproject · AC-15 · Dep: **T8, T9, T10, T12, T13** ·
  Verify: `serverless tests --type=unit` + `lint-deps` +
  `rg "shared.queue|ASYNC_MODE"` → 0

## Fase 7 — Eliminar stream_processor + rules

- **T15 — destruir + limpiar `stream_processor`** · destroy stage/prod + refs ·
  AC-14 · Dep: T6, T14 · Paral. con T16 · Verify: `rg stream_processor` (fuera
  de `_archive/` + plan) → 0; `list-functions` sin stream-processor
- **T16 — promover convenciones a rules + CLAUDE.md + validar skills** ·
  `.claude/rules/*` (incl. lambda-config con los hallazgos cold), `CLAUDE.md` ·
  Dep: T6, T14 · Paral. con T15 · Verify: `claude -p` 5 ángulos

## Fase 8 — Verificación E2E + gate de cold (NO paralelizable)

- **T17 — batería E2E + deploy + seed + destroy + gate de cold + borrar plan** ·
  ver [13](13-verificacion-e2e.md) · Dep: TODO

## Granularidad — olas de ≤4 agentes

- **T1 secuencial primero** (Fase 0 es gate; nada empieza sin baseline).
- Ola A: T2, T3, T4, T5 (4; archivos disjuntos: lambda_invoke, templating,
  provisioner, infra_provision).
- T6 secuencial tras T4/T5 (re-tocan provisioner/infra).
- Ola B: T7 (+T7b tras T7).
- Ola C: T8, T9, T10, T11 (4; un lambda/dir disjunto: contact, tracking_pixel,
  tracking_writer, cv).
- Ola D: T12, T13 (auth, users).
- T14 secuencial tras Ola C+D.
- Ola E: T15, T16.
- T17 secuencial final.

17 tareas (Large).

[← 09 cleanup](09-cleanup-stream-processor.md) · [siguiente: 11 commits →](11-commits.md)
