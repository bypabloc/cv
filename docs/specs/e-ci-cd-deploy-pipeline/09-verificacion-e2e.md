# Fase Verificacion — E2E iterativa + eliminacion del plan

> Ultima fase y ultimo commit del plan. Validacion completa de la
> pipeline + eliminacion de `docs/specs/e-ci-cd-deploy-pipeline/`.

## Parte A — verificacion de cada componente aislado

### A.1 — devtools (Fases B + C)

```bash
python -m compileall -q devtools/serverless/state.py \
  devtools/serverless/change_detector.py

# Tests unit
python devtools/run.py test_runner --module=devtools --type=unit \
  -- -k 'state or change_detector'
```

Esperado: 9 + 12 = 21 tests verdes.

### A.2 — Sintaxis de los 4 workflows

```bash
# actionlint cubre sintaxis YAML + referencias a needs/outputs/secrets
actionlint .github/workflows/*.yml
```

Esperado: cero warnings.

### A.3 — Rule + skill + docs

```bash
ls .claude/rules/ci-cd-pipeline.md
ls .claude/skills/ci-cd-pipeline/SKILL.md
ls .claude/docs/ci-cd-pipeline/{README,aws-oidc-setup,deploy-runbook,troubleshooting}.md

# Validacion claude -p (5 prompts)
for prompt in \
  "como se deploya el backend al mergear a dev" \
  "que pasa si la migracion de DB falla en CI" \
  "donde vive el state de devtools cuando corre desde GitHub Actions" \
  "como rotar el role IAM del CI" \
  "como configurar tailwind"; do
  echo "--- $prompt ---"
  claude --permission-mode bypassPermissions \
    --disallowedTools "WebSearch" "WebFetch" \
    --strict-mcp-config --mcp-config '{"mcpServers":{}}' \
    --output-format json \
    -p "$prompt" 2>&1 | jq -r '"\(.num_turns) turns: \(.result[0:200])"'
done
```

Esperado: los 4 primeros con `num_turns > 1`; el ultimo (tailwind)
con `num_turns == 1`.

### A.4 — Estado AWS

```bash
# OIDC provider
aws iam list-open-id-connect-providers --aws-profile tfs-dev | \
  jq '.OpenIDConnectProviderList[] | select(.Arn | contains("token.actions.githubusercontent.com"))'

# 3 IAM roles
for env in dev stage prod; do
  aws iam get-role --role-name portfolio-deploy-$env \
    --aws-profile tfs-dev --query 'Role.Arn'
done

# Bucket S3 con encryption + versioning + public block
aws s3api get-bucket-versioning --bucket portfolio-devtools-state --aws-profile tfs-dev
aws s3api get-bucket-encryption --bucket portfolio-devtools-state --aws-profile tfs-dev
aws s3api get-public-access-block --bucket portfolio-devtools-state --aws-profile tfs-dev
```

Esperado: los 3 roles existen con trust policy correcta; el bucket
tiene los 3 settings activos.

## Parte B — smoke test E2E del pipeline

### B.1 — PR de prueba

```bash
git checkout dev && git pull
git checkout -b test/ci-cd-pipeline-smoke

# Cambio trivial en un archivo de cv (dispara redeploy de cv)
echo "# trivial change for smoke test" >> serverless/lambda/services/cv/README.md

git add -A
git commit -m "test(smoke): trigger ci-cd pipeline"
git push -u origin test/ci-cd-pipeline-smoke

# Abrir PR a dev
gh pr create --base dev --title "test: smoke ci-cd" --body "Smoke test del pipeline e-ci-cd-deploy-pipeline"
```

### B.2 — Validar que CI corre

```bash
# Esperar a que ci.yml (Lint + Build) termine
gh run watch
gh pr checks <PR_NUMBER>
```

Esperado: el check `Lint + Build` aparece como verde en ~45s.

### B.3 — Mergear y validar deploys

```bash
gh pr merge <PR_NUMBER> --merge --delete-branch
```

Esperar a que disparen `deploy-backend.yml` y `deploy-apps.yml` en
push a `dev`.

```bash
# Listar runs activos del branch dev
gh run list --branch dev --limit 5

# Watch del deploy-backend
gh run watch <run-id-backend>

# Watch del deploy-apps
gh run watch <run-id-apps>
```

