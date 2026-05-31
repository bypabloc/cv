# 11 — Commits

[← 10 descomposición](10-descomposicion.md) · [siguiente: 12 worktrees →](12-paralelizacion-worktrees.md)

> Conventional Commits en español. Cada commit deja el repo verde (lint +
> compileall + tests del scope) y ejecuta su verificación incremental ANTES
> de commitear. Un solo PR `feature/serverless-sqs-to-async-invoke → dev`.

## Secuencia

1. **`docs(specs): plan cold start + eliminar SQS + email centralizado`** (T0)
   - La carpeta del plan. Verify: markdown válido.

2. **`perf(shared): after_restore hook + baseline cold start (Fase 0)`** (T1)
   - `shared/db/{warmup,snapstart}.py` + tests + descomposición del cold
     documentada (CloudWatch). **Commit gate**: nada sigue sin esto.
   - Verify: `serverless tests --type=unit --shared` + SnapStart `:live` On.

3. **`feat(shared): portador shared.aws.lambda_invoke para invoke async`** (T2)
   - `shared/aws/lambda_invoke.py` + tests. Verify: `--shared` + `lint-deps`.

4. **`feat(shared): portador shared.templating con Jinja2`** (T3)
   - `shared/templating/**` + tests. Verify: idem.

5. **`feat(devtools): uses.invokes + uses.buckets en el provisioner`** (T4)
   - `provisioner.py` + tests. Verify: `test_runner --module=devtools --type=unit`.

6. **`feat(devtools): recurso s3-bucket + tabla email-config`** (T5)
   - `infra_provision.py`, `resources/s3/email-templates.yaml`,
     `resources/dynamodb/email-config.yaml` + tests. Verify: idem.

7. **`refactor(devtools): elimina soporte de SQS del provisioning`** (T6)
   - Quita trigger sqs + uses.queues + _provision_sqs_queue + tests sqs.
   - Verify: `test_runner --module=devtools --type=unit`.

8. **`feat(send_email): lambda puro de email (DynamoDB+S3+Jinja2+SES)`** (T7)
   - `services/send_email/**`. Verify:
     `serverless tests --type=unit --lambda=send_email` (≥80%) + `lint-deps`.

9. **`feat(send_email): seed de email-config + templates S3`** (T7b)
   - `services/send_email/seeds/**` + comando seed devtools. Verify: dry-run.

10. **`refactor(contact_form): escritura Neon inline + invoke send_email, sin ASYNC_MODE`** (T8)
    - `contact_form/**` + tests. Verify: `--lambda=contact_form` + `lint-deps`.

11. **`refactor(tracking_pixel): async via invoke (sin SQS, 128MB)`** (T9)
    - `tracking_pixel/**` + tests. Body: documentar que se MANTIENE 128 MB y el
      cold ~3.7s porque NO toca Neon (async via invoke). Verify:
      `--lambda=tracking_pixel` + `lint-deps`.

12. **`refactor(tracking_writer): reconvierte el worker SQS a invoke-target`** (T10)
    - `tracking_worker/` → `tracking_writer/` (manifest direct + handler payload)
      + tests. Verify: `--lambda=tracking_writer` + `lint-deps`.

13. **`perf(cv): @cached DynamoDB + invalidacion en seed`** (T11)
    - `cv/core/services/cv_service.py`, controllers cv.*, `db/seed_service` +
      tests. Body: el warm de cv.get baja de 7.3s a <0.5s (cache hit no toca
      Neon). Verify: `--lambda=cv` (≥80%) + `lint-deps`.

14. **`refactor(auth): invoca send_email async en vez de SQS`** (T12)
    - `auth/{email_dispatch_service,manifest,pyproject}`. Verify: `--lambda=auth`.

15. **`refactor(users): invoca send_email async en vez de SQS`** (T13)
    - `users/{...}`. Verify: `--lambda=users` + lint-deps.

16. **`refactor(serverless): elimina colas SQS, shared.queue y 2 workers`** (T14)
    - Borra `auth_email_worker`, `contact_worker`, `shared/queue/`,
      `resources/sqs/` (NO tracking_worker, ya es tracking_writer); limpia
      pyproject. Verify: `serverless tests --type=unit` + `lint-deps` +
      `rg "shared.queue|ASYNC_MODE"` → 0.

17. **`refactor(backend): elimina el Lambda stream_processor (stage/prod)`** (T15)
    - Código + docs + devtools + destroy AWS. Verify: `rg stream_processor`
      (fuera de `_archive/` + plan) → 0; `list-functions` sin stream-processor.

18. **`docs(rules): promueve uses.invokes/buckets + hallazgos cold a rules`** (T16)
    - `.claude/rules/*` (incl. lambda-config con los hallazgos cold start),
      `CLAUDE.md`. Verify: `claude -p` 5 ángulos.

19. **`test(serverless): verificacion E2E + gate de cold + elimina spec`** (T17)
    - Incluye `git rm -r docs/specs/serverless-sqs-to-async-invoke/`.
    - Verify: batería completa de [13](13-verificacion-e2e.md) + gate de cold
      en verde.

## PR

- Único: `feature/serverless-sqs-to-async-invoke → dev`, merge commit.
- Body: Problema / Solución / Cómo probar (reusa la batería de [13] + el gate de
  cold medido en CloudWatch) / TODO (cleanup versiones SnapStart; keep-alive
  Neon si se decide). Sin atribución de IA.

[← 10 descomposición](10-descomposicion.md) · [siguiente: 12 worktrees →](12-paralelizacion-worktrees.md)
