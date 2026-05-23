# Plan e-ci-cd-deploy-pipeline

> CI/CD modular del portfolio: al mergear a dev/stage/main, el workflow
> aplica migraciones de DB, redeploya los Lambdas tocados y rebuildea
> las apps en su entorno Cloudflare Pages. AWS via OIDC (sin secrets
> largos), estado de devtools en S3, concurrency por env.

## Contexto

### Estado actual (mayo 2026)

| Componente | Hoy | Gap |
|------------|-----|-----|
| **CI quality gates** | `.github/workflows/ci.yml` corre conformance + typecheck + astro check + unit + build + upload coverage en cada PR y push. ~1m 20s | El typecheck + unit duplica lo que ya valida el pre-push hook local. astro check duplica trabajo con build (mismo parsing del grafo) |
| **Deploy apps** | `.github/workflows/deploy.yml` dispara solo en push a `main`, despliega via wrangler-action a Cloudflare Pages | dev/stage NO tienen deploy automatizado |
| **Deploy Lambdas** | 100% manual via `python devtools/run.py serverless deploy --lambda=<X> --stage=<env>` | Cero automatizacion. AWS credentials viven en `docker/env/dev-cli/.{env}` del developer local |
| **Migrations DB** | Manual: `serverless run --lambda=db --event=events/migrate.json --stage=<env>` | Sin gate de "no podes deployar el resto si migrations fallan" |
| **Estado devtools** | `serverless/lambda/.state/<scope>-<stage>.json` en disco local del developer, gitignored | No compartido entre el laptop del dev y CI. Si CI deploya, no sabe que hizo antes el dev local |
| **AWS auth** | IAM user `dev` con AdministratorAccess (perfil `tfs-dev`), key vive en `.env` local | No hay auth desde GitHub Actions |
| **Branch flow** | `branch-flow-guard.yml` valida `dev -> stage -> main` (enforce via ruleset) | Funciona, no cambia |

### Objetivo

Al mergear un PR a una rama de entorno (`dev`/`stage`/`main`), el CI debe:

1. **Apply migrations** (Lambda `db` con `migrate.json`). Si falla, abortar.
2. **Detectar lambdas tocados** (path-based + cierre transitivo de shared).
3. **Re-deployar SOLO esos lambdas** en paralelo cuando se puede.
4. **Re-build + deploy de TODAS las apps** al proyecto Cloudflare Pages
   del env (no path-detection en apps — son baratas y consistencia
   importa).
5. **Reportar el resultado** del deploy completo en el commit y/o un
   summary del workflow.

PRs siguen corriendo el `quality-gates` (lint + build) como gate, pero
sin redundar con el pre-push.

## Decisiones (no reabribles)

1. **AWS auth via OIDC** (federacion GitHub → IAM). 3 IAM roles separados:
   `portfolio-deploy-dev`, `portfolio-deploy-stage`,
   `portfolio-deploy-prod`. Trust policy: solo este repo + solo la branch
   correspondiente puede asumir el rol. Cero secrets AWS de larga vida.

2. **Migraciones siempre antes** del resto de los deploys. Sequencial:
   `apply migrations -> deploy lambdas afectados -> deploy apps`. Si
   migrations falla, el workflow se detiene.

3. **Path-based detection para lambdas** (con expansion del cierre
   transitivo de shared):
   - `serverless/lambda/services/cv/**` cambia -> redeploy `cv`.
   - `serverless/lambda/shared/db/**` cambia -> redeploy todos los
     lambdas cuyo cierre transitivo incluye `shared.db` (db, cv,
     stream_processor).
   - `serverless/lambda/services/db/core/seeds/data/**` cambia -> NO
     deploy (los seeds van en el zip pero solo se aplican via
     `serverless run --lambda=db --event=seed.json`, comando manual).

4. **Apps Astro: full rebuild + deploy siempre**. 6 apps × 3 envs = 18
   proyectos Cloudflare Pages. Path-detection NO aplica (las apps son
   ~3s cada una; consistencia > optimizacion).

5. **CI quality-gates simplificado**: quita `typecheck` + `unit tests` +
   `upload coverage`. Deja solo:
   - `biome check` (lint + format)
   - `pnpm run build` de todas las apps (cubre los errores que importan
     para deploy)

   Razon: pre-push hook local SIEMPRE corre la bateria completa (lint +
   typecheck + unit + build + E2E). El CI es la red de seguridad para
   `--no-verify`, asi que solo necesita el subset que detecta deploys
   rotos. Coverage se sigue midiendo en local; si en el futuro alguien
   quiere coverage en PRs, se agrega Codecov (1 step extra).

6. **Concurrency**: `queue` por env (`group=deploy-${env}`,
   `cancel-in-progress=false`). Si 2 merges llegan rapido a `dev`, el
   segundo espera. Evita race conditions con S3 state.

