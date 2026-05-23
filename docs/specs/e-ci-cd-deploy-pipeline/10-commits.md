# Seccion 10 — Commits

> Lista de commits del plan en orden, con verificacion incremental.
> Conventional Commits en espanol. Rama: `feature/ci-cd-deploy-pipeline`
> desde `dev`. UN solo PR final a `dev`.

## Rama de trabajo

Pre-condicion (segun `.claude/rules/plan-format.md`):

```bash
branch=$(git branch --show-current)
case "$branch" in
  dev|stage|main|master)
    git checkout dev && git pull --rebase origin dev
    git checkout -b feature/ci-cd-deploy-pipeline
    ;;
  feature/ci-cd-deploy-pipeline) ;;  # continuar
  *) echo "rama inesperada: $branch"; exit 1 ;;
esac
```

## Secuencia de commits

| # | Commit (subject) | Fase | Verificacion incremental |
|---|-------------------|------|--------------------------|
| 1 | `docs(specs): plan e-ci-cd-deploy-pipeline` | Plan | sintaxis MD ok |
| 2 | `docs(ci-cd): runbook AWS OIDC + S3 state bucket setup` | A | provider + roles + bucket creados via AWS CLI (manual) |
| 3 | `feat(devtools/serverless): state.py backend S3 opcional` | B | `compileall`, `test_runner -- -k state` (9 tests) |
| 4 | `feat(devtools/serverless): change_detector helper detecta lambdas afectados` | C | `test_runner -- -k change_detector` (12 tests) |
| 5 | `ci: simplifica ci.yml — solo lint + build, quita typecheck y unit` | D | actionlint, PR de prueba `<60s` |
| 6 | `feat(ci): workflow deploy-backend.yml (lambdas + migrations)` | E | actionlint |
| 7 | `feat(ci): workflow deploy-apps.yml multi-env (dev/stage/main)` | F | actionlint |
| 8 | `feat(ci): commit comment con resumen de cada deploy` | G | actionlint (modificaciones a los 2 workflows previos) |
| 9 | `docs(claude): rule + skill + docs para CI/CD pipeline` | H | claude -p (5 prompts) |
| 10 | `test(ci-cd): verificacion E2E del pipeline + elimina plan` | Verif | smoke test E2E + bateria completa |

Total: **10 commits**.

## Regla por commit

- Cada commit corresponde a una fase del plan.
- Cada commit deja:
  - `actionlint` verde para los workflows tocados.
  - `compileall` verde para el codigo Python tocado.
  - Los tests del scope tocado verdes.
- Conventional Commits en espanol, sin atribucion de IA.
- Subject <= 70 caracteres.

## Pull Request

UN solo PR `feature/ci-cd-deploy-pipeline -> dev`. Title:

```text
feat(ci-cd): pipeline modular dev/stage/main con OIDC + S3 state
```

Body:

```markdown
## Problema

El deploy del backend serverless era 100% manual (`python devtools/run.py
serverless deploy --lambda=X --stage=Y` desde laptop). Solo `main`
tenia deploy automatico de las apps Astro. No habia coordinacion entre
migraciones de DB y redeploy de Lambdas: si una migration metia
breaking change, los Lambdas viejos crasheaban en runtime.

## Solucion

Pipeline CI/CD modular en 10 commits:

- AWS auth via OIDC (cero secrets de larga vida): 3 IAM roles
  (portfolio-deploy-{dev,stage,prod}) scoped al repo + branch.
- S3 bucket portfolio-devtools-state: estado de devtools compartido
  entre CI y laptop, encryption KMS + versioning + lifecycle.
- ci.yml simplificado: solo lint + build (pre-push local ya cubre
  typecheck + unit). ~80s -> ~45s.
- deploy-backend.yml: migrate-db -> detect-changes -> deploy-lambdas
  (matrix paralelo). Trigger: push a dev/stage/main. Concurrency queue
  por env.
- deploy-apps.yml: multi-env (dev/stage/main), matrix 6 niches en
  paralelo, reusa el artifact dist-all-apps-<sha> de ci.yml.
- Commit comment con resumen de cada deploy (tabla + URLs + duracion).
- .claude/rules/ci-cd-pipeline.md + skill + docs como referencia
  permanente.

## Como probar

```bash
# 1. Validar sintaxis de los 4 workflows
actionlint .github/workflows/*.yml

# 2. Tests devtools
python devtools/run.py test_runner --module=devtools --type=unit \
  -- -k 'state or change_detector'

# 3. Smoke E2E: PR de prueba a dev
git checkout -b test/smoke
echo "# trivial" >> serverless/lambda/services/cv/README.md
git commit -am "test: smoke" && git push
gh pr create --base dev --title "test: smoke"
# Esperar CI verde (~45s), mergear
gh pr merge <N> --merge --delete-branch
# Validar deploy-backend y deploy-apps en gh run list

# 4. Validar URLs deployadas
curl https://api.portfolio.dev.the-full-stack.com/cv?action=profile
for niche in generic hub fintech architect leader vibe; do
  curl -I https://$niche.portfolio.dev.the-full-stack.com | head -1
done
```

## TODO

(vacio — la carpeta del plan se elimina en el ultimo commit)
```
