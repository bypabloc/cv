# Fase H — Documentacion permanente en .claude/

> Rule autoritativa `.claude/rules/ci-cd-pipeline.md` + skill
> `ci-cd-pipeline` + docs `.claude/docs/ci-cd-pipeline/` (3 archivos:
> setup OIDC, runbook deploy, troubleshooting). Artefactos PERMANENTES
> que sobreviven a la eliminacion del plan.

## Contexto / Problema

El plan se elimina al mergear. Si no extraemos las decisiones y
procedimientos a artefactos permanentes:

1. Si la infra AWS se pierde (KMS rotation accidental, region change),
   nadie sabe como recrearla.
2. Si el CI falla en mid-deploy, no hay troubleshooting.
3. Si un dev nuevo necesita entender como funciona el deploy, debe
   leer 3 workflows YAML largos.

Tres artefactos en un solo commit.

## Solucion

### H.1 — Rule `.claude/rules/ci-cd-pipeline.md`

Rule de proyecto, ~250 lineas. Estructura:

```markdown
# CI/CD pipeline del portfolio

> Workflows GitHub Actions del backend serverless y las apps Astro.
> Auth via AWS OIDC, deploy automatizado en merge a dev/stage/main,
> migraciones de DB previas a redeploy de Lambdas.

## Activacion

Aplica al editar:
- `.github/workflows/*.yml`
- `devtools/serverless/state.py`, `change_detector.py`
- Cualquier IAM role / S3 bucket que use el deploy

## Reglas duras (SIEMPRE / NUNCA)

- SIEMPRE migrate-db ANTES de deploy-lambdas. Si falla migrate, abortar.
- SIEMPRE deploy-lambdas ANTES de deploy-apps (las apps consumen el API).
- SIEMPRE concurrency.group=deploy-<area>-${branch} + cancel-in-progress=false.
- SIEMPRE AWS auth via OIDC, NUNCA IAM access keys en GitHub Secrets.
- NUNCA editar manualmente el JSON de state en S3 (rompe la idempotencia
  del provisioner).
- NUNCA correr `serverless downgrade` desde el workflow CI.
- NUNCA usar `cancel-in-progress: true` en deploys que tocan AWS.

## Workflows

| Workflow | Trigger | Que hace | Duracion |
|----------|---------|----------|----------|
| `ci.yml` | PRs + push dev/stage/main | Biome check + build apps (artifact dist-all-apps-<sha>) | ~45s |
| `branch-flow-guard.yml` | PRs a main/stage | Valida dev->stage->main | <10s |
| `clean-pr-attribution.yml` | PRs | Limpia atribuciones IA | <10s |
| `deploy-backend.yml` | Push dev/stage/main | migrate-db -> detect-changes -> deploy-lambdas | 2-5 min |
| `deploy-apps.yml` | Push dev/stage/main + manual | build-apps (reuso CI artifact) -> deploy-pages matrix 6 | 1-3 min |

## Mapeo branch -> env -> recursos

| Branch | Stage | IAM role | Pages projects | URL pattern |
|--------|-------|----------|----------------|-------------|
| dev | dev | portfolio-deploy-dev | portfolio-{niche}-dev | {niche}.portfolio.dev.the-full-stack.com |
| stage | stage | portfolio-deploy-stage | portfolio-{niche}-stage | {niche}.portfolio.stage.the-full-stack.com |
| main | prod | portfolio-deploy-prod | portfolio-{niche} | {niche}.portfolio.the-full-stack.com (apex para generic) |

## Estado de devtools en S3

- Bucket: `portfolio-devtools-state` (us-east-1, KMS encrypted, versioned).
- Activacion: env vars `DEVTOOLS_STATE_BACKEND=s3` +
  `DEVTOOLS_STATE_BUCKET=portfolio-devtools-state`.
- Layout: `s3://portfolio-devtools-state/state/<scope>-<stage>.json`.
- Default (sin env vars): backend local en `serverless/lambda/.state/`.
- Lifecycle: versions viejas (>30 dias) se borran automaticamente.

## Anti-patrones

| Anti-patron | Por que | Correccion |
|-------------|---------|------------|
| IAM access keys en GitHub Secrets | Larga vida, no rotables, leak risk | OIDC con roles federados |
| cancel-in-progress: true en deploy | Cancela mid-deploy, AWS queda parcial | cancel-in-progress: false |
| Editar el state JSON a mano | Rompe idempotencia del provisioner | Recrear el recurso (provisioner detecta drift) |
| Migrate-db en paralelo con deploy-lambdas | Lambdas pueden referenciar columnas inexistentes | Sequencial obligatorio |
| Apps deploy SIN backend deploy | Frontend roto si el API cambio shape | El workflow ya enforza orden |

## Referencias cruzadas

- `.claude/docs/ci-cd-pipeline/` — runbook AWS OIDC + troubleshooting
- Skill `ci-cd-pipeline` — guia rapida invocable
- `devtools/serverless/state.py` — backend de estado
- `devtools/serverless/change_detector.py` — detect-changes
```

### H.2 — Skill `.claude/skills/ci-cd-pipeline/SKILL.md`

```yaml
---
name: ci-cd-pipeline
description: >
  CI/CD pipeline of the portfolio: GitHub Actions workflows for the
  serverless backend (Lambda + DB migrations) and the Astro apps
  (Cloudflare Pages). Use when the user says "ci", "cd", "deploy",
  "github actions", "workflow", "como deployo", "como funciona el
  ci", "redeploy lambda", "trigger deploy", "ci falla", "migrate db
  en ci", "oidc aws", "deploy backend", "deploy apps", "pages
  deploy", "deploy automatico", or asks about how the deploy pipeline
  is structured for this project.
user-invocable: true
allowed-tools: Read, Glob, Grep
argument-hint: "opcional: tema (oidc, deploy, troubleshoot)"
---
```

Cuerpo: cheatsheet de workflows + secuencia de deploy + troubleshooting
comun. Replica el contenido nuclear de la rule en formato "guia rapida".

### H.3 — Docs `.claude/docs/ci-cd-pipeline/`

3 archivos navegables:

- **`README.md`** — Indice + diagrama ASCII del flujo + tabla resumen
  de workflows.
- **`aws-oidc-setup.md`** — Runbook completo de la Fase A (JSONs
  trust + policy + comandos + verificacion). Ya escrito en Fase A,
  vive aqui.
- **`deploy-runbook.md`** — "Como deployar manualmente con devtools
  si CI esta caido", "como verificar el estado post-deploy", "como
  rollback".
- **`troubleshooting.md`** — Errores comunes:
  - "OIDC: Could not assume role" -> verificar trust policy sub.
  - "S3 state: NoSuchKey en primer deploy" -> esperado, returna {}.
  - "Migrate falla: relation does not exist" -> revisar Alembic
    revision actual via `events/current.json`.
  - "Deploy Lambda: ValidationException CodeStorageExceededException"
    -> el zip excede 50MB unzipped o 250MB layers; revisar tamano de
    deps.
  - "Cloudflare Pages: project not found" -> verificar nombre del
    proyecto con sufijo.

### H.4 — Actualizar `CLAUDE.md`

Agregar fila a "Arbol de conocimiento":

```diff
+ | CI/CD pipeline | [.claude/rules/ci-cd-pipeline.md](.claude/rules/ci-cd-pipeline.md) + [.claude/docs/ci-cd-pipeline/](.claude/docs/ci-cd-pipeline/) o skill `ci-cd-pipeline` | Workflows GitHub Actions: ci.yml (lint+build), deploy-backend.yml (migrations + lambdas), deploy-apps.yml (Cloudflare Pages multi-env). AWS auth via OIDC, state en S3, concurrency queue por env. Mapeo dev/stage/main -> recursos |
```

Agregar fila a "Skills disponibles":

```diff
+ | `ci-cd-pipeline` | Pipeline CI/CD: workflows de deploy del backend serverless y las apps Astro. AWS OIDC, S3 state, concurrency. Troubleshooting comun |
```

### H.5 — Validacion claude -p

5 prompts en espanol:

1. "como se deploya el backend al mergear a dev"
2. "que pasa si la migracion de DB falla en CI"
3. "donde vive el state de devtools cuando corre desde GitHub Actions"
4. "como configurar tailwind" (negativo, NO debe disparar)
5. "como rotar el role IAM del CI" (cubre el runbook)

Esperado: 4 positivos con `num_turns > 1` citando la rule; el
negativo no.

## Archivos afectados

### Crear

- `.claude/rules/ci-cd-pipeline.md` (~250 lineas).
- `.claude/skills/ci-cd-pipeline/SKILL.md`.
- `.claude/docs/ci-cd-pipeline/README.md`.
- `.claude/docs/ci-cd-pipeline/aws-oidc-setup.md` (movido desde Fase A).
- `.claude/docs/ci-cd-pipeline/deploy-runbook.md`.
- `.claude/docs/ci-cd-pipeline/troubleshooting.md`.

### Modificar

- `CLAUDE.md` — agrega 2 filas (arbol + skills).

## Criterios de aceptacion

- **AC-H1**: Given los 5 archivos creados, When `ls .claude/...`,
  Then existen.
- **AC-H2**: Given los 5 prompts de validacion, When ejecuto con
  `claude -p`, Then 4 positivos invocan la skill (`num_turns > 1`)
  y el negativo no la dispara.
- **AC-H3**: Given `CLAUDE.md`, When inspecciono "Arbol de
  conocimiento", Then existe la fila "CI/CD pipeline".

## Verificacion

```bash
ls .claude/rules/ci-cd-pipeline.md
ls .claude/skills/ci-cd-pipeline/SKILL.md
ls .claude/docs/ci-cd-pipeline/

claude --permission-mode bypassPermissions \
  --disallowedTools "WebSearch" "WebFetch" \
  --strict-mcp-config --mcp-config '{"mcpServers":{}}' \
  --output-format json \
  -p "como se deploya el backend al mergear a dev" \
  2>&1 | tail -40
```

## Commit

```text
docs(claude): rule + skill + docs para CI/CD pipeline

- .claude/rules/ci-cd-pipeline.md (rule autoritativa): workflows,
  mapeo branch -> env, reglas duras (migrate antes que deploy,
  concurrency queue, OIDC only)
- .claude/skills/ci-cd-pipeline/SKILL.md: skill invocable con
  /ci-cd-pipeline; description en ingles + keywords es/en
- .claude/docs/ci-cd-pipeline/: README + aws-oidc-setup (movido desde
  spec Fase A) + deploy-runbook + troubleshooting
- CLAUDE.md: agrega 2 filas (arbol de conocimiento + skills)
- Validado con claude -p: 5 prompts (4 positivos invocan skill, 1
  negativo no dispara)
- Artefactos permanentes que sobreviven a la eliminacion del plan
  e-ci-cd-deploy-pipeline"
```