7. **State de devtools en S3**: bucket `portfolio-devtools-state` en
   `us-east-1`. Cada run de deploy hace `aws s3 cp` del JSON al inicio
   y al final. `devtools/serverless/state.py` se extiende con un
   backend opcional S3 (controlado por env var
   `DEVTOOLS_STATE_BACKEND=s3` + `DEVTOOLS_STATE_BUCKET=...`). El
   default sigue siendo local (zero impact para el dev).

8. **Apps en 3 envs Cloudflare Pages**: los 18 proyectos ya existen
   (creados con el setup actual de Cloudflare). El workflow apunta a:
   - dev: `portfolio-{niche}-dev` (URL: `{niche}.portfolio.dev.the-full-stack.com`)
   - stage: `portfolio-{niche}-stage`
   - main: `portfolio-{niche}` (canonical, sin sufijo)

9. **NO se borran los workflows actuales** en este plan. Se rediseñan:
   - `ci.yml` se simplifica (commit dedicado).
   - `deploy.yml` se transforma en `deploy-apps.yml` (multi-env, no
     solo main).
   - Workflow nuevo `deploy-backend.yml` (lambdas + migrations).
   - `branch-flow-guard.yml` y `clean-pr-attribution.yml` quedan
     intactos.

10. **Notificaciones**: el workflow comenta en el commit (no en PR
    porque ya esta mergeado). Si un step falla, falla el workflow
    completo (visible en el badge del commit).

11. **Plan efimero**: `docs/specs/e-ci-cd-deploy-pipeline/` se elimina
    al mergear el plan a `dev`. Los workflows + S3 bucket + IAM roles
    + docs en `.claude/docs/ci-cd-pipeline/` son los artefactos
    permanentes.

## Arquitectura (alto nivel)

```text
                       Merge PR -> dev/stage/main
                                  │
                                  ▼
                  ┌──────────────────────────────┐
                  │  branch-flow-guard.yml       │  (ya existe)
                  │  + clean-pr-attribution.yml  │
                  └──────────────────────────────┘
                                  │
                                  ▼
        ┌─────────────────────────┴─────────────────────────┐
        │                                                   │
        ▼                                                   ▼
 ┌──────────────┐                              ┌──────────────────────┐
 │ ci.yml       │                              │ deploy-backend.yml   │
 │ quality-gates│                              │   migrate-db        │
 │ (PRs solo)   │                              │     │                │
 └──────────────┘                              │     ▼                │
                                               │   detect-changes     │
                                               │     │                │
                                               │     ▼                │
                                               │   deploy-lambdas     │
                                               │   (matrix: solo los  │
                                               │   tocados, paralelo) │
                                               └──────────────────────┘
                                                          │
                                                          ▼
                                              ┌──────────────────────┐
                                              │ deploy-apps.yml      │
                                              │   build-apps         │
                                              │     │                │
                                              │     ▼                │
                                              │   deploy-pages       │
                                              │   (matrix: 6 niches  │
                                              │   en paralelo)       │
                                              └──────────────────────┘
                                                          │
                                                          ▼
                                              ┌──────────────────────┐
                                              │ Commit comment con   │
                                              │ resumen del deploy   │
                                              └──────────────────────┘
```

## Fases del plan

| Fase | Archivo | Que hace | Commits |
|------|---------|----------|---------|
| **A — Infra AWS OIDC + S3 state** | `01-fase-a-aws-oidc-s3-state.md` | Crear OIDC provider en AWS, 3 IAM roles, bucket S3 portfolio-devtools-state. Documentar setup paso a paso (manual, una sola vez) | 0 (setup manual con AWS CLI) + 1 commit del doc operativo |
| **B — devtools state backend S3** | `02-fase-b-devtools-state-s3.md` | Extender `devtools/serverless/state.py` con backend S3 opcional (env vars). Tests del backend con moto. Documentacion | 1 commit |
| **C — devtools detect-changes helper** | `03-fase-c-detect-changes-helper.md` | Crear `devtools/serverless/change_detector.py`: dado un sha base + sha head, devuelve la lista de lambdas afectados (path-based + cierre transitivo de shared) | 1 commit |
| **D — CI simplificado** | `04-fase-d-ci-simplificado.md` | Refactor `ci.yml`: quita typecheck + unit + coverage. Deja conformance + build. Reduce duracion de ~80s a ~45s | 1 commit |
| **E — Workflow deploy-backend** | `05-fase-e-workflow-deploy-backend.md` | Crear `.github/workflows/deploy-backend.yml`: migrate-db -> detect-changes -> deploy-lambdas matrix. Trigger: push a dev/stage/main + workflow_dispatch | 1 commit |
| **F — Workflow deploy-apps** | `06-fase-f-workflow-deploy-apps.md` | Refactor `deploy.yml` -> `deploy-apps.yml`: dispara en los 3 envs, matrix 6 niches en paralelo, mapeo de env -> nombre del proyecto Pages | 1 commit |
| **G — Commit comment summary** | `07-fase-g-commit-comment-summary.md` | Step final que arma un Markdown con que se deployo + URLs + duracion, y lo postea como commit comment con peter-evans/commit-comment | 1 commit |
| **H — Documentacion .claude** | `08-fase-h-docs-claude.md` | Rule `.claude/rules/ci-cd-pipeline.md` + skill `ci-cd-pipeline` + docs `.claude/docs/ci-cd-pipeline/` (3 archivos: setup OIDC, runbook deploy, troubleshooting) | 1 commit |
| **VERIF** | `09-verificacion-e2e.md` | Bateria E2E: PR de prueba al branch dev -> verificar que los 3 workflows corren en orden + comentario en commit. Eliminar `docs/specs/e-ci-cd-deploy-pipeline/` | 1 commit |

