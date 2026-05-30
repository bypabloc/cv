# 07 — Limpieza `stream_processor` + promover convenciones a rules

[← 06 migrar callers](06-migrate-callers-remove-sqs.md) · [siguiente: 08 descomposición →](08-descomposicion.md)

> Fase 6. Borra TODA referencia a `stream_processor` (nunca existió como
> Lambda) y promueve a `.claude/rules/` las convenciones nuevas antes de que
> la carpeta del plan se elimine.

## 7.1 Referencias a `stream_processor` a eliminar/corregir

Detectadas con `rg -l stream_processor` (verificar la lista al ejecutar):

| Archivo | Acción |
|---------|--------|
| `CLAUDE.md` | Quitar `stream_processor` de la lista de Lambdas, del árbol de conocimiento y de las descripciones de skills backend. Actualizar a los Lambdas reales (auth, contact_form, cv, db, send_email, tracking_pixel, users). |
| `devtools/serverless/lambda_controller.py` | Quitar refs en comentarios/listas. |
| `devtools/serverless/provisioner.py` | Quitar mención en comentario (`on-table-changes se elimino…`). |
| `devtools/serverless/change_detector.py` | Quitar de listas/comentarios. |
| `devtools/tests/unit/src/serverless/{infra_provision,provisioner,change_detector}.py` | Actualizar/eliminar casos. |
| `serverless/lambda/shared/aws/dynamodb_types.py` | Quitar comentario especulativo. |
| `serverless/lambda/shared/dynamodb/README.md` | Quitar mención. |
| `serverless/lambda/shared/db/cv_repository.py` | Quitar comentario especulativo sobre stream_processor. |
| `serverless/scripts/seed_test_contact.py` | Revisar y limpiar. |
| `serverless/lambda/services/tracking_pixel/core/services/tracking_service.py` | Ya se reescribe en fase 5; confirmar sin refs. |
| `docs/specs/analytics-dashboard-api/*`, `docs/specs/dashboard/*` | Specs de otros planes: corregir la mención (o nota de que el stream_processor nunca existió). NO borrar esas specs. |
| `serverless/migrations/_archive/*.sql` | Archivo histórico: dejar (es `_archive`), o agregar nota. |

> Regla: tras esta fase, `rg "stream_processor|stream-processor"` en código
> activo (fuera de `_archive/`) debe dar **0 resultados** (AC-10).

## 7.2 Promover convenciones a rules (antes de borrar la carpeta del plan)

La carpeta `docs/specs/serverless-sqs-to-async-invoke/` es efímera. Lo que
debe sobrevivir se promueve a `.claude/rules/`:

1. **`.claude/rules/lambda-shared-imports.md`** — agregar al catálogo de
   portadores: `shared.aws.lambda_invoke` (invoke async) y
   `shared.templating.jinja` (Jinja2). Agregar `import jinja2` / `import
   boto3` lambda a la lista de imports prohibidos en `core/`.
2. **`.claude/rules/lambda-controller.md`** o una rule nueva
   **`.claude/rules/async-lambda-invoke.md`** — documentar el patrón
   `uses.invokes` (IAM `lambda:InvokeFunction` + env var
   `LAMBDA_<X>_FUNCTION_NAME`) y `uses.buckets` (`s3:GetObject` + env var
   `S3_<X>_BUCKET`), y la decisión "async = InvocationType=Event,
   best-effort, sin SQS".
3. **`.claude/rules/devtools.md`** — actualizar: trigger válidos
   `direct`/`http` (sin `sqs`); recursos válidos dynamodb/api_gateway/
   cloudwatch_alarms/**s3** (sin sqs); comando `serverless seed-email-config`.
4. **`.claude/rules/serverless-secrets.md`** — actualizar la matriz de IAM
   por Lambda: quitar las colas SQS, agregar `email-config` (DynamoDB) +
   bucket S3 + los `uses.invokes`. Quitar `ses-from-address` de
   `contact_form` (lo usa `send_email`); `contact_form`/`tracking_pixel`
   conservan `neon-url` (escriben inline).
5. **`.claude/rules/auth-system.md`** — actualizar: `auth_email_worker`
   eliminado; auth/users invocan `send_email` async. Quitar refs a la cola
   SQS auth-email y al worker.
6. **CLAUDE.md** — actualizar el árbol de la estructura del repo
   (`serverless/lambda/services/`), la tabla de Lambdas y las descripciones
   de skills backend (quitar workers + stream_processor + SQS;
   agregar send_email + invoke async + escritura inline en los encoders).
7. **Skills afectadas** (`.claude/skills/auth-system/`,
   `serverless-rate-limit`, `aws-*`): revisar menciones a SQS/workers; el
   detalle de validación con `claude -p` lo cubre la regla
   `.claude/rules/claude-config-testing.md` (validar las skills/rules
   tocadas en 5 ángulos).

## 7.3 Eliminar la carpeta del plan

En el último commit (fase 7, archivo 11) — tras la batería E2E verde:
`git rm -r docs/specs/serverless-sqs-to-async-invoke/`.

## Archivos afectados (fase 6)

### Modificar
- `CLAUDE.md`, `.claude/rules/{lambda-shared-imports,devtools,serverless-secrets,auth-system}.md`,
  `.claude/rules/async-lambda-invoke.md` (nueva o dentro de lambda-controller),
  `devtools/serverless/{lambda_controller,provisioner,change_detector}.py`,
  `serverless/lambda/shared/aws/dynamodb_types.py`,
  `serverless/lambda/shared/dynamodb/README.md`,
  `serverless/lambda/shared/db/cv_repository.py`,
  `serverless/scripts/seed_test_contact.py`,
  `docs/specs/{analytics-dashboard-api,dashboard}/*` (corrección de mención).
  - Verificar: `rg "stream_processor" --glob '!**/_archive/**' --glob '!docs/specs/serverless-sqs-to-async-invoke/**'` → 0 resultados.
  - Verificar: validar las rules/skills tocadas con `claude -p`
    (`.claude/rules/claude-config-testing.md`).

[← 06 migrar callers](06-migrate-callers-remove-sqs.md) · [siguiente: 08 descomposición →](08-descomposicion.md)
