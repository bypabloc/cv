# SPEC-000: Setup inicial del backend serverless

**Estado**: done
**Autor**: Pablo Contreras
**Fecha**: 2026-05-14
**Ejecutado**: 2026-05-14
**Areas afectadas**: AWS account 637423614564, Cloudflare account, SSM Parameter Store, KMS, CloudWatch Alarms, SNS
**Dependencias**: ninguna
**Paralelizable con**: SPEC-011 (SES DNS)

## Cambios respecto al draft original

- **Region**: us-east-1 (no us-west-2). SES ya tiene Production Access GRANTED
  en us-east-1 (case `173472640000887`), evitamos 24-48h de espera.
- **Cuentas**: AWS `637423614564` (IAM user `dev` con Administrator),
  Cloudflare account `f009aedf484e283f64a758dbcd725e9a`, Neon (project propio
  con `DB_URL` en `docker/env/.dev`).
- **Turnstile widget nuevo**: `Portfolio Backend` (sitekey `0x4AAAAAADPSoiQA_-LcRafo`)
  con 8 hostnames (6 subdominios + `localhost` + `127.0.0.1`).
- **Estrategia hibrida secrets**: solo `turnstile-secret` y `neon-url` en SSM
  con KMS. Resto en env vars del SAM template (ver `serverless/docs/secrets.md`).

## 1. Contexto