Total estimado: **8 commits** en `feature/ci-cd-deploy-pipeline` desde `dev`.

## Reglas criticas

- SIEMPRE migrate-db ANTES de deploy-lambdas (si las migrations
  fallan, los lambdas pueden referenciar columnas que no existen).
- SIEMPRE deploy-lambdas ANTES de deploy-apps (las apps pueden depender
  del API; si el API esta down, el deploy de las apps no sirve).
- SIEMPRE concurrency.group por env: dos merges seguidos a `dev` se
  encolan, NO se ejecutan en paralelo.
- NUNCA usar IAM access keys de larga vida en GitHub Secrets — solo
  OIDC.
- NUNCA atribuir a IA en commits/PRs ni en mensajes del workflow.
- NUNCA mergear a stage/main con tests rojos en el ultimo commit de
  dev/stage.

## Matriz de verificacion

| Comando | Cuando |
|---------|--------|
| `python -m compileall -q devtools/serverless` | Tras editar state.py o change_detector.py |
| `python devtools/run.py test_runner --module=devtools --type=unit -- -k 'state or change_detector'` | Tests de los modulos nuevos |
| `gh workflow list` | Validar que los workflows existen tras commits |
| `gh workflow run deploy-backend.yml --ref dev` | Smoke test del workflow nuevo (Fase verif) |
| `gh run watch <run-id>` | Seguir el progreso del workflow |

## Riesgos y mitigaciones

| Riesgo | Mitigacion |
|--------|------------|
| OIDC mal configurado -> CI no puede autenticarse a AWS | Setup paso a paso en `01-fase-a` con verificacion via `aws sts get-caller-identity` despues de assumir el rol |
| State drift entre laptop local y S3 | El dev local sigue usando state local por default. Solo CI usa S3. Documentar que tras un deploy manual desde laptop el dev DEBE subir el state a S3 antes del proximo CI |
| Migrations downgrade en prod sin rollback | El workflow NO ejecuta downgrade. Solo `migrate` (upgrade head). Si una migration mete bug, se aplica una nueva migration que la revierte (forward fix). Politica de neon-management.md |
| Costos GH Actions Free tier | Cada deploy a env: ~3-5 min (migrate 30s + 5 lambdas paralelo 2m + 6 apps paralelo 2m). 3 envs = max 15 min/dia si se mergea mucho. Free tier: 2000 min/mes. Holgado |
| Cloudflare Pages: rate limit en deploys | Cloudflare permite 100 deploys/dia por proyecto. Holgado |
| Lambda deploy falla a mitad (5 en paralelo) | Cada matrix job es independiente. Si cv falla pero stream_processor pasa, los otros no se revierten. El operador debe inspeccionar y re-deployar el fallido manualmente |

## Navegacion

- [01-fase-a-aws-oidc-s3-state.md](01-fase-a-aws-oidc-s3-state.md)
- [02-fase-b-devtools-state-s3.md](02-fase-b-devtools-state-s3.md)
- [03-fase-c-detect-changes-helper.md](03-fase-c-detect-changes-helper.md)
- [04-fase-d-ci-simplificado.md](04-fase-d-ci-simplificado.md)
- [05-fase-e-workflow-deploy-backend.md](05-fase-e-workflow-deploy-backend.md)
- [06-fase-f-workflow-deploy-apps.md](06-fase-f-workflow-deploy-apps.md)
- [07-fase-g-commit-comment-summary.md](07-fase-g-commit-comment-summary.md)
- [08-fase-h-docs-claude.md](08-fase-h-docs-claude.md)
- [09-verificacion-e2e.md](09-verificacion-e2e.md)
- [10-commits.md](10-commits.md)
- [11-paralelizacion-worktrees.md](11-paralelizacion-worktrees.md)
