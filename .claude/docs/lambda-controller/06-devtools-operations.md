# 06 - Operacion con devtools

> Anterior: [05 - Crear y refactorizar](05-create-and-refactor.md) | [README](README.md)

Un lambda-controller se opera con el script `serverless` de devtools:
ejecutar en local, deployar a los entornos, invocar el Lambda deployado
y correr los tests. El comando resuelve el lambda objetivo via
`--lambda=<nombre>` (o `--path=<dir>`).

## El manifiesto `lambda.yaml`

Cada lambda-controller trae un `lambda.yaml` en su raiz: el manifiesto
**simple** que declara la configuracion. Es la unica fuente de verdad
versionada. devtools genera el `template.yaml` SAM a partir de el.

```yaml
# Obligatorios
name: payment-router                    # nombre logico (kebab-case)
runtime: python3.13                     # python3.12 | python3.13
handler: core.handler.lambda_handler    # el handler vive en core/

# Opcionales (con defaults)
memory: 256                             # MB    (default 256)
timeout: 30                             # seg   (default 30)
region: us-east-1                       # AWS region (default us-east-1)

layers: []                              # ARNs de layers compartidos
iam_policies: []                        # managed policies / SAM templates

# Env vars por stage: 'default' aplica a todos; el stage especifico
# sobrescribe las claves de 'default'.
environment:
  default:
    LOG_LEVEL: INFO
  prod:
    LOG_LEVEL: WARNING
```

## El template.yaml es efimero

devtools **genera** `template.yaml` desde `lambda.yaml` antes de cada
`run` / `deploy`. El `template.yaml` esta en `.gitignore` — NUNCA se
commitea ni se edita a mano. Esto elimina el drift: el dev cambia solo
el `lambda.yaml`.

```text
lambda.yaml  --(devtools sam-generate)-->  template.yaml  --(sam)-->  AWS
 (versionado, fuente de verdad)            (efimero, .gitignore)
```

Si necesitas ver el SAM que se va a usar:

```bash
python devtools/run.py serverless sam-generate --lambda=<nombre> --stage=dev
```

## Comandos

Los comandos de lambda-controller apuntan al lambda con `--lambda=<nombre>`
(forma recomendada): el nombre corto se resuelve contra
`serverless/lambda/services/<nombre>/` y devtools valida que la carpeta
cumpla la estructura lambda-controller (que exista y traiga `lambda.yaml`);
si no, lanza un error listando los lambdas validos. Como alternativa,
`--path=<dir>` apunta a un directorio explicito en cualquier ubicacion
(`--module` es alias de `--path`).

El CLI unifico la operacion en dos verbos: `run` (ejecutar el lambda, en
local o contra un stage deployado) y `tests` (correr la suite). Los viejos
`run-local` / `invoke-remote` / `test-unit` / `test-integration` ya NO
existen.

### Ejecutar el lambda: `run`

```bash
# --stage=local -> regenera el SAM y corre `sam local invoke`
python devtools/run.py serverless run \
  --stage=local --lambda=<nombre> --event=events/create.json

# --stage=dev|stage|prod -> `aws lambda invoke` contra el ya deployado
python devtools/run.py serverless run \
  --stage=dev --lambda=<nombre> --event=events/create.json --aws-profile=<perfil>
```

`run` SIEMPRE necesita `--stage` y `--lambda` (o `--path`). El `--stage`
decide el modo: `local` usa `sam local invoke` (requiere AWS SAM CLI);
`dev`/`stage`/`prod` usan `aws lambda invoke` contra la funcion ya
desplegada (requiere AWS CLI + credenciales). El `--event` es relativo a
la raiz del lambda.

### Deployar a un entorno

```bash
python devtools/run.py serverless deploy --lambda=<nombre> --stage=dev --aws-profile=<perfil>
python devtools/run.py serverless deploy --lambda=<nombre> --stage=stage --aws-profile=<perfil>
python devtools/run.py serverless deploy --lambda=<nombre> --stage=prod --aws-profile=<perfil>
```

Regenera el SAM para ese stage (selecciona su bloque de env vars), corre
`sam build --use-container` y `sam deploy`. El stack se llama
`<name>-<stage>`. `--dry-run` imprime las acciones sin ejecutar.

### Flag `--aws-profile` (perfil AWS CLI)

`deploy` y `run` contra un stage deployado ejecutan `aws`/`sam` por
debajo. Sin `--aws-profile`, usan el perfil del shell (`AWS_PROFILE` o
`[default]`), que puede apuntar a OTRA cuenta AWS o tener el token SSO
expirado — sintoma: `Error when retrieving token from sso` aunque hayas
hecho `aws sso login`. Pasar SIEMPRE `--aws-profile=<perfil>` para fijar
el perfil correcto. Alternativa: `export AWS_PROFILE=<perfil>` en la
sesion de trabajo. El nombre del perfil es especifico del backend (en el
portfolio: `tfs-dev`).

### Tests: `tests --type`

```bash
python devtools/run.py serverless tests --type=unit --lambda=<nombre>
python devtools/run.py serverless tests --type=integration --lambda=<nombre>
python devtools/run.py serverless tests --type=coverage --lambda=<nombre>
```

`tests` SIEMPRE necesita `--type` (`unit` | `integration` | `coverage`).
`--type=unit` corre `pytest tests/unit`, `--type=integration` corre
`pytest tests/integration` y `--type=coverage` agrega el reporte de
cobertura; todos con cwd en la raiz del lambda. Sin target
(`--lambda`/`--path`/`--shared`), `tests` corre la suite completa: los 4
lambdas + la libreria comun. Con `--shared` corre solo la suite de
`serverless/lambda/shared/`.

## Ciclo de trabajo tipico

```bash
# 1. Desarrollar + tests
python devtools/run.py serverless tests --type=unit --lambda=<nombre>

# 2. Probar en local
python devtools/run.py serverless run \
  --stage=local --lambda=<nombre> --event=events/create.json

# 3. Deployar a dev y verificar
python devtools/run.py serverless deploy --lambda=<nombre> --stage=dev --aws-profile=tfs-dev
python devtools/run.py serverless run \
  --stage=dev --lambda=<nombre> --event=events/create.json --aws-profile=tfs-dev

# 4. Promover a stage y prod
python devtools/run.py serverless deploy --lambda=<nombre> --stage=stage --aws-profile=tfs-dev
python devtools/run.py serverless deploy --lambda=<nombre> --stage=prod --aws-profile=tfs-dev
```

---

[README](README.md) | Anterior: [05](05-create-and-refactor.md)
