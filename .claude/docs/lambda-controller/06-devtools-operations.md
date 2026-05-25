# 06 - Operacion con devtools

> Anterior: [05 - Crear y refactorizar](05-create-and-refactor.md) | [README](README.md)

Un lambda-controller se opera con el script `serverless` de devtools:
ejecutar en local, deployar a los entornos, invocar el Lambda deployado,
ver su estado, destruirlo y correr los tests. devtools provisiona cada
recurso AWS con AWS CLI imperativo (sin capas de IaC declarativa) y
mantiene un archivo de estado local por `(scope, stage)`. El comando
resuelve el lambda objetivo via `--lambda=<nombre>` (o `--path=<dir>`).

## El manifiesto `manifest.yaml`

Cada lambda-controller trae un `manifest.yaml` en su raiz: el manifiesto
**simple** que declara la configuracion. Es la unica fuente de verdad
versionada. devtools lo lee directamente — `provisioner.py` lo traduce a
una secuencia de llamadas AWS CLI (rol IAM, LogGroup, funcion, wiring del
trigger). NO hay paso intermedio ni archivo de config generado.

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
iam_policies: []                        # managed policies adicionales

# Env vars por stage: 'default' aplica a todos; el stage especifico
# sobrescribe las claves de 'default'.
environment:
  default:
    LOG_LEVEL: INFO
  prod:
    LOG_LEVEL: WARNING
```

## Como devtools provisiona el Lambda

`provisioner.py` lee el `manifest.yaml` y emite las llamadas AWS CLI que
crean/actualizan el Lambda y su wiring: `aws iam create-role` +
`put-role-policy`, `aws logs create-log-group` + `put-retention-policy`,
`aws lambda create-function`, y segun el `trigger` las llamadas de
`apigateway` (rutas HTTP) o `aws lambda create-event-source-mapping`
(triggers de tabla).

`packaging.py` arma el artefacto `build.zip` con uv (deps + `core/` +
vendoring selectivo de `shared/`). El `build/` y el `build.zip` son
efimeros (`.gitignore`); se regeneran en cada `deploy`.

## El archivo de estado local

devtools mantiene un JSON por `(scope, stage)` en
`serverless/lambda/.state/<scope>-<stage>.json` (gitignored). Registra
los ARNs de lo creado y dos hashes: `config_hash` (config aplicada) y
`code_hash` (contenido de `core/`). El diff de esos hashes decide la
accion del `deploy`:

```text
config_hash y code_hash coinciden con disco  -> noop
solo cambio code_hash                        -> update-function-code
cambio config_hash                           -> update-function-configuration (+ IAM)
no hay estado previo                          -> create (secuencia completa)
```

Esto hace el `deploy` idempotente y re-ejecutable. Esquema completo:
[.claude/docs/serverless-backend/05-estado-local.md](../serverless-backend/05-estado-local.md).

## Comandos

Los comandos de lambda-controller apuntan al lambda con `--lambda=<nombre>`
(forma recomendada): el nombre corto se resuelve contra
`serverless/lambda/services/<nombre>/` y devtools valida que la carpeta
cumpla la estructura lambda-controller (que exista y traiga `manifest.yaml`);
si no, lanza un error listando los lambdas validos. Como alternativa,
`--path=<dir>` apunta a un directorio explicito en cualquier ubicacion
(`--module` es alias de `--path`).

Los verbos: `run` (ejecutar el lambda, en local o contra un stage
deployado), `deploy` (provisionar), `destroy` (eliminar), `status`
(estado local vs AWS) y `tests` (correr la suite).

### Ejecutar el lambda: `run`

```bash
# --stage=local -> ejecuta el lambda en local. Por defecto usa el
#   Runtime Interface Emulator (RIE) en un contenedor Docker; con
#   --runtime-mode=direct corre el handler en proceso (sin Docker).
python devtools/run.py serverless run \
  --stage=local --lambda=<nombre> --event=events/create.json
python devtools/run.py serverless run \
  --stage=local --lambda=<nombre> --event=events/create.json --runtime-mode=direct

# --stage=dev|stage|prod -> `aws lambda invoke` contra el ya deployado
python devtools/run.py serverless run \
  --stage=dev --lambda=<nombre> --event=events/create.json --aws-profile=<perfil>
```

`run` SIEMPRE necesita `--stage` y `--lambda` (o `--path`). El `--stage`
decide el modo: `local` corre el Lambda en local (RIE via Docker, o
modo directo con `--runtime-mode=direct`); `dev`/`stage`/`prod` usan
`aws lambda invoke` contra la funcion ya deployada (requiere AWS CLI +
credenciales). El `--event` es relativo a la raiz del lambda.

### Deployar a un entorno

```bash
python devtools/run.py serverless deploy --lambda=<nombre> --stage=dev --aws-profile=<perfil>
python devtools/run.py serverless deploy --lambda=<nombre> --stage=stage --aws-profile=<perfil>
python devtools/run.py serverless deploy --lambda=<nombre> --stage=prod --aws-profile=<perfil>
```

`deploy` arma el `build.zip` con uv + vendoring selectivo de `shared/`,
lee el `manifest.yaml`, carga el estado previo, calcula el diff de
hashes y aplica la accion correspondiente (`create` / `update-code` /
`update-config` / `noop`) con AWS CLI. Al terminar guarda el estado en
`.state/<nombre>-<stage>.json`. `--dry-run` imprime las acciones sin
ejecutarlas.

### Ver el estado: `status`

```bash
python devtools/run.py serverless status --lambda=<nombre> --stage=dev --aws-profile=<perfil>
```

Compara el estado local (`.state/<nombre>-<stage>.json`) contra los
`describe-*` reales de AWS. Sirve para detectar drift: si alguien cambio
un recurso a mano en la consola, `status` lo muestra.

### Destruir: `destroy`

```bash
python devtools/run.py serverless destroy --lambda=<nombre> --stage=dev --yes --aws-profile=<perfil>
```

Borra los recursos del lambda en ese stage en orden inverso al de
creacion (event source mapping, permisos, metodos de API, funcion, rol,
LogGroup) y limpia el archivo de estado. Requiere `--yes` por ser
destructivo.

### Flag `--aws-profile` (perfil AWS CLI)

`deploy`, `destroy`, `status` y `run` contra un stage deployado ejecutan
`aws` por debajo. Sin `--aws-profile`, usan el perfil del shell
(`AWS_PROFILE` o `[default]`), que puede apuntar a OTRA cuenta AWS o
tener el token SSO expirado — sintoma: `Error when retrieving token from
sso` aunque hayas hecho `aws sso login`. Pasar SIEMPRE
`--aws-profile=<perfil>` para fijar el perfil correcto. Alternativa:
`export AWS_PROFILE=<perfil>` en la sesion de trabajo. El nombre del
perfil es especifico del backend (en el portfolio: `tfs-dev`).

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
