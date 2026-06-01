# AWS OIDC + S3 state setup — runbook

> Configuracion MANUAL (una sola vez) que habilita el pipeline CI/CD del
> portfolio. Crea: OpenID Connect provider en AWS, 3 IAM roles
> (dev/stage/prod) con trust policy scoped al repo + branch, y el bucket
> S3 `portfolio-devtools-state` con encryption KMS + versioning +
> lifecycle.

## Pre-requisitos

| Recurso | Valor |
|---------|-------|
| Account AWS | `637423614564` |
| Region | `us-east-1` (igual que los Lambdas y SES) |
| AWS profile local | `tfs-dev` (IAM user `dev`, AdministratorAccess) |
| GitHub repo | `bypabloc/cv` |
| KMS key | `alias/portfolio-lambdas` (ya existe) |

> Si el shell tiene `AWS_PROFILE` exportado, los comandos lo respetan.
> Sino, agregar `--profile tfs-dev` explicitamente.

## Paso 1: Crear OIDC provider

```bash
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1 \
  --region us-east-1
```

> AWS valida el thumbprint automaticamente desde mediados de 2023. El
> parametro `--thumbprint-list` es requerido por el API pero su valor
> es legacy compat.

Verificar:

```bash
aws iam list-open-id-connect-providers \
  --query 'OpenIDConnectProviderList[?contains(Arn, `token.actions.githubusercontent.com`)].Arn' \
  --output text
```

Esperado: `arn:aws:iam::637423614564:oidc-provider/token.actions.githubusercontent.com`.

## Paso 2: Crear los 3 IAM roles

### 2.1 — Trust policy por rol

Crear tres archivos JSON en `./tmp/iam/` (efimero, NO commitear):

```bash
mkdir -p ./tmp/iam
```