Antes de poder ejecutar SAM deploy, hay configuraciones manuales que viven
fuera del template.yaml (la decision esta documentada en
[serverless/ARCHITECTURE.md](../ARCHITECTURE.md) seccion 7 "NOT in
template.yaml"). Este setup es prerequisito de todas las otras specs.

### Hallazgos de exploracion

- AWS account ya existe (verificar perfil AWS CLI configurado)
- Cloudflare account ya gestiona DNS de `the-full-stack.com`
- SES tiene un correo verificado historico (preguntar usuario antes de
  cualquier accion potencialmente destructiva)
- Skill `cloudflare-deploy` ya configurado para gestionar DNS

## 2. Solucion propuesta

Setup en 5 pasos manuales documentados, todos idempotentes:

1. Verificar credenciales AWS CLI (perfil + region us-east-1)
2. Crear KMS key custom + alias `alias/portfolio-lambdas` para encryption
   de SSM SecureStrings
3. Crear SSM Parameters base (Turnstile secret, Neon URL placeholder,
   owner email, SES from address)
4. Crear Cloudflare Turnstile widget en dashboard + registrar 6 hostnames
5. Configurar AWS Billing Alarm global ($50 USD threshold) — UNICA alarma
   permitida en este diseno (gratis, no `AWS::CloudWatch::Alarm`)

### Decisiones clave

- **Decision 1: KMS customer-managed key** — vs AWS-owned key default.
  Razon: rotar la key sin redesplegar Lambdas. Costo: $1/mes (no en free
  tier permanente pero unico AWS managed cost que aceptamos).
- **Decision 2: 4 SSM Parameters separados** — vs 1 JSON blob. Razon:
  rotar individualmente sin perder los demas + IAM scope granular.
- **Decision 3: AWS Billing Alarm en region us-east-1** — el billing
  service AWS solo emite metricas en us-east-1. La alarma se configura
  alli aunque el resto del stack vive en us-east-1.

## 3. Criterios de Aceptacion (AC)

- **AC-1**: Given AWS CLI configurado con perfil correcto, When ejecuto
  `aws sts get-caller-identity --region us-east-1`, Then retorna el
  account ID esperado del owner del portfolio
- **AC-2**: Given KMS key creada, When ejecuto `aws kms describe-key
  --key-id alias/portfolio-lambdas --region us-east-1`, Then retorna
  KeyMetadata con `KeyState: Enabled` y `KeyUsage: ENCRYPT_DECRYPT`
- **AC-3**: Given los 4 SSM Parameters creados, When ejecuto `aws ssm
  describe-parameters --region us-east-1 --filters
  "Key=Name,Values=/portfolio"`, Then retorna 4 parameters
  (`/portfolio/turnstile-secret`, `/portfolio/neon-url`,
  `/portfolio/owner-email`, `/portfolio/ses-from-address`)
- **AC-4**: Given Turnstile widget creado, When abro Cloudflare dashboard
  Turnstile, Then el widget esta listado con los 6 hostnames del
  portfolio (the-full-stack.com + hub + fintech + architect + leader +
  vibe)
- **AC-5**: Given billing alarm creada en us-east-1, When ejecuto `aws
  cloudwatch describe-alarms --region us-east-1 --alarm-name-prefix
  portfolio-billing`, Then retorna 1 alarma con threshold $50

## 4. Diagrama de Flujo

N/A — el cambio NO altera flujos de control, es configuracion estatica.

## 5. Diagrama ER

N/A — no hay cambios en data model.

## 6. Tests Requeridos

### 6.A. TDD Flows

N/A (setup manual, no codigo nuevo).

### 6.B. Unit Tests

N/A (sin codigo Python en esta spec).

### 6.C. Typecheck

N/A.

### 6.D. E2E Tests

N/A.

### 6.E. Manual verification

- Ejecutar comandos de la seccion AC y validar outputs

## 7. Archivos Afectados

### Crear

- Ninguno (configuracion AWS/Cloudflare runtime)

### Modificar

- `serverless/env/.env.example` — agregar lista de SSM Parameters
  requeridos (template para developers)
  - Verificar: archivo existe y contiene los 4 nombres de parameter
- `serverless/docs/secrets.md` — inventario completo de SSM parameters,
  KMS key alias, rotation policy
  - Verificar: documento lista los 4 SSM parameters con descripcion

### Comandos a ejecutar (orden estricto)

```bash
# 1. Verificar AWS CLI
aws sts get-caller-identity --region us-east-1
# Verificar: AC-1

# 2. Crear KMS key
aws kms create-key \
  --description "Portfolio backend Lambdas SSM encryption" \
  --region us-east-1 \
  --tags TagKey=Project,TagValue=portfolio

# Anotar el KeyId del output, luego crear alias:
aws kms create-alias \
  --alias-name alias/portfolio-lambdas \
  --target-key-id <KEY_ID_DEL_OUTPUT> \
  --region us-east-1
# Verificar: AC-2

# 3. Crear SSM Parameters (placeholder values, se rotan despues)
# Usar `serverless setup-ssm` cuando este implementado.
# Mientras tanto, manual:
python devtools/run.py serverless setup-ssm \
  --name=/portfolio/turnstile-secret \
  --key-id=alias/portfolio-lambdas
# (pide value por stdin sin echo)

python devtools/run.py serverless setup-ssm \
  --name=/portfolio/owner-email \
  --value="pacg1991@gmail.com"

python devtools/run.py serverless setup-ssm \
  --name=/portfolio/ses-from-address \
  --value="no-reply@the-full-stack.com"

python devtools/run.py serverless setup-ssm \
  --name=/portfolio/neon-url \
  --key-id=alias/portfolio-lambdas
# (placeholder hasta SPEC-008, se rota despues)
# Verificar: AC-3

# 4. Crear Turnstile widget (manual en dashboard CF)
# Anotar sitekey publico y secret key (este ultimo va al SSM en paso 3)
# Configurar 6 hostnames en el widget
# Verificar: AC-4 manual en dashboard

# 5. AWS Billing Alarm en us-east-1
# Manual en consola Billing (gratis, primeras 10 alarmas) o via CLI:
aws cloudwatch put-metric-alarm \
  --alarm-name portfolio-billing-50usd \
  --alarm-description "Alert if AWS bill > 50 USD" \
  --metric-name EstimatedCharges \
  --namespace AWS/Billing \
  --statistic Maximum \
  --period 21600 \
  --threshold 50 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1 \
  --dimensions Name=Currency,Value=USD \
  --region us-east-1
# Verificar: AC-5
```

### Eliminar

- Nada.

## 8. Descomposicion para Paralelizacion

N/A — Small spec (2 archivos).

## 9. Validacion y Definition of Done

### Pre-implementacion

- [ ] AWS CLI configurado con perfil correcto
- [ ] Cloudflare account con acceso a Turnstile dashboard
- [ ] DNS del dominio the-full-stack.com en Cloudflare (verificar con
      `dig +short NS the-full-stack.com`)

### Definition of Done

- [ ] AC-1 a AC-5 cumplidos
- [ ] `serverless/env/.env.example` lista los 4 SSM Parameter paths
- [ ] `serverless/docs/secrets.md` documenta cada parameter (proposito,
      rotation policy, IAM access)
- [ ] AWS Billing Alarm responde a test (subir threshold a 0.01 USD
      temporalmente, esperar alert, restaurar 50)
- [ ] Turnstile sitekey publico disponible para el frontend (SPEC-012)
- [ ] Turnstile secret key cargado en SSM (verificable solo con
      `serverless rotate-secret` con valor de prueba)
