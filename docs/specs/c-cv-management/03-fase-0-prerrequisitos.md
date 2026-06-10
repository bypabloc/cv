# 03 — Fase 0: prerrequisitos de infraestructura

> Bloqueante: nada de escritura desde el admin hasta cerrar esta fase.
> [Volver al README](README.md).

## 0.1 Aislamiento del branch Neon de dev (CRITICO)

Pendiente operativo conocido: `/portfolio/dev/neon-url` se creo copiando
el valor del parametro legacy, que apunta al branch `production` de Neon.
Si sigue asi, escribir desde el admin de dev MUTARIA datos de prod.

Pasos:

1. Verificar a que branch apunta cada parametro (comparar el host/branch
   del connection string SIN imprimir el valor — usar
   `serverless secrets-status --stage=dev` + la consola/CLI de Neon).
2. Si dev no esta aislado: crear branch `dev` en Neon desde `main`
   (`neon branches create --name dev --parent main`) y actualizar
   `/portfolio/dev/neon-url` via
   `sync_secrets --env=dev --category=server` (valor primero en
   `docker/env/server/.dev`).
3. Verificar: `serverless run --stage=dev --lambda=db
   --event=events/tables.json` muestra tablas pobladas en el branch dev.

- Verificar: una escritura de prueba en dev NO aparece en prod (AC-12).

## 0.2 Secret nuevo: `github-deploy-token` (PAT fine-grained)

Para que `cv_admin` dispare `workflow_dispatch`:

1. Crear PAT fine-grained scoped al repo `bypabloc/cv`, permiso
   `Actions: read and write` (nada mas). Expiracion 1 año, rotacion
   documentada.
2. Declararlo en el catalogo: `serverless/lambda/resources/secrets/
   github-deploy-token.yaml` (SecureString + KMS, paths
   `/portfolio/{dev,prod}/github-deploy-token`).
3. Valor en `docker/env/server/.{dev,prod}` → publicar con
   `sync_secrets --env=<X> --category=server --aws-profile=tfs-dev`.

- Verificar: `serverless secrets-status --stage=dev` lista el secret.

## 0.3 Bucket S3 de backups

1. Declarar `serverless/lambda/resources/s3/db-backups.yaml`:
   `portfolio-db-backups` (us-east-1), versioning ON, lifecycle: expirar
   noncurrent y objetos fechados > 12 semanas (los `latest/` no expiran),
   bloqueo de acceso publico.
2. Provisionar: `serverless provision-infra --stage=<X>
   --aws-profile=tfs-dev` (publica name/arn a SSM
   `/portfolio/{stage}/s3/db-backups/*` como el bucket de templates).

- Verificar: `aws s3api get-bucket-versioning --bucket portfolio-db-backups`
  → `Enabled`.

## 0.4 Rol IAM OIDC para el cron de backup

Los roles existentes (`portfolio-deploy-{dev,prod}`) estan scoped por
branch y el cron corre sobre la default branch (`dev`) — no puede asumir
el rol prod. Crear rol dedicado `portfolio-db-backup`:

- Trust: OIDC GitHub, `sub = repo:bypabloc/cv:ref:refs/heads/dev`.
- Permisos minimos: `ssm:GetParameter` sobre
  `/portfolio/{dev,prod}/neon-url` + `kms:Decrypt` de
  `alias/portfolio-lambdas` + `s3:PutObject` sobre
  `arn:aws:s3:::portfolio-db-backups/*`.
- Documentar en `.claude/docs/ci-cd-pipeline/aws-oidc-setup.md`.

- Verificar: dry-run del workflow (dispatch manual) asume el rol y lista
  el bucket.

## Archivos afectados (Fase 0)

### Crear

- `serverless/lambda/resources/secrets/github-deploy-token.yaml` — secret
  declarativo
  - Verificar: `python devtools/run.py serverless validate-catalog`
- `serverless/lambda/resources/s3/db-backups.yaml` — bucket backups
  - Verificar: `serverless provision-infra --stage=dev` idempotente (re-run
    → noop)

### Modificar

- `.claude/rules/serverless-secrets.md` — inventario: agregar
  `github-deploy-token` + bucket `db-backups` + rol `portfolio-db-backup`
  - Verificar: lectura cruzada con `secrets-status`
- `docker/env/server/.example` — placeholder `GITHUB_DEPLOY_TOKEN`
  - Verificar: archivo `.example` versionado sin valor real