`./tmp/iam/trust-dev.json`:

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
        "token.actions.githubusercontent.com:sub": "repo:bypabloc/cv:ref:refs/heads/dev"
      }
    }
  }]
}
```

`./tmp/iam/trust-stage.json`: idem, cambiar `dev` -> `stage`.
`./tmp/iam/trust-prod.json`: idem, cambiar `dev` -> `main`.

### 2.2 — Permissions policy (UNICA, comparten los 3 roles)

`./tmp/iam/policy-permissions.json`:

```jsonc
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "LambdaManagement",
      "Effect": "Allow",
      "Action": [
        "lambda:CreateFunction",
        "lambda:UpdateFunctionCode",
        "lambda:UpdateFunctionConfiguration",
        "lambda:DeleteFunction",
        "lambda:GetFunction",
        "lambda:GetFunctionConfiguration",
        "lambda:InvokeFunction",
        "lambda:ListFunctions",
        "lambda:AddPermission",
        "lambda:RemovePermission",
        "lambda:GetPolicy",
        "lambda:CreateEventSourceMapping",
        "lambda:UpdateEventSourceMapping",
        "lambda:DeleteEventSourceMapping",
        "lambda:ListEventSourceMappings",
        "lambda:TagResource",
        "lambda:UntagResource"
      ],
      "Resource": "*"
    },
    {
      "Sid": "IAMForLambdaExecutionRoles",
      "Effect": "Allow",
      "Action": [
        "iam:PassRole",
        "iam:CreateRole",
        "iam:DeleteRole",
        "iam:GetRole",
        "iam:UpdateRole",
        "iam:AttachRolePolicy",
        "iam:DetachRolePolicy",
        "iam:PutRolePolicy",
        "iam:DeleteRolePolicy",
        "iam:GetRolePolicy",
        "iam:ListRolePolicies",
        "iam:ListAttachedRolePolicies",
        "iam:TagRole",
        "iam:UntagRole"
      ],
      "Resource": "arn:aws:iam::637423614564:role/portfolio-*"
    },
    {
      "Sid": "CloudWatchLogs",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:DeleteLogGroup",
        "logs:PutRetentionPolicy",
        "logs:DescribeLogGroups",
        "logs:TagResource",
        "logs:UntagResource"
      ],
      "Resource": "*"
    },
    {
      "Sid": "APIGateway",
      "Effect": "Allow",
      "Action": "apigateway:*",
      "Resource": "*"
    },
    {
      "Sid": "DynamoDB",
      "Effect": "Allow",
      "Action": [
        "dynamodb:DescribeTable",
        "dynamodb:UpdateTable",
        "dynamodb:DescribeContinuousBackups",
        "dynamodb:UpdateContinuousBackups",
        "dynamodb:DescribeTimeToLive",
        "dynamodb:UpdateTimeToLive",
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:Query",
        "dynamodb:ListTables",
        "dynamodb:TagResource",
        "dynamodb:UntagResource"
      ],
      "Resource": "*"
    },
    {
      "Sid": "SQS",
      "Effect": "Allow",
      "Action": [
        "sqs:CreateQueue",
        "sqs:GetQueueAttributes",
        "sqs:SetQueueAttributes",
        "sqs:GetQueueUrl",
        "sqs:ListQueues",
        "sqs:TagQueue",
        "sqs:UntagQueue"
      ],
      "Resource": "*"
    },
    {
      "Sid": "SSMParameterStore",
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameter",
        "ssm:GetParameters",
        "ssm:GetParametersByPath",
        "ssm:PutParameter",
        "ssm:DescribeParameters"
      ],
      "Resource": [
        "arn:aws:ssm:us-east-1:637423614564:parameter/portfolio/*"
      ]
    },
    {
      "Sid": "KMS",
      "Effect": "Allow",
      "Action": [
        "kms:Decrypt",
        "kms:GenerateDataKey",
        "kms:DescribeKey"
      ],
      "Resource": "arn:aws:kms:us-east-1:637423614564:key/*",
      "Condition": {
        "ForAnyValue:StringEquals": {
          "kms:ResourceAliases": ["alias/portfolio-lambdas"]
        }
      }
    },
    {
      "Sid": "S3DevtoolsState",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::portfolio-devtools-state",
        "arn:aws:s3:::portfolio-devtools-state/*"
      ]
    },
    {
      "Sid": "S3EmailTemplates",
      "Effect": "Allow",
      "Action": [
        "s3:CreateBucket",
        "s3:PutBucketPublicAccessBlock",
        "s3:PutEncryptionConfiguration",
        "s3:GetEncryptionConfiguration",
        "s3:ListBucket",
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": [
        "arn:aws:s3:::portfolio-email-templates-dev",
        "arn:aws:s3:::portfolio-email-templates-dev/*",
        "arn:aws:s3:::portfolio-email-templates-stage",
        "arn:aws:s3:::portfolio-email-templates-stage/*",
        "arn:aws:s3:::portfolio-email-templates-prod",
        "arn:aws:s3:::portfolio-email-templates-prod/*"
      ]
    }
  ]
}
```

> El statement `S3EmailTemplates` lo necesita `provision-infra` + `seed-email-config`
> para crear/configurar el bucket de templates de email y subir los archivos.
> El statement `SQS` quedo OBSOLETO tras eliminar SQS del backend (invoke async
> Lambda->Lambda): no hace dano (no hay colas que crear) pero se puede quitar.

### 2.3 — Crear los 3 roles

```bash
for env in dev stage prod; do
  aws iam create-role \
    --role-name portfolio-deploy-$env \
    --assume-role-policy-document file://./tmp/iam/trust-$env.json \
    --description "GitHub Actions OIDC role for portfolio deploys to $env" \
    --max-session-duration 3600

  aws iam put-role-policy \
    --role-name portfolio-deploy-$env \
    --policy-name portfolio-deploy-permissions \
    --policy-document file://./tmp/iam/policy-permissions.json
done
```

Verificar:

```bash
for env in dev stage prod; do
  echo "--- portfolio-deploy-$env ---"
  aws iam get-role --role-name portfolio-deploy-$env \
    --query 'Role.[Arn,AssumeRolePolicyDocument.Statement[0].Condition.StringLike]'
done
```

Anotar los 3 ARNs — los referenciamos en el workflow:

- `arn:aws:iam::637423614564:role/portfolio-deploy-dev`
- `arn:aws:iam::637423614564:role/portfolio-deploy-stage`
- `arn:aws:iam::637423614564:role/portfolio-deploy-prod`

## Paso 3: Crear bucket S3 portfolio-devtools-state

```bash
# Crear (us-east-1 NO acepta LocationConstraint)
aws s3api create-bucket \
  --bucket portfolio-devtools-state \
  --region us-east-1

# Bloquear acceso publico (defense in depth)
aws s3api put-public-access-block \
  --bucket portfolio-devtools-state \
  --public-access-block-configuration \
  BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

# Versioning (preserva versions anteriores del JSON)
aws s3api put-bucket-versioning \
  --bucket portfolio-devtools-state \
  --versioning-configuration Status=Enabled

# Encryption con KMS del portfolio
aws s3api put-bucket-encryption \
  --bucket portfolio-devtools-state \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "aws:kms",
        "KMSMasterKeyID": "alias/portfolio-lambdas"
      }
    }]
  }'
