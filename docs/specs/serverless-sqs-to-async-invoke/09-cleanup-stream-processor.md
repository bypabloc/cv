# 09 — Eliminar el Lambda `stream_processor` + promover convenciones a rules

[← 08 migrar callers](08-migrate-callers-remove-sqs.md) · [siguiente: 10 descomposición →](10-descomposicion.md)

> Fase 7. **CORRECCIÓN al plan v1**: `stream_processor` SÍ existe como Lambda
> (verificado en vivo). Hay que **destruirlo de verdad** (AWS) + borrar sus
> refs de código, y promover a `.claude/rules/` las convenciones nuevas antes
> de eliminar la carpeta del plan.

## 9.1 `stream_processor` es un Lambda real (HECHO verificado)

`aws lambda list-functions` (2026-05-30, perfil tfs-dev):

```
portfolio-stream-processor-stage   EXISTE  (Event Source Mappings:
portfolio-stream-processor-prod    EXISTE   DDB Streams de contacts + tracking)
(no existe en dev)
```

Consume los DynamoDB Streams de `portfolio-contacts-*` y `portfolio-tracking-*`
(réplica analítica a Neon). El plan v1 afirmaba "nunca existió" — **FALSO**.

> Decisión de scope: el plan elimina `stream_processor`. La réplica analítica a
> Neon que hacía queda cubierta por la **escritura inline** (contact_form) y el
> **tracking_writer** (tracking). Si alguna analítica dependía del stream y NO
> está cubierta por esos dos paths, **detenerse y reconsiderar** antes de
> destruir (verificar en fase 0 / al ejecutar esta fase qué escribía exactamente
> a Neon que no escriban ya los nuevos paths).

### Destrucción (AWS, real)
- Borrar los Event Source Mappings (DDB Streams → stream_processor) en stage y
  prod.
- `serverless destroy --lambda=stream_processor --stage=stage` y `--stage=prod`.
- Si el DynamoDB Stream de las tablas queda sin consumidor y no se usa para
  nada más, deshabilitarlo (`StreamSpecification`) en el manifest de las tablas
  (opcional, evita costo de stream sin lector).
- Verificar: `aws lambda list-functions` no lista `portfolio-stream-processor-*`.

## 9.2 Referencias a `stream_processor` a eliminar (código + docs)

`rg -l stream_processor` (verificar la lista al ejecutar):

| Archivo | Acción |
|---------|--------|
| `CLAUDE.md` | Quitar de la lista de Lambdas, árbol de conocimiento y skills backend. Lambdas reales tras el plan: auth, contact_form, cv, db, send_email, tracking_pixel, tracking_writer, users. |
| `devtools/serverless/{lambda_controller,provisioner,change_detector}.py` | Quitar refs en comentarios/listas. |
| `devtools/tests/unit/src/serverless/*` | Actualizar/eliminar casos. |
| `serverless/lambda/shared/aws/dynamodb_types.py`, `shared/dynamodb/README.md`, `shared/db/cv_repository.py` | Quitar comentarios especulativos. |
| `serverless/scripts/seed_test_contact.py` | Revisar y limpiar. |
| `docs/specs/{analytics-dashboard-api,dashboard}/*` | Specs de otros planes: corregir la mención (el stream_processor se eliminó; la analítica viene de inline + tracking_writer). NO borrar esas specs. |
| `serverless/migrations/_archive/*.sql` | Histórico (`_archive`): dejar. |

> Regla: tras esta fase, `rg "stream_processor|stream-processor"` en código
> activo (fuera de `_archive/`) → **0 resultados** Y el Lambda destruido en AWS
> (AC-14).

## 9.3 Promover convenciones a rules (antes de borrar la carpeta del plan)

1. **`.claude/rules/lambda-shared-imports.md`** — catálogo: `shared.aws.lambda_invoke`
   (invoke async) + `shared.templating.jinja` (Jinja2). Agregar `import jinja2`
   / `import boto3` lambda a los imports prohibidos en `core/`.
2. **`.claude/rules/lambda-controller.md`** o nueva **`async-lambda-invoke.md`** —
   patrón `uses.invokes` (IAM `lambda:InvokeFunction` + env var
   `LAMBDA_<X>_FUNCTION_NAME`) + `uses.buckets` (`s3:GetObject` + env var
   `S3_<X>_BUCKET`) + "async = InvocationType=Event, best-effort, sin SQS".
3. **`.claude/rules/lambda-config.md`** — **(NUEVO, foco del plan)** agregar:
   medir el cold con `Restore Duration`/`Duration` de CloudWatch (no el
   roundtrip del harness); verificar SnapStart con `--qualifier live`; lazy
   imports NO ayudan con SnapStart activo (pueden empeorar); el cuello típico es
   Neon wake + query, no imports; `@cached` DynamoDB para reads que no necesitan
   frescura. Promover los hallazgos de `tmp/cold-start-analysis/08-*.md`.
4. **`.claude/rules/devtools.md`** — trigger válidos `direct`/`http` (sin `sqs`);
   recursos válidos dynamodb/api_gateway/cloudwatch_alarms/**s3** (sin sqs);
   comando `serverless seed-email-config`.
5. **`.claude/rules/serverless-secrets.md`** — matriz IAM: quitar colas SQS,
   agregar `email-config` (DynamoDB) + bucket S3 + `uses.invokes`. Quitar
   `ses-from-address` de contact_form (lo usa send_email). contact_form +
   tracking_writer conservan `neon-url`.
6. **`.claude/rules/auth-system.md`** — `auth_email_worker` eliminado; auth/users
   invocan send_email async. Quitar refs a la cola auth-email + worker.
7. **CLAUDE.md** — árbol del repo, tabla de Lambdas (8 reales) y skills backend:
   quitar workers SQS + stream_processor + SQS; agregar send_email +
   tracking_writer + invoke async + cv @cached.
8. **Skills** (`auth-system`, `serverless-rate-limit`, `aws-*`): revisar
   menciones a SQS/workers/stream_processor; validar las tocadas con `claude -p`
   (`.claude/rules/claude-config-testing.md`, 5 ángulos).

## 9.4 Eliminar la carpeta del plan

En el último commit (fase 8, archivo 13), tras la batería verde:
`git rm -r docs/specs/serverless-sqs-to-async-invoke/`.

## Archivos afectados (fase 7)

### Destruir (AWS)
- `portfolio-stream-processor-{stage,prod}` + sus Event Source Mappings.
  - Verificar: `aws lambda list-functions | rg stream-processor` → vacío.

### Modificar
- `CLAUDE.md`, `.claude/rules/{lambda-shared-imports,lambda-controller,lambda-config,devtools,serverless-secrets,auth-system}.md`,
  `.claude/rules/async-lambda-invoke.md` (nueva o dentro de lambda-controller),
  `devtools/serverless/{lambda_controller,provisioner,change_detector}.py`,
  `serverless/lambda/shared/aws/dynamodb_types.py`,
  `serverless/lambda/shared/dynamodb/README.md`,
  `serverless/lambda/shared/db/cv_repository.py`,
  `serverless/scripts/seed_test_contact.py`,
  `docs/specs/{analytics-dashboard-api,dashboard}/*`.
  - Verificar: `rg "stream_processor" --glob '!**/_archive/**' --glob '!docs/specs/serverless-sqs-to-async-invoke/**'` → 0.
  - Verificar: rules/skills tocadas con `claude -p`.

[← 08 migrar callers](08-migrate-callers-remove-sqs.md) · [siguiente: 10 descomposición →](10-descomposicion.md)
