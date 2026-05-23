# Fase A — Infra AWS: OIDC + S3 state bucket

> Setup MANUAL en AWS (una sola vez, no automatizable porque crea la
> infra de CI/CD inicial). Configurar OpenID Connect provider para
> GitHub Actions + 3 IAM roles (dev/stage/prod) con trust policy
> scoped al repo + crear bucket S3 para el estado de devtools.

## Contexto / Problema

Hoy AWS credentials viven en `docker/env/dev-cli/.{dev,local,prod}`
(IAM user con AdministratorAccess). No hay forma de que GitHub
Actions se autentique a AWS sin meter esas keys como secrets — eso
seria de larga vida, sin rotacion automatica, leak risk.

GitHub Actions soporta OIDC desde 2021: el workflow recibe un JWT
firmado por GitHub, AWS lo valida contra el OIDC provider y emite
credenciales temporales (15 min - 12h). Cero secrets en GitHub.

## Solucion

Tres bloques que se ejecutan UNA SOLA VEZ, en orden:

### A.1 — Crear OIDC provider en AWS

```bash
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1 \
  --aws-profile tfs-dev
```

(El thumbprint de github.com es estable; AWS lo verifica automaticamente
desde mediados de 2023 — el parametro es legacy compat. Se documenta
en `01-fase-a-aws-oidc-s3-state.md` por completitud.)

### A.2 — Crear 3 IAM roles por env

Para cada `env` ∈ {`dev`, `stage`, `prod`}:

**Trust policy** (`portfolio-deploy-${env}-trust.json`):

```jsonc
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "Federated": "arn:aws:iam::637423614564:oidc-provider/token.actions.githubusercontent.com"
    },
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringEquals": {
        "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
      },
      "StringLike": {
        // dev role: solo desde la rama dev del repo bypabloc/cv
        "token.actions.githubusercontent.com:sub": "repo:bypabloc/cv:ref:refs/heads/dev"
      }
    }
  }]
}
```

Para `stage`: `sub` = `repo:bypabloc/cv:ref:refs/heads/stage`.
Para `prod`: `sub` = `repo:bypabloc/cv:ref:refs/heads/main`.

**Permissions policy** (`portfolio-deploy-${env}-policy.json`):

Necesita permisos para:
- `lambda:CreateFunction`, `UpdateFunctionCode`, `UpdateFunctionConfiguration`, `DeleteFunction`, `GetFunction`, `InvokeFunction`
- `iam:PassRole` (para el execution role del Lambda)
- `iam:CreateRole`, `AttachRolePolicy`, `PutRolePolicy`, `GetRole` (provisioner crea roles para los Lambdas)
- `logs:CreateLogGroup`, `PutRetentionPolicy`, `DeleteLogGroup`
- `apigateway:*` (acotado al ARN del API GW del portfolio)
- `dynamodb:*Item`, `Query`, `Scan`, `DescribeTable`, `UpdateTable` (acotado a las tablas del portfolio)
- `ssm:GetParameter` sobre `/portfolio/${env}/*` y `/portfolio/turnstile-secret`
- `kms:Decrypt` sobre la KMS key `alias/portfolio-lambdas`
- `s3:GetObject`, `PutObject`, `ListBucket` sobre `portfolio-devtools-state`
- `sqs:CreateQueue`, `GetQueueAttributes`, `SetQueueAttributes` (para DLQ del stream_processor)

(El JSON completo va en el doc operativo del commit, no aqui — es
largo y vive en `.claude/docs/ci-cd-pipeline/`.)

```bash
for env in dev stage prod; do
  aws iam create-role \
    --role-name portfolio-deploy-$env \
    --assume-role-policy-document file://portfolio-deploy-$env-trust.json \
    --aws-profile tfs-dev

  aws iam put-role-policy \
    --role-name portfolio-deploy-$env \
    --policy-name portfolio-deploy-$env-permissions \
    --policy-document file://portfolio-deploy-$env-policy.json \
    --aws-profile tfs-dev
done
```

Anotar los ARNs:
- `arn:aws:iam::637423614564:role/portfolio-deploy-dev`
- `arn:aws:iam::637423614564:role/portfolio-deploy-stage`
- `arn:aws:iam::637423614564:role/portfolio-deploy-prod`

### A.3 — Crear bucket S3 portfolio-devtools-state

```bash
aws s3api create-bucket \
  --bucket portfolio-devtools-state \
  --region us-east-1 \
  --aws-profile tfs-dev

# Versioning para audit trail (cada deploy genera version nueva del JSON)
aws s3api put-bucket-versioning \
  --bucket portfolio-devtools-state \
  --versioning-configuration Status=Enabled \
  --aws-profile tfs-dev

# Encryption at rest (KMS key del portfolio)
aws s3api put-bucket-encryption \
  --bucket portfolio-devtools-state \
  --server-side-encryption-configuration \
  '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"aws:kms","KMSMasterKeyID":"alias/portfolio-lambdas"}}]}' \
  --aws-profile tfs-dev

# Bloquear acceso publico (defensa en profundidad)
aws s3api put-public-access-block \
  --bucket portfolio-devtools-state \
  --public-access-block-configuration \
  BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true \
  --aws-profile tfs-dev

# Lifecycle: borrar versions viejas (>30 dias) para no acumular costo
aws s3api put-bucket-lifecycle-configuration \
  --bucket portfolio-devtools-state \
  --lifecycle-configuration file://lifecycle.json \
  --aws-profile tfs-dev
```