```

Lifecycle (borra versions viejas a los 30 dias):

`./tmp/iam/s3-lifecycle.json`:

```jsonc
{
  "Rules": [{
    "ID": "expire-old-versions",
    "Status": "Enabled",
    "Filter": {},
    "NoncurrentVersionExpiration": {"NoncurrentDays": 30},
    "AbortIncompleteMultipartUpload": {"DaysAfterInitiation": 7}
  }]
}
```

```bash
aws s3api put-bucket-lifecycle-configuration \
  --bucket portfolio-devtools-state \
  --lifecycle-configuration file://./tmp/iam/s3-lifecycle.json
```

Verificar:

```bash
aws s3api get-bucket-versioning --bucket portfolio-devtools-state
aws s3api get-bucket-encryption --bucket portfolio-devtools-state
aws s3api get-public-access-block --bucket portfolio-devtools-state
aws s3api get-bucket-lifecycle-configuration --bucket portfolio-devtools-state
```

## Paso 4: Smoke test del OIDC desde GitHub Actions

Crear archivo temporal en la rama del plan o feature:

`.github/workflows/_test-oidc.yml` (efimero, se borra tras validar):

```yaml
name: Test OIDC
on:
  workflow_dispatch:
    inputs:
      env:
        description: "Env del rol a asumir"
        required: true
        type: choice
        options: [dev, stage, prod]

permissions:
  id-token: write
  contents: read

jobs:
  test:
    runs-on: ubuntu-24.04
    steps:
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::637423614564:role/portfolio-deploy-${{ inputs.env }}
          aws-region: us-east-1
      - run: aws sts get-caller-identity
```

Disparar desde la branch correcta:

```bash
git checkout dev   # o stage, o main
gh workflow run _test-oidc.yml --field env=dev
gh run watch
```

Esperado en el log:

```jsonc
{
    "UserId": "AROAxxxxxxxxxxx:GitHubActions",
    "Account": "637423614564",
    "Arn": "arn:aws:sts::637423614564:assumed-role/portfolio-deploy-dev/GitHubActions"
}
```

Test cross-branch (defensa en profundidad):

```bash
# Desde rama dev intentar asumir el role de prod -> debe fallar
gh workflow run _test-oidc.yml --field env=prod --ref dev
```

Esperado: el workflow falla con `AccessDenied` (el sub `repo:bypabloc/cv:ref:refs/heads/dev` no matchea la trust policy del rol prod).

## Paso 5: Limpieza

```bash
# Borrar el workflow temporal
git rm .github/workflows/_test-oidc.yml
git commit -m "chore(ci): elimina test workflow _test-oidc.yml tras validar"

# Borrar los JSONs temporales
rm -rf ./tmp/iam/
```

## Rollback (solo si hace falta)

Si algo sale mal y querés deshacer:

```bash
# Borrar los 3 roles
for env in dev stage prod; do
  aws iam delete-role-policy --role-name portfolio-deploy-$env \
    --policy-name portfolio-deploy-permissions
  aws iam delete-role --role-name portfolio-deploy-$env
done

# Borrar el OIDC provider
aws iam delete-open-id-connect-provider \
  --open-id-connect-provider-arn \
  arn:aws:iam::637423614564:oidc-provider/token.actions.githubusercontent.com

# Vaciar y borrar el bucket
aws s3 rm s3://portfolio-devtools-state --recursive
aws s3api delete-bucket --bucket portfolio-devtools-state
```

## Notas operativas

- Los IAM roles son scoped por branch en el `sub`. Si en el futuro
  agregas una branch `release/*`, hay que extender el `StringLike` con
  el patron correspondiente.
- La `--max-session-duration 3600` (1h) basta para los workflows. Si
  un deploy tarda mas, GH Actions renueva el token automaticamente.
- El bucket S3 tiene versioning + lifecycle. Si necesitas inspectar
  un state anterior: `aws s3api list-object-versions --bucket
  portfolio-devtools-state --prefix state/`.
- Costos: 3 roles + 1 OIDC provider + 1 bucket S3 = $0/mes (free
  tier perpetuo).

## Referencias cruzadas

- `.claude/rules/serverless-secrets.md` — inventario completo de
  SSM + KMS del portfolio.
- `.claude/rules/ci-cd-pipeline.md` — workflows que consumen estos
  roles.
- `devtools/serverless/state.py` — backend S3 que usa este bucket.
- AWS OIDC docs: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_oidc.html
