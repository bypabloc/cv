# Catalogo de secretos / parametros SSM

Cada archivo `<short-name>.yaml` declara un parametro de SSM Parameter
Store del backend serverless. devtools usa este catalogo como UNICA
fuente de verdad — los antiguos diccionarios hardcodeados (`_SECRETS`
en `provisioner.py`, `_SSM_PARAMETERS` en `secrets.py`) ya no existen.

## Schema

```yaml
kind: ssm-parameter

name: <short-name>          # debe coincidir con el filename stem
description: <una linea>
path: /portfolio/${stage}/<short-name>   # ${stage} interpolado por devtools
                                          # path sin ${stage} == global
ssm_type: SecureString | String
kms_key_alias: alias/portfolio-lambdas    # solo si SecureString
                                           # default: alias/portfolio-lambdas

# Mapeo .env -> Lambda
source_env_var: <KEY_EN_EL_.ENV>          # KEY en docker/env/server/.{stage}
target_env_var: <KEY_EN_EL_LAMBDA>        # env var del Lambda

stages: [dev, stage, prod]                 # subset de [dev, stage, prod]
                                            # NUNCA incluir 'local'
required: true                             # bool

# Bloques opcionales
rotation: { interval_days: 90 }
owners: [pacg1991@gmail.com]
consumed_by: [contact_form]
tags: { Project: portfolio, ManagedBy: devtools }
```

## Como agregar un secreto

1. Crear `<short-name>.yaml` siguiendo el ejemplo de
   `turnstile-secret.yaml`.
2. Agregar la KEY a `docker/env/server/.example` (sin valor).
3. Agregar el valor real a `docker/env/server/.{dev,stage,prod}`
   (gitignored).
4. Listar `<short-name>` en `uses.secrets` del `manifest.yaml` del
   Lambda consumer.
5. En el codigo del Lambda usar
   `from shared.aws.ssm import get_secret` y `value = get_secret('<short-name>')`.
6. Deploy: `python devtools/run.py serverless deploy --stage=dev --lambda=<X>
   --aws-profile=tfs-dev`. El sync se ejecuta automaticamente.

## Como rotar un secreto

```bash
# Despues de actualizar docker/env/server/.{stage}
python devtools/run.py serverless sync-secrets --stage=dev --aws-profile=tfs-dev
```

## Inventario actual

| Archivo | Path SSM | Tipo | Stages | Required |
|---------|----------|------|--------|----------|
| `turnstile-secret.yaml` | `/portfolio/${stage}/turnstile-secret` | SecureString | dev,stage,prod | true |
| `turnstile-bypass-secret.yaml` | `/portfolio/dev/turnstile-bypass-secret` | SecureString | dev | false |
| `neon-url.yaml` | `/portfolio/${stage}/neon-url` | SecureString | dev,stage,prod | true |
| `owner-email.yaml` | `/portfolio/owner-email` | String | dev,stage,prod | true |
| `ses-from-address.yaml` | `/portfolio/ses-from-address` | String | dev,stage,prod | true |
| `ses-from-name.yaml` | `/portfolio/ses-from-name` | String | dev,stage,prod | false |

Comando rapido para auditar:

```bash
python -c "
from serverless.secrets_catalog import Catalog
for s in sorted(Catalog.load().by_name.values(), key=lambda x: x.name):
    print(f'{s.name:<25} {s.ssm_type:<13} stages={sorted(s.stages)}')
"
```