`lifecycle.json`:

```jsonc
{
  "Rules": [{
    "ID": "expire-old-versions",
    "Status": "Enabled",
    "NoncurrentVersionExpiration": {"NoncurrentDays": 30}
  }]
}
```

### A.4 — Verificacion del setup

```bash
# El provider existe
aws iam list-open-id-connect-providers --aws-profile tfs-dev

# Los 3 roles existen
for env in dev stage prod; do
  aws iam get-role --role-name portfolio-deploy-$env \
    --aws-profile tfs-dev --query 'Role.Arn'
done

# El bucket existe y tiene versioning + encryption + public block
aws s3api get-bucket-versioning --bucket portfolio-devtools-state --aws-profile tfs-dev
aws s3api get-bucket-encryption --bucket portfolio-devtools-state --aws-profile tfs-dev
aws s3api get-public-access-block --bucket portfolio-devtools-state --aws-profile tfs-dev
```

Smoke test desde un workflow temporal (no commiteado):

```yaml
# .github/workflows/_test-oidc.yml (efimero, se borra tras validar)
name: Test OIDC
on: workflow_dispatch
permissions:
  id-token: write
  contents: read
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::637423614564:role/portfolio-deploy-dev
          aws-region: us-east-1
      - run: aws sts get-caller-identity
```

Esperado: imprime el ARN de la sesion temporal asumida.

## Archivos afectados

### Crear (manualmente, NO commiteados al repo principal)

- `~/portfolio-deploy-dev-trust.json`, idem stage/prod (efimeros, se
  borran tras crear los roles).
- `~/portfolio-deploy-dev-policy.json`, idem stage/prod.
- `~/lifecycle.json`.

### Crear (commiteados, documentacion)

- `.claude/docs/ci-cd-pipeline/aws-oidc-setup.md` — runbook completo
  con los JSONs full + comandos + verificacion. Para que el setup sea
  reproducible si hace falta recrear la infra.

## Criterios de aceptacion

- **AC-A1**: Given el OIDC provider creado, When ejecuto `aws iam
  list-open-id-connect-providers`, Then aparece
  `arn:aws:iam::637423614564:oidc-provider/token.actions.githubusercontent.com`.
- **AC-A2**: Given los 3 roles creados, When ejecuto `aws iam get-role
  --role-name portfolio-deploy-<env>`, Then existe y su trust policy
  tiene `StringLike: sub: repo:bypabloc/cv:ref:refs/heads/<env-branch>`.
- **AC-A3**: Given el bucket S3, When ejecuto `aws s3api
  get-bucket-versioning`, Then `Status: Enabled`. Idem encryption KMS.
- **AC-A4**: Given el workflow temporal `_test-oidc.yml` corrido en
  branch `dev`, When inspecciono el log, Then `aws sts
  get-caller-identity` retorna el ARN del rol asumido (no del IAM
  user del fork).
- **AC-A5**: Given un workflow corrido con `role-to-assume:
  portfolio-deploy-prod` desde la branch `dev`, When intenta asumir el
  rol, Then falla con `AccessDenied` (el sub no matchea — defensa en
  profundidad contra deploy accidental a prod desde dev).

## Verificacion

```bash
# AC-A1
aws iam list-open-id-connect-providers --aws-profile tfs-dev

# AC-A2
for env in dev stage prod; do
  aws iam get-role --role-name portfolio-deploy-$env --aws-profile tfs-dev \
    --query 'Role.AssumeRolePolicyDocument.Statement[0].Condition'
done

# AC-A3
aws s3api get-bucket-versioning --bucket portfolio-devtools-state --aws-profile tfs-dev
aws s3api get-bucket-encryption --bucket portfolio-devtools-state --aws-profile tfs-dev

# AC-A4 + AC-A5: gh workflow run _test-oidc.yml en cada branch
```

## Commit

```text
docs(ci-cd): runbook AWS OIDC + S3 state bucket setup

- .claude/docs/ci-cd-pipeline/aws-oidc-setup.md: runbook completo
  para crear OIDC provider, 3 IAM roles (portfolio-deploy-{dev,stage,
  prod}) y bucket S3 portfolio-devtools-state con encryption KMS +
  versioning + lifecycle + public block
- Trust policy de cada rol scoped al repo bypabloc/cv y a la rama
  correspondiente (dev/stage/main) para defensa en profundidad
- Permissions policy escoped a lambda, iam:PassRole, logs, apigateway,
  dynamodb, ssm:/portfolio/{env}/*, kms:Decrypt sobre la key del
  portfolio y s3 sobre portfolio-devtools-state
- Comandos de verificacion (sts get-caller-identity desde el workflow
  temporal _test-oidc.yml en cada branch)
- Setup manual (una sola vez); las fases siguientes asumen la infra
  creada
```

## Notas

- El setup es MANUAL en AWS porque NO podemos automatizarlo desde
  GitHub Actions (huevo-y-gallina: el workflow necesita el rol para
  correr).
- Lo hace el operador con el perfil `tfs-dev` (IAM user con
  AdministratorAccess).
- Los JSONs `*-trust.json` y `*-policy.json` van en el runbook, no
  en el repo principal — pueden recrearse desde el runbook si la
  infra se pierde.
- AWS Account ID `637423614564` esta documentado en
  `.claude/rules/serverless-secrets.md`.
