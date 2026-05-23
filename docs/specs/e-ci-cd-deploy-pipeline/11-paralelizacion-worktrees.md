# Seccion 11 — Paralelizacion con git worktrees

> Que se puede paralelizar y desde que commit. La base secuencial son
> los commits 1-2 (plan + AWS infra). Los commits 3-8 son worktree-safe
> (archivos disjuntos). El 9 (docs claude) y 10 (verif E2E) son
> secuenciales al final.

## Base secuencial (NO se paraleliza)

| Commit | Por que es base |
|--------|-----------------|
| 1 (plan) | Crea la carpeta del plan; todos los worktrees la consultan |
| 2 (AWS infra) | Setup AWS manual con AWS CLI (provider + 3 roles + S3 bucket). NO toca codigo del repo (solo crea `.claude/docs/ci-cd-pipeline/aws-oidc-setup.md`). Los workflows de fases E/F dependen del role-arn |

Despues del commit 2, se puede ramificar.

## Bloque worktree-safe (paralelo)

Cada worktree toca archivos exclusivos:

| Worktree | Fase | Archivos exclusivos |
|----------|------|---------------------|
| `worktree-state` | B | `devtools/serverless/state.py` + `devtools/tests/unit/src/serverless/state.py` |
| `worktree-detect` | C | `devtools/serverless/change_detector.py` + `devtools/serverless/main.py` (cmd nuevo) + `devtools/serverless/flags.py` + `devtools/tests/unit/src/serverless/change_detector.py` |
| `worktree-ci` | D | `.github/workflows/ci.yml` solamente |
| `worktree-backend` | E | `.github/workflows/deploy-backend.yml` (nuevo) |
| `worktree-apps` | F | `.github/workflows/deploy.yml` -> `deploy-apps.yml` (rename + reescritura) |

Cero solapamiento de archivos. Cada worktree termina con un commit
atomico que se mergea de vuelta a `feature/ci-cd-deploy-pipeline`.

Comandos:

```bash
# Crear los 5 worktrees desde la base
for name in state detect ci backend apps; do
  git worktree add ../portfolio-ci-$name feature/ci-cd-deploy-pipeline
done
```

## Lo que NO se paraleliza

| Commit | Razon |
|--------|-------|
| 8 (commit comment summary) | Edita los 2 workflows (E y F). Mejor secuencial DESPUES de ambos. Sino genera conflicts |
| 9 (docs claude) | Edita CLAUDE.md (compartido). Va al final, cuando el contrato esta estabilizado |
| 10 (verif E2E) | Fase de cierre: smoke test E2E completo, eliminacion del plan. NO se paraleliza |

## Orden recomendado de lanzamiento

```text
T0: commit 1 (plan) -> push
T1: commit 2 (AWS infra manual + runbook) -> push
T2: 5 worktrees en paralelo:
    - worktree-state (Fase B)
    - worktree-detect (Fase C)
    - worktree-ci (Fase D)
    - worktree-backend (Fase E)
    - worktree-apps (Fase F)
T3: merge de los 5 worktrees a feature/ci-cd-deploy-pipeline
    -> commits 3-7 en orden cualquiera
T4: commit 8 (commit comment summary)
T5: commit 9 (docs claude)
T6: commit 10 (verif E2E + git rm del plan)
T7: git push + crear PR (gate de cierre)
```

Limite: maximo 5 agentes concurrentes (cumple el limite del
plan-format).

## Anti-patrones

- Lanzar Fase E o F antes de Fase B y C: los workflows usan
  `serverless detect-changes` (Fase C) y `DEVTOOLS_STATE_BACKEND=s3`
  (Fase B). El commit puede crearse en paralelo, pero el smoke test
  E2E final requiere los 3 commits en HEAD.
- Lanzar Fase 8 en paralelo con E o F: edita los workflows de ambos.
  Conflicto seguro.
- Mergear el plan a `dev` sin pasar el smoke test E2E (Fase 10).

## Limpieza

```bash
for name in state detect ci backend apps; do
  git worktree remove ../portfolio-ci-$name
done
git worktree prune
```
