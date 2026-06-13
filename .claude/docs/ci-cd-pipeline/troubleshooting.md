# Troubleshooting CI/CD pipeline

> Errores comunes del pipeline CI/CD y como diagnosticarlos.

## OIDC: "Could not assume role with OIDC"

**Sintoma**: el step `aws-actions/configure-aws-credentials@v4` falla con:

```text
Error: Could not assume role with OIDC: ...
```

**Causas y fixes**:

| Causa | Fix |
|-------|-----|
| Trust policy del rol NO matchea la branch desde donde se dispara | Verificar el `StringLike: sub` del rol. Disparar el workflow desde la branch correspondiente, NO desde una feature branch |
| OIDC provider no creado | `aws iam list-open-id-connect-providers` debe listar el de github |
| `permissions.id-token: write` faltante en el workflow | Agregar el bloque `permissions` con `id-token: write` |
| El workflow corre en un fork | OIDC NO funciona en forks externos por seguridad |

```bash
# Diagnostico desde local (con perfil tfs-dev)
aws iam get-role --role-name portfolio-deploy-dev \
  --query 'Role.AssumeRolePolicyDocument.Statement[0].Condition'
```

## S3 state: "NoSuchKey" en primer deploy

**Sintoma**: el workflow corre por primera vez y devtools NO encuentra
el state.

**Es esperado**: el backend S3 devuelve `None` cuando el archivo no
existe. devtools entonces decide `Action.CREATE` y crea todos los
recursos desde cero. No es un error.

## Migrate falla: "relation does not exist"

**Sintoma**: la Lambda `db` lanza `psycopg.errors.UndefinedTable: relation "X" does not exist`.

**Causa**: el branch Neon esta vacio (sin schema). Las migrations
Alembic NO se aplicaron alguna vez.

**Fix**:

```bash
# Aplicar migraciones desde local (en el dev branch primero)
python devtools/run.py serverless run --lambda=db --stage=dev \
  --event=serverless/lambda/services/db/events/migrate.json \
  --aws-profile=tfs-dev

# Ver revision actual
python devtools/run.py serverless run --lambda=db --stage=dev \
  --event=serverless/lambda/services/db/events/current.json \
  --aws-profile=tfs-dev
```

Si el schema ya existe (creado fuera de Alembic), usar `stamp` antes
de `migrate`:

```bash
python devtools/run.py serverless run --lambda=db --stage=dev \
  --event=serverless/lambda/services/db/events/stamp.json \
  --aws-profile=tfs-dev
```

Detalle: `.claude/rules/neon-management.md` seccion "Migrations".

## Deploy Lambda: "CodeStorageExceededException"

**Sintoma**:

```text
botocore.errorfactory.CodeStorageExceededException: ...
```

**Causa**: el zip del Lambda excede el limite de AWS (50 MB unzipped
o 250 MB total con layers).

**Diagnostico**:

```bash
ls -lh serverless/lambda/services/<lambda>/build.zip
du -sh serverless/lambda/services/<lambda>/build/
```

**Fix**:
- Revisar que `core/shared/` solo contiene los subpaquetes del cierre
  transitivo (no toda `shared/`).
- Revisar deps en `pyproject.toml` del Lambda: ninguna debe duplicar
  lo que `shared/` ya aporta (regla D-3, validada por `serverless
  lint-deps`).
- Si la dep es grande (ej. boto3 ~50 MB), confirmar que NO se
  vendoriza — AWS la provee en el runtime.

## Cloudflare Pages: "project not found"

**Sintoma**:

```text
✘ A request to the Cloudflare API ... failed.
project not found
```

**Causa**: el nombre del proyecto Pages no existe en la cuenta.

**Fix**:

```bash
# Listar proyectos existentes
gh api -H "Accept: application/json" \
  "https://api.cloudflare.com/client/v4/accounts/$CLOUDFLARE_ACCOUNT_ID/pages/projects" \
  | jq -r '.result[].name' | sort

# Crear el faltante (ej. vibe-dev)
# Ver skill 'cloudflare-deploy' para el comando exacto.
```

## detect-changes devuelve vacio cuando esperaba cambios

