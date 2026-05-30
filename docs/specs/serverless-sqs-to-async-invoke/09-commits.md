# 09 — Commits

[← 08 descomposición](08-descomposicion.md) · [siguiente: 10 worktrees →](10-paralelizacion-worktrees.md)

> Conventional Commits en español. Cada commit deja el repo verde (lint +
> compileall + tests del scope) y ejecuta su verificación incremental ANTES
> de commitear. Un solo PR `feature/serverless-sqs-to-async-invoke → dev`.
> **NO hay commit de `db_writer`.**

## Secuencia

1. **`docs(specs): plan eliminar SQS + email centralizado + encoders sync`** (T0)
   - La carpeta del plan. Verify: markdown válido.

2. **`feat(shared): portador shared.aws.lambda_invoke para invoke async`** (T1)
   - `shared/aws/lambda_invoke.py` + tests.
   - Verify: `serverless tests --type=unit --shared` + `lint-deps --shared`.

3. **`feat(shared): portador shared.templating con Jinja2`** (T2)
   - `shared/templating/**` + tests. Verify: idem.

3b. **`feat(shared): shared.db.read_async (gather de reads concurrentes)`** (T2b)
   - `shared/db/read_async.py` + tests. Patrón para reads multi-query del
     dashboard; sin consumidor en este plan (decisión del usuario).
   - Verify: `serverless tests --type=unit --shared` + `lint-deps --shared`.

4. **`feat(devtools): uses.invokes + uses.buckets en el provisioner`** (T3)
   - `provisioner.py` + tests. Verify: `test_runner --module=devtools --type=unit`.

5. **`feat(devtools): recurso s3-bucket + tabla email-config`** (T4)
   - `infra_provision.py`, `resources/s3/email-templates.yaml`,
     `resources/dynamodb/email-config.yaml` + tests. Verify: idem.

6. **`refactor(devtools): elimina soporte de SQS del provisioning`** (T5)
   - Quita trigger sqs + uses.queues + _provision_sqs_queue + tests sqs.
   - Verify: `test_runner --module=devtools --type=unit`.

7. **`feat(send_email): lambda puro de email (DynamoDB+S3+Jinja2+SES)`** (T6)
   - `services/send_email/**`. Verify:
     `serverless tests --type=unit --lambda=send_email` (≥80%) +
     `lint-deps --lambda=send_email`.

8. **`feat(send_email): seed de email-config + templates S3`** (T6b)
   - `services/send_email/seeds/**` + comando seed devtools. Verify: dry-run
     del seed; `test_runner --module=devtools --type=unit`.

9. **`refactor(contact_form): escritura Neon inline + invoke send_email, sin ASYNC_MODE`** (T7)
   - `contact_form/**` + tests. Verify:
     `serverless tests --type=unit --lambda=contact_form` + `lint-deps`.

10. **`refactor(tracking_pixel): escritura Neon inline (256MB), sin ASYNC_MODE`** (T8)
    - `tracking_pixel/**` + tests. Verify:
      `serverless tests --type=unit --lambda=tracking_pixel` + `lint-deps`.
    - Body: documentar el bump de memoria 128→256 con la razón (shared.db).

11. **`refactor(auth): invoca send_email async en vez de SQS`** (T9)
    - `auth/{email_dispatch_service,manifest,pyproject}`. Verify:
      `--lambda=auth` + lint-deps.

12. **`refactor(users): invoca send_email async en vez de SQS`** (T10)
    - `users/{...}`. Verify: `--lambda=users` + lint-deps.

13. **`refactor(serverless): elimina los 3 workers SQS, shared.queue y colas`** (T11)
    - Borra `auth_email_worker`, `contact_worker`, `tracking_worker`,
      `shared/queue/`, `resources/sqs/`; limpia pyproject.
    - Verify: `serverless tests --type=unit` (suite) + `lint-deps` +
      `rg "shared.queue|ASYNC_MODE"` → 0.

14. **`refactor(backend): elimina toda referencia a stream_processor`** (T12)
    - Código + docs + devtools. Verify: `rg stream_processor` (fuera de
      `_archive/` y la carpeta del plan) → 0.

15. **`docs(rules): promueve uses.invokes/buckets + portadores a rules`** (T13)
    - `.claude/rules/*`, `CLAUDE.md`. Verify: `claude -p` 5 ángulos.

16. **`test(serverless): verificacion E2E + medicion cold start + elimina spec`** (T14)
    - Incluye `git rm -r docs/specs/serverless-sqs-to-async-invoke/`.
    - Verify: batería completa de [11](11-verificacion-e2e.md) en verde.

## PR

- Único: `feature/serverless-sqs-to-async-invoke → dev`, merge commit.
- Body: Problema / Solución / Cómo probar (reusa la batería de la sección 11)
  / TODO (incluir: medición de cold start + tradeoff memoria tracking_pixel).
  Sin atribución de IA.

[← 08 descomposición](08-descomposicion.md) · [siguiente: 10 worktrees →](10-paralelizacion-worktrees.md)
