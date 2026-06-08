# CI/CD pipeline del portfolio

> Documentacion conceptual + runbooks del pipeline CI/CD. Para la
> rule autoritativa ver `.claude/rules/ci-cd-pipeline.md`; para la
> guia rapida invocable ver la skill `ci-cd-pipeline`.

## Diagrama

```text
                       Merge PR -> dev/main
                                  │
                                  ▼
                  ┌──────────────────────────────┐
                  │  branch-flow-guard.yml       │
                  │  + clean-pr-attribution.yml  │
                  └──────────────────────────────┘
                                  │
                                  ▼
        ┌─────────────────────────┴─────────────────────────┐
        │                                                   │
        ▼                                                   ▼
 ┌──────────────┐                              ┌──────────────────────┐
 │ ci.yml       │                              │ deploy-backend.yml   │
 │ Lint + Build │                              │   resolve-env        │
 │ ~45s         │                              │   migrate-db         │
 │ (PRs + push) │                              │   detect-changes     │
 └──────────────┘                              │   deploy-lambdas     │
                                               │   report             │
                                               └──────────────────────┘
                                                          │
                                                          ▼
                                              ┌──────────────────────┐
                                              │ deploy-apps.yml      │
                                              │   resolve-env        │
                                              │   build-apps         │
                                              │   deploy-pages (x6)  │
                                              │   report             │
                                              └──────────────────────┘
                                                          │
                                                          ▼
                                              ┌──────────────────────┐
                                              │ Commit comment con   │
                                              │ resumen del deploy   │
                                              └──────────────────────┘
```

## Tabla de contenidos

| Documento | Cuando leer |
|-----------|-------------|
| [aws-oidc-setup.md](aws-oidc-setup.md) | Setup inicial AWS (OIDC + 2 IAM roles + S3 bucket). Una sola vez |
| [troubleshooting.md](troubleshooting.md) | Errores comunes y como diagnosticarlos |

## Pre-requisitos para el primer deploy

1. Infra AWS creada (ver `aws-oidc-setup.md`):
   - OIDC provider para `token.actions.githubusercontent.com`.
   - 2 IAM roles `portfolio-deploy-{dev,prod}` con trust policy
     scoped al repo + branch.
   - Bucket S3 `portfolio-devtools-state` (encryption KMS + versioning
     + lifecycle).
2. Secrets de GitHub: `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`
   (ya existian para `deploy.yml`).
3. 12 proyectos Cloudflare Pages creados:
   `portfolio-{niche}{-dev|}` por cada uno de los 6 niches
   (generic, hub, fintech, architect, leader, vibe).
4. Custom domains apuntando a los proyectos correctos (ya configurado
   en el setup actual de Cloudflare DNS).

## Workflows

### ci.yml (PRs + push)

- Biome check (lint + format).
- Build de las 6 apps en paralelo (`--workspace-concurrency=6`).
- Sube `dist-all-apps-<sha>` como artifact (solo en push, no PRs).
- Duracion: ~45s.

### deploy-backend.yml (push env branches)

- `resolve-env`: mapea branch -> stage + IAM role ARN.
- `migrate-db`: re-deploy del Lambda `db` + apply Alembic
  (`events/migrate.json`) + show current (`events/current.json`).
- `detect-changes`: invoca `serverless detect-changes` para listar
  lambdas afectados.
- `deploy-lambdas`: matrix paralelo (fail-fast: false). Cada lambda
  corre `serverless deploy --lambda=X --stage=...`.
- `report`: postea commit comment con resultados.

### deploy-apps.yml (push env branches)

- `resolve-env`: branch -> stage + sufijo del proyecto Pages.
- `build-apps`: descarga el artifact `dist-all-apps-<sha>` si esta;
  sino rebuildea local.
- `deploy-pages`: matrix de 6 niches con `cloudflare/wrangler-action@v3`.
- `report`: commit comment con URLs.

## State de devtools

- Local (default): `serverless/lambda/.state/<scope>-<stage>.json`,
  gitignored.
- S3 (CI): `s3://portfolio-devtools-state/state/<scope>-<stage>.json`,
  encryption KMS, versioning.
- Activacion: env vars `DEVTOOLS_STATE_BACKEND=s3` +
  `DEVTOOLS_STATE_BUCKET=portfolio-devtools-state`.

## Costos

| Recurso | Costo mensual |
|---------|---------------|
| AWS OIDC provider + IAM roles | $0 (free) |
| S3 bucket portfolio-devtools-state | <$0.01 (KB de JSON con versioning) |
| GitHub Actions minutos | $0 (free tier 2000 min/mes; consumo estimado ~150 min/mes) |
| Cloudflare Pages deploys | $0 (free tier 500 deploys/mes; consumo estimado ~60/mes) |

## Reglas criticas

Ver `.claude/rules/ci-cd-pipeline.md` para la lista completa de
SIEMPRE/NUNCA.

## Navegacion

- Volver: `.claude/rules/ci-cd-pipeline.md` (rule autoritativa).
- Setup inicial: [aws-oidc-setup.md](aws-oidc-setup.md).
- Errores comunes: [troubleshooting.md](troubleshooting.md).
