---
name: ci-cd-pipeline
description: >
  CI/CD pipeline of the portfolio. GitHub Actions workflows for the
  serverless backend (Lambda + DB migrations) and the Astro apps
  (Cloudflare Pages). AWS auth via OIDC, devtools state in S3,
  concurrency queue per env. Use when the user says "ci", "cd",
  "deploy", "github actions", "workflow", "como deployo", "como
  funciona el ci", "redeploy lambda", "trigger deploy", "ci falla",
  "migrate db en ci", "oidc aws", "deploy backend", "deploy apps",
  "pages deploy", "deploy automatico", "concurrency", "queue por env",
  "iam role del ci", or asks about how the deploy pipeline is
  structured.
user-invocable: true
allowed-tools: Read, Glob, Grep
argument-hint: "opcional: tema (oidc, deploy, troubleshoot, state)"
---

# CI/CD pipeline — guia rapida

Workflows GitHub Actions del portfolio. Al mergear a una rama de
entorno (`dev`/`main`), el CI aplica migraciones de DB,
redeploya los lambdas afectados y rebuildea las apps a Cloudflare
Pages.

## Workflows

| Workflow | Trigger | Que hace |
|----------|---------|----------|
| `ci.yml` | PRs + push env branches | Biome check + build (~45s) |
| `deploy-backend.yml` | Push dev/main | migrate-db -> detect-changes -> deploy-lambdas matrix |
| `deploy-apps.yml` | Push dev/main + manual | build-apps -> deploy-pages matrix 6 niches |
| `branch-flow-guard.yml` | PRs main | Enforce `dev -> main` |
| `clean-pr-attribution.yml` | PRs | Limpia atribucion IA |

## Mapeo branch -> env -> recursos

| Branch | Stage | IAM role | Pages projects | URL |
|--------|-------|----------|----------------|-----|
| dev | dev | `portfolio-deploy-dev` | `portfolio-{niche}-dev` | `{niche}.portfolio.dev.the-full-stack.com` |
| main | prod | `portfolio-deploy-prod` | `portfolio-{niche}` | `{niche}.portfolio.the-full-stack.com` (apex para `generic`) |

## AWS auth via OIDC

- Cero secrets de larga vida. 1 OIDC provider + 2 IAM roles, trust
  policy scoped a `repo:bypabloc/cv:ref:refs/heads/<branch>`.
- Setup paso a paso: `.claude/docs/ci-cd-pipeline/aws-oidc-setup.md`.

## State de devtools

- S3 bucket `portfolio-devtools-state` (us-east-1, KMS, versioned).
- Activacion: env vars `DEVTOOLS_STATE_BACKEND=s3` +
  `DEVTOOLS_STATE_BUCKET=portfolio-devtools-state` (declaradas en
  workflows). Default sin env vars: local en `.state/`.
- Layout: `s3://portfolio-devtools-state/state/<scope>-<stage>.json`.

## Detect-changes

`devtools/serverless/change_detector.py`:

- `services/<X>/**` cambia -> redeploy `X` (excluyendo `tests/`,
  `events/`, `build/`, `core/seeds/data/`).
- `shared/<Y>/**` cambia -> redeploy consumers transitivos.
- `db` se excluye del matrix (ya redeployado en `migrate-db`).

CLI: `serverless detect-changes --base=<sha> --head=<sha>`.

## Concurrency

`concurrency.group=deploy-<area>-${branch}` + `cancel-in-progress:
false`. Dos pushes seguidos al mismo env se ENCOLAN, nunca se
cancelan (cancelar mid-deploy deja AWS en estado parcial).

## Que NO corre CI (vs pre-push local)

| Step | Donde corre |
|------|-------------|
| Biome lint + format | ci.yml + pre-push |
| Build apps | ci.yml + pre-push |
| TypeScript check | SOLO pre-push (CI lo evita: redundante con build) |
| `astro check` | SOLO pre-push (CI lo evita: duplica parsing con build) |
| Vitest unit + coverage | SOLO pre-push (no es required check) |
| Playwright E2E | SOLO pre-push (lento; depende de Docker) |

CI es la red de seguridad para pushes que bypassean el hook. Cubre el
subset que detecta deploys rotos.

## Comandos utiles

```bash
# Validar sintaxis de los workflows
python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"

# Smoke del detect-changes
python devtools/run.py serverless detect-changes \
  --base=HEAD~10 --head=HEAD

# Listar runs recientes
gh run list --limit 5

# Watch del run actual
gh run watch

# Disparar deploy-apps manualmente
gh workflow run deploy-apps.yml -f env=dev
```

## Referencia

- Rule autoritativa: `.claude/rules/ci-cd-pipeline.md`.
- Runbook OIDC setup: `.claude/docs/ci-cd-pipeline/aws-oidc-setup.md`.
- Troubleshooting: `.claude/docs/ci-cd-pipeline/troubleshooting.md`
  (si existe).
- Implementacion del state: `devtools/serverless/state.py`.
- Implementacion del detector: `devtools/serverless/change_detector.py`.