Esperado:

1. **`deploy-backend.yml`**:
   - `resolve-env` -> `stage=dev`, role-arn correcto.
   - `migrate-db` -> verde (no hay migrations pending, exit 0).
   - `detect-changes` -> `affected=["cv"]`.
   - `deploy-lambdas` (matrix: 1 job para cv) -> verde.
   - `report` -> comentario en el commit.

2. **`deploy-apps.yml`**:
   - `resolve-env` -> `stage=dev`, project-suffix=`-dev`.
   - `build-apps` -> reusa artifact `dist-all-apps-<sha>` (CI ya
     corrio).
   - `deploy-pages` (matrix: 6 niches) -> verde.
   - `report` -> comentario en el commit con las 6 URLs
     `*.portfolio.dev.the-full-stack.com`.

### B.4 — Validar los deploys reales

```bash
# CV deploy
curl https://api.portfolio.dev.the-full-stack.com/cv?action=profile&locale=es

# Apps deploy (las 6 niches)
for niche in generic hub fintech architect leader vibe; do
  curl -I https://$niche.portfolio.dev.the-full-stack.com | head -2
done
```

Esperado: HTTP 200 en todos.

### B.5 — Validar S3 state

```bash
aws s3 ls s3://portfolio-devtools-state/state/ --aws-profile tfs-dev
```

Esperado: existe `cv-dev.json` (y eventualmente todos los lambdas
desplegados desde CI).

### B.6 — Validar concurrency queue

Push 2 commits seguidos (con 5s de delta) a `dev`:

```bash
git commit --allow-empty -m "test: trigger 1" && git push
sleep 5
git commit --allow-empty -m "test: trigger 2" && git push
gh run list --branch dev --limit 3
```

Esperado: el segundo run aparece como `queued`, no `in_progress`,
hasta que el primero termine.

## Parte C — Bucle de correccion

Si CUALQUIER paso falla:

1. Leer el output completo del comando/job fallido.
2. Identificar la causa.
3. Corregir.
4. Re-correr la suite desde el paso fallido.
5. NO mergear con un solo rojo.

## Parte D — Eliminacion del plan

Ultimo commit:

```bash
git rm -r docs/specs/e-ci-cd-deploy-pipeline/
```

Mensaje del commit:

```text
test(ci-cd): verificacion E2E del pipeline + elimina plan

Bateria de verificacion completa:

- A.1 devtools: 21 tests verdes (state + change_detector)
- A.2 actionlint: 4 workflows sin warnings
- A.3 .claude validation: 5 prompts (4 positivos invocan skill,
  1 negativo no)
- A.4 AWS: OIDC provider + 3 roles + bucket S3 (encryption + versioning
  + public block) verificados
- B.1-B.6 smoke test E2E: PR a dev -> CI verde 45s -> merge ->
  deploy-backend exitoso (1 lambda afectado) -> deploy-apps exitoso
  (6 niches) -> URLs HTTP 200 -> S3 state poblado -> concurrency
  queue funciona

Elimina docs/specs/e-ci-cd-deploy-pipeline/ (plan efimero). Los
artefactos permanentes son:
- .github/workflows/{ci,deploy-backend,deploy-apps}.yml
- devtools/serverless/{state,change_detector}.py
- .claude/rules/ci-cd-pipeline.md + skill + docs
- AWS infra: OIDC provider + 3 IAM roles + bucket S3
```

## Criterios de aceptacion globales

- **AC-V1**: Given los 4 workflows en el repo, When inspecciono
  `gh workflow list`, Then aparecen los 4 nombrados correctamente.
- **AC-V2**: Given el smoke test E2E, When inspecciono el ultimo
  commit en `dev`, Then existen 2 commit comments (uno de backend,
  uno de apps).
- **AC-V3**: Given un push a `main` con cambio en `serverless/lambda/shared/core/`,
  When inspecciono `detect-changes`, Then `affected` incluye los 5
  lambdas (excepto db que ya fue redeployado en migrate).
- **AC-V4**: Given el commit final, When `git show --stat`, Then
  contiene `delete mode docs/specs/e-ci-cd-deploy-pipeline/...`.