**Sintoma**: el workflow corre pero `deploy-lambdas` se salta porque
`detect-changes.outputs.has-affected == 'false'`.

**Causas**:

1. El cambio toca solo paths excluidos (`tests/`, `events/`, `build/`,
   `shared/tests/`).
2. `github.event.before` es `zeros` (primer push) -> fallback a
   `HEAD~10`. Si el cambio relevante esta mas atras, no lo detecta.
3. El cambio toca `apps/` o `packages/` (no es backend) -> correcto,
   no dispara `deploy-backend`.

**Diagnostico**:

```bash
# Replicar localmente
python devtools/run.py serverless detect-changes \
  --base=$(git rev-parse HEAD~5) --head=HEAD
```

## Concurrency: workflow se queda en "queued" forever

**Sintoma**: un push a `dev` queda `queued` y nunca arranca.

**Causa**: hay otro workflow del mismo grupo (`deploy-backend-dev` o
`deploy-apps-dev`) corriendo. La queue (cancel-in-progress: false)
espera al primero.

**Fix**:
- Esperar (lo normal).
- Si el primero esta colgado: cancelarlo desde la UI o `gh run cancel <id>`.

## "AccessDenied" al hacer `aws ssm get-parameter`

**Sintoma**: el Lambda en runtime falla leyendo SSM:

```text
ClientError: An error occurred (AccessDenied) when calling the
GetParameter operation: User: ... is not authorized to perform:
ssm:GetParameter on resource: arn:aws:ssm:us-east-1:...:parameter/portfolio/...
```

**Causa**: el rol de ejecucion del Lambda (NO el del CI) no tiene
permisos sobre el parametro.

**Diagnostico**: revisar la IAM policy del rol del Lambda
(`portfolio-<lambda>-<stage>-role`), no del rol del CI.

**Fix**: el manifest del Lambda declara los SSM paths que necesita.
Confirmar que el provisioner genero la policy correcta:

```bash
aws iam list-role-policies --role-name portfolio-<lambda>-<stage>-role \
  --aws-profile=tfs-dev
aws iam get-role-policy --role-name portfolio-<lambda>-<stage>-role \
  --policy-name <name> --aws-profile=tfs-dev
```

Si esta mal, hacer `serverless deploy` para que el provisioner
re-aplique la policy.

## Workflow falla con "Unable to find any artifact for the run"

**Sintoma**: `deploy-apps.yml` corre `actions/download-artifact@v4` y
falla con esta excepcion.

**Causa**: `ci.yml` no termino antes que `deploy-apps.yml`, o no
subio el artifact (PR, no push).

**Fix**: el step tiene `continue-on-error: true`. Cuando falla,
`deploy-apps.yml` rebuilda local automaticamente (vias if del
`steps.try-artifact.outcome`). Si ves esta excepcion como FATAL,
revisar el step `Re-upload artifact for matrix` — `if-no-files-found:
error` ahi sin un rebuild previo lo causaria.

## Commit comment no aparece

**Sintoma**: el workflow termina verde pero no hay comment en el commit.

**Causas**:

| Causa | Fix |
|-------|-----|
| `permissions.pull-requests: write` faltante | Agregar al workflow |
| `peter-evans/commit-comment@v3` falla silenciosamente | Inspeccionar el log del step |
| El SHA del commit no existe (workflow disparado en push force) | Esperado; no es bug |

## Como saber si OIDC funciona sin deployar

Smoke test con workflow temporal `_test-oidc.yml` (ver
[aws-oidc-setup.md](aws-oidc-setup.md) seccion Paso 4):

```bash
gh workflow run _test-oidc.yml --field env=dev --ref dev
gh run watch
```

El log debe mostrar:

```jsonc
{
    "UserId": "AROA...:GitHubActions",
    "Account": "637423614564",
    "Arn": "arn:aws:sts::637423614564:assumed-role/portfolio-deploy-dev/GitHubActions"
}
```

## Navegacion

- Setup inicial: [aws-oidc-setup.md](aws-oidc-setup.md)
- Indice: [README.md](README.md)
- Rule: `.claude/rules/ci-cd-pipeline.md`
