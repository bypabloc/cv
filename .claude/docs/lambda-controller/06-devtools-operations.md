# 06 - Operacion con devtools

> Anterior: [05 - Crear y refactorizar](05-create-and-refactor.md) | [README](README.md)

Un lambda-controller se opera con el script `serverless` de devtools:
ejecutar en local, deployar a los entornos, invocar el Lambda deployado
y correr los tests. El comando resuelve el lambda objetivo via `--path`.

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
`run-local` / `deploy`. El `template.yaml` esta en `.gitignore` — NUNCA
se commitea ni se edita a mano. Esto elimina el drift: el dev cambia
solo el `lambda.yaml`.

```text
lambda.yaml  --(devtools sam-generate)-->  template.yaml  --(sam)-->  AWS
 (versionado, fuente de verdad)            (efimero, .gitignore)
```

Si necesitas ver el SAM que se va a usar:

```bash
python devtools/run.py serverless sam-generate --path=<dir> --stage=dev
```

## Comandos

Todos los comandos de lambda-controller requieren `--path=<dir>` (el
directorio raiz del lambda, el que contiene `lambda.yaml`). `--module`
es alias de `--path`.

### Ejecutar en local

```bash
python devtools/run.py serverless run-local \
  --path=<dir> --event=events/create.json
```

Regenera el SAM y corre `sam local invoke` con el event JSON indicado.
Requiere AWS SAM CLI instalado. El `--event` es relativo a la raiz del
lambda.

### Deployar a un entorno

```bash
python devtools/run.py serverless deploy --path=<dir> --stage=dev
python devtools/run.py serverless deploy --path=<dir> --stage=stage
python devtools/run.py serverless deploy --path=<dir> --stage=prod
```

Regenera el SAM para ese stage (selecciona su bloque de env vars), corre
`sam build --use-container` y `sam deploy`. El stack se llama
`<name>-<stage>`. `--dry-run` imprime las acciones sin ejecutar.

### Invocar el Lambda ya deployado

```bash
python devtools/run.py serverless invoke-remote \
  --path=<dir> --stage=dev --event=events/create.json
```

Invoca via `aws lambda invoke` la funcion `<name>-<stage>` ya desplegada
e imprime el payload de respuesta. Requiere AWS CLI + credenciales.

### Tests

```bash
python devtools/run.py serverless test-unit --path=<dir>
python devtools/run.py serverless test-integration --path=<dir>
```

`test-unit` corre `pytest tests/unit` y `test-integration` corre
`pytest tests/integration`, ambos con cwd en la raiz del lambda. Sin
`--path`, estos comandos operan sobre el backend SAM del portfolio
(modo legacy).

## Ciclo de trabajo tipico

```bash
# 1. Desarrollar + tests
python devtools/run.py serverless test-unit --path=<dir>

# 2. Probar en local
python devtools/run.py serverless run-local \
  --path=<dir> --event=events/create.json

# 3. Deployar a dev y verificar
python devtools/run.py serverless deploy --path=<dir> --stage=dev
python devtools/run.py serverless invoke-remote \
  --path=<dir> --stage=dev --event=events/create.json

# 4. Promover a stage y prod
python devtools/run.py serverless deploy --path=<dir> --stage=stage
python devtools/run.py serverless deploy --path=<dir> --stage=prod
```

## Modo legacy vs lambda-controller

El script `serverless` opera en dos modos segun la presencia de `--path`:

| Sin `--path` | Con `--path=<dir>` |
|--------------|--------------------|
| Backend SAM del portfolio (`serverless/`) | lambda-controller en `<dir>` |
| `template.yaml` escrito a mano | `template.yaml` generado de `lambda.yaml` |
| 3 funciones fijas | cualquier lambda con `lambda.yaml` |

Los comandos `sam-generate`, `run-local`, `invoke-remote` SOLO existen
en modo lambda-controller (exigen `--path`). `deploy`, `test-unit`,
`test-integration` funcionan en ambos modos.

---

[README](README.md) | Anterior: [05](05-create-and-refactor.md)
