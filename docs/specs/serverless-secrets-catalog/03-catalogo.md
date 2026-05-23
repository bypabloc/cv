# Fase 2 — Catálogo migrado (6 archivos YAML)

> Crea los 6 archivos del catálogo en `serverless/lambda/resources/secrets/`
> con el mapeo exacto del estado actual (parity con `_SECRETS` +
> `_SSM_PARAMETERS` antes de eliminarlos).

## Inventario completo del catálogo

| Archivo | Path SSM | ssm_type | source_env_var | target_env_var | stages | required |
|---------|----------|----------|----------------|----------------|--------|----------|
| `turnstile-secret.yaml` | `/portfolio/${stage}/turnstile-secret` | SecureString | `TURNSTILE_SECRET_KEY` | `SSM_TURNSTILE_SECRET_PATH` | dev,stage,prod | true |
| `turnstile-bypass-secret.yaml` | `/portfolio/dev/turnstile-bypass-secret` | SecureString | `TURNSTILE_BYPASS_SECRET` | `SSM_TURNSTILE_BYPASS_PATH` | dev | false |
| `neon-url.yaml` | `/portfolio/${stage}/neon-url` | SecureString | `DB_URL` | `SSM_NEON_URL_PATH` | dev,stage,prod | true |
| `owner-email.yaml` | `/portfolio/owner-email` | String | `OWNER_EMAIL` | `SSM_OWNER_EMAIL_PATH` | dev,stage,prod | true |
| `ses-from-address.yaml` | `/portfolio/ses-from-address` | String | `EMAIL_FROM` | `SSM_SES_FROM_PATH` | dev,stage,prod | true |
| `ses-from-name.yaml` *(nuevo)* | `/portfolio/ses-from-name` | String | `EMAIL_FROM_NAME` | `SSM_SES_FROM_NAME_PATH` | dev,stage,prod | false |

### Notas sobre el inventario

- `turnstile-bypass-secret` solo existe en `dev` (su uso es bypass para
  E2E; jamás debe propagarse a stage/prod).
- `owner-email` y `ses-from-address` son `String` (no sensibles) y NO
  llevan stage en el path: un único parámetro global para los 3 stages.
  Esto refleja el estado actual del código (línea 97-103 en `provisioner.py`).
- `ses-from-name` es NUEVO en el catálogo. Hoy vive solo como env var
  inline (`EMAIL_FROM_NAME=The Full Stack` en el `.env`). Lo incluyo
  porque el requerimiento del usuario es "todas las server/.{env} a SSM".
- `neon-url` tiene UN solo archivo YAML pero genera 3 paths SSM (dev/stage/prod)
  por la interpolación de `${stage}`.

### Variables del `.env` que NO van al catálogo

Estas vars de `server/.{env}` siguen siendo derivables y se quedan inline
en `manifest.yaml` de cada Lambda (decisión del usuario en tanda 1 = "todo a
SSM" se interpreta como "todos los SECRETOS/CONFIG NO DERIVABLE"). Si el
usuario quiere realmente TODAS (incluso constantes triviales), agregar:

- `AWS_REGION`, `AWS_SES_REGION`, `AWS_S3_REGION_NAME` — constantes
  (`us-east-1`) iguales en todos los stages. No vale la pena un SSM lookup.
- `KMS_KEY_ALIAS` — constante (`alias/portfolio-lambdas`).
- `SSM_PATH_PREFIX` — constante (`/portfolio`). Es el prefijo del catálogo.
- `EMAIL_BACKEND` — constante de runtime (`ses`).
- `AWS_STORAGE_BUCKET_NAME` — varía por stage (`the-full-stack-dev` vs
  `the-full-stack`). Podría ser un SSM String por stage. Marcar como TODO.
- `DB_DB`, `DB_USER`, `DB_PORT`, `DB_SSLMODE`, `DB_CHANNEL_BINDING`,
  `DB_HOST`, `DB_PASSWORD` — son parte del `DB_URL` ya embebido en
  `neon-url`. La Lambda solo necesita `DB_URL`. Las dejo fuera del catálogo
  para no duplicar.

**Decisión a confirmar con el usuario en revisión del plan**: aceptar
este recorte o si literalmente quiere TODAS las variables del `.env` a SSM
(incluyendo `AWS_REGION` etc. como SSM String). La opción literal infla SSM
sin valor y agrega 14 GetParameter por cold start.

## Ejemplo completo: `turnstile-secret.yaml`

```yaml
# serverless/lambda/resources/secrets/turnstile-secret.yaml
# Esquema devtools — NO CloudFormation: esquema plano, sin funciones
# intrinsecas. devtools lo lee y emite las llamadas AWS CLI necesarias.
kind: ssm-parameter

name: turnstile-secret
description: Cloudflare Turnstile secret key (siteverify) — Portfolio Backend

path: /portfolio/${stage}/turnstile-secret
ssm_type: SecureString
kms_key_alias: alias/portfolio-lambdas

source_env_var: TURNSTILE_SECRET_KEY
target_env_var: SSM_TURNSTILE_SECRET_PATH

stages: [dev, stage, prod]
required: true

rotation:
  interval_days: 90
  last_rotated: 2026-05-22

owners:
  - pacg1991@gmail.com

consumed_by:
  - contact_form

tags:
  Project: portfolio
  ManagedBy: devtools
```

## Archivos afectados

### Crear

- `serverless/lambda/resources/secrets/turnstile-secret.yaml`
  - Verificar: `Catalog.load().get('turnstile-secret').path_for('dev') == '/portfolio/dev/turnstile-secret'`
- `serverless/lambda/resources/secrets/turnstile-bypass-secret.yaml`
  - Verificar: `Catalog.load().get('turnstile-bypass-secret').stages == frozenset({'dev'})`
- `serverless/lambda/resources/secrets/neon-url.yaml`
  - Verificar: path interpolado en 3 stages
- `serverless/lambda/resources/secrets/owner-email.yaml`
  - Verificar: ssm_type=String, sin ${stage} (path global)
- `serverless/lambda/resources/secrets/ses-from-address.yaml`
  - Verificar: idem owner-email
- `serverless/lambda/resources/secrets/ses-from-name.yaml`
  - Verificar: idem

### Modificar

- `serverless/lambda/resources/README.md` *(crear si no existe)* —
  documenta el tipo `ssm-parameter` y el patrón del catálogo
  - Verificar: lectura visual

## Verify-before-done

```bash
# El parser carga los 6 archivos sin error
python -c "
from devtools.serverless.secrets_catalog import Catalog
c = Catalog.load()
assert sorted(c.by_name) == ['neon-url', 'owner-email', 'ses-from-address',
                              'ses-from-name', 'turnstile-bypass-secret',
                              'turnstile-secret']
print('OK 6 secretos cargados')
"

# Test de parity con el _SECRETS hardcodeado (snapshot)
pytest devtools/tests/serverless/test_secrets_catalog_parity.py -v
```
