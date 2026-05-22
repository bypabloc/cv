# 04 — Fase 2: `provisioner.py` (lambda.yaml -> AWS CLI)

> [Anterior: 03](03-fase-1-capa-base.md) | [README](README.md) | [Siguiente: 05](05-fase-3-provisioner-infra.md)

Reemplazo de `sam_generate.py`. Traduce el `lambda.yaml` de un Lambda a
una secuencia de llamadas AWS CLI: rol IAM, LogGroup, funcion, wiring del
trigger. Depende de Fase 1 (`aws_cli.py` + `state.py`).

## Objetivo

`sam_generate.py` hoy convierte `lambda.yaml` a un `template.yaml` con
`Transform: AWS::Serverless`. `provisioner.py` hace dos cosas en su
lugar:

1. **`render(manifest, stage)`** — funcion PURA que produce un
   `RenderedLambda`: el documento de politica IAM, la config de la
   funcion (memory, timeout, env, runtime, architecture) y la
   descripcion del wiring del trigger. Sin tocar AWS. Es lo testeable.
2. **`provision(rendered, action, ...)`** — ejecuta las llamadas AWS CLI
   segun la `Action` que decidio `state.diff`.

La logica de traduccion de `uses` -> IAM ya existe y es correcta en
[sam_generate.py:231-376](../../../devtools/serverless/sam_generate.py#L231-L376)
(`_build_policies`). Se PORTA casi tal cual a `provisioner.py`: lo unico
que cambia es que los ARNs se resuelven a strings concretos (no
`Fn::Sub` ni `Fn::ImportValue`).

## Sub-tarea: rename `lambda.yaml` -> `manifest.yaml`

Como parte de esta fase se renombra el manifiesto de cada Lambda:

```text
serverless/lambda/services/{service}/lambda.yaml
  -> serverless/lambda/services/{service}/manifest.yaml
```

### Por que el rename

`lambda.yaml` es redundante: el archivo vive dentro de
`serverless/lambda/services/<x>/` — ya se sabe que es un Lambda. El
nombre no dice QUE es el archivo. `manifest.yaml` nombra lo que ES: un
manifiesto declarativo de la configuracion del servicio (runtime,
trigger, recursos que usa, env vars). Es el termino estandar en
IaC / contenedores, y es agnostico a si el deploy usa SAM o AWS CLI —
sobrevive a esta migracion.

### Alcance del rename

El rename toca tres grupos de archivos:

1. **Los 4 manifiestos** — `git mv` de cada uno:
   - `serverless/lambda/services/contact_form/lambda.yaml` -> `manifest.yaml`
   - `serverless/lambda/services/tracking_pixel/lambda.yaml` -> `manifest.yaml`
   - `serverless/lambda/services/stream_processor/lambda.yaml` -> `manifest.yaml`
   - `serverless/lambda/services/db/lambda.yaml` -> `manifest.yaml`

2. **El codigo de devtools que busca el archivo por nombre** — 8
   modulos lo referencian (`rg 'lambda\.yaml' devtools/serverless/`):
   `resolve.py` (resuelve el lambda buscando el manifiesto),
   `shared_resolver.py`, `vendoring.py`, `lifecycle.py`,
   `lambda_controller.py`, `packaging.py`, `flags.py`, y
   `sam_generate.py` (este ultimo se elimina en la Fase 6, no se toca).
   El cambio es mecanico: la constante con el nombre del archivo pasa de
   `'lambda.yaml'` a `'manifest.yaml'`. Idealmente se centraliza en UNA
   constante en `resolve.py` (`MANIFEST_FILENAME = 'manifest.yaml'`) y
   los demas modulos la importan, para que no quede el string repetido.

3. **El scaffold** — `.claude/templates/lambda-controller/lambda.yaml`
   se renombra a `manifest.yaml` (el template desde el que se crea un
   Lambda nuevo).

> Las menciones en `.claude/rules/`, `.claude/docs/` y la skill se
> actualizan en la Fase 7 (docs), junto con el resto de la
> documentacion. Aqui solo se renombran los archivos y se ajusta el
> codigo que los lee.

### Verificacion del rename

```bash
# No queda ningun lambda.yaml en services/
rg --files serverless/lambda/services/ | rg 'lambda\.yaml$'   # 0 resultados
# Existen los 4 manifest.yaml
rg --files serverless/lambda/services/ | rg 'manifest\.yaml$' # 4 resultados
# devtools no busca ya 'lambda.yaml'
rg "'lambda\.yaml'|\"lambda\.yaml\"" devtools/serverless/      # 0 (salvo sam_generate, que se borra en Fase 6)
```

## Archivos afectados

### Crear

- `devtools/serverless/provisioner.py` — render + provision del Lambda.
- `devtools/tests/unit/src/serverless/test_provisioner_render.py` — tests del render.
- `devtools/tests/unit/src/serverless/test_provisioner_provision.py` — tests de la
  secuencia de llamadas (AWS CLI mockeado).

### Renombrar (`git mv`)

- `serverless/lambda/services/contact_form/lambda.yaml` -> `manifest.yaml`
- `serverless/lambda/services/tracking_pixel/lambda.yaml` -> `manifest.yaml`
- `serverless/lambda/services/stream_processor/lambda.yaml` -> `manifest.yaml`
- `serverless/lambda/services/db/lambda.yaml` -> `manifest.yaml`
- `.claude/templates/lambda-controller/lambda.yaml` -> `manifest.yaml`

### Modificar

- `devtools/serverless/packaging.py` — `package_lambda` /
  `packaged_lambda` producen un `build.zip` (archivo) ademas del
  `build/` (directorio). `aws lambda update-function-code --zip-file`
  necesita un archivo zip; `create-function` tambien (o un S3 key).
  Anadir `zip_build_dir()`. Ademas: usa `'lambda.yaml'` -> usar la
  constante `MANIFEST_FILENAME` (ver sub-tarea del rename).
- `devtools/serverless/resolve.py` — define la constante
  `MANIFEST_FILENAME = 'manifest.yaml'` y la usa para localizar el
  manifiesto del Lambda (hoy busca `'lambda.yaml'`).
- `devtools/serverless/shared_resolver.py` — referencia `'lambda.yaml'`;
  importar `MANIFEST_FILENAME` de `resolve.py`.
- `devtools/serverless/vendoring.py` — idem.
- `devtools/serverless/lifecycle.py` — idem.
- `devtools/serverless/lambda_controller.py` — idem (este modulo se
  reescribe a fondo en la Fase 5; aqui solo el nombre del manifiesto).
- `devtools/serverless/flags.py` — referencias a `'lambda.yaml'` en
  textos de ayuda / validacion; usar el nombre nuevo.

> `sam_generate.py` tambien referencia `lambda.yaml` pero NO se toca: se
> elimina entero en la Fase 6.

## Diferencias clave vs `sam_generate.py`

| Aspecto | `sam_generate.py` (SAM) | `provisioner.py` (AWS CLI) |
|---------|-------------------------|----------------------------|
| ARN de cuenta | `${AWS::AccountId}` (resuelto por CFN) | `aws sts get-caller-identity` una vez, cacheado |
| ARN de region | `${AWS::Region}` | string fijo de `manifest.yaml` (`us-east-1`) |
| Recurso de infra (tabla, API) | `Fn::ImportValue` del Output del stack | `aws ssm get-parameter` del path que publico `infra_provision` |
| Rol IAM | implicito en `AWS::Serverless::Function` | explicito: `create-role` + `put-role-policy` |
| LogGroup | implicito (CFN lo crea con retencion default `Never`) | explicito: `create-log-group` + `put-retention-policy 7` |
| Trigger http | `AWS::ApiGateway::Resource/Method/...` | `aws apigateway put-method` / `put-integration` / `create-deployment` + `aws lambda add-permission` |
| Trigger on-table-changes | `Events: { Type: DynamoDB }` | `aws lambda create-event-source-mapping` |

> Nota: la infra (tablas, API) ya NO publica Outputs CloudFormation con
> Export; publica SSM Parameters (decidido en `serverless-restructure`
> commit 3 — ver `resources/dynamodb/contacts.yaml` actual). `provisioner`
> lee esos SSM. Si `serverless-restructure` no esta mergeado, esta fase
> asume el esquema SSM como contrato; ver
> [11-paralelizacion-worktrees.md](11-paralelizacion-worktrees.md).

## API publica de `provisioner.py`

```python
@dataclass(frozen=True)
class RenderedLambda:
    name: str                       # contact-form
    function_name: str              # portfolio-contact-form-dev
    runtime: str
    architecture: str
    handler: str
    memory: int
    timeout: int
    env_vars: dict[str, str]
    iam_policy: dict                 # documento de politica IAM
    trigger: TriggerSpec             # direct | http | on-table-changes
    role_name: str

def render(manifest: dict, *, stage: str) -> RenderedLambda:
    """Funcion pura: manifest.yaml -> RenderedLambda. Sin tocar AWS."""

def provision(
    rendered: RenderedLambda,
    *,
    action: Action,
    zip_path: Path,
    previous: LambdaState | None,
    profile: str | None,
    region: str,
) -> LambdaState:
    """Ejecuta las llamadas AWS CLI segun `action`. Devuelve el estado nuevo."""

def deprovision(
    state: LambdaState, *, profile: str | None, region: str
) -> None:
    """Borra los recursos del Lambda en orden inverso al de creacion."""
```

## Secuencia de creacion (`Action.CREATE`)

Orden FIJO (reemplaza el grafo de dependencias de CloudFormation):

```text
1. aws iam create-role            --role-name portfolio-<name>-<stage>
                                  --assume-role-policy-document <lambda trust>
2. aws iam put-role-policy        --role-name ... --policy-name inline
                                  --policy-document <iam_policy renderizado>
3. aws iam attach-role-policy     (AWSLambdaBasicExecutionRole, para logs)
4. aws logs create-log-group      --log-group-name /aws/lambda/portfolio-<name>-<stage>
5. aws logs put-retention-policy  --retention-in-days 7
6. (espera de propagacion IAM ~10s — el rol recien creado puede no estar
    disponible para create-function; reintentar con backoff)
7. aws lambda create-function     --function-name ... --runtime ...
                                  --role <role_arn> --handler ...
                                  --zip-file fileb://build.zip
                                  --memory-size ... --timeout ...
                                  --architectures ... --environment ...
                                  --tracing-config Mode=Active
8. [trigger == http]
     aws apigateway create-resource   (path part, parent = root de SSM)
     aws apigateway put-method        --http-method POST --authorization-type NONE
     aws apigateway put-integration   --type AWS_PROXY --integration-http-method POST
                                      --uri <lambda invoke arn>
     aws apigateway create-deployment --stage-name <stage>
     aws lambda add-permission        --principal apigateway.amazonaws.com
                                      --source-arn <execute-api arn>
   [trigger == on-table-changes]
     aws lambda create-event-source-mapping
       --event-source-arn <stream arn de SSM> --batch-size 100
       --maximum-batching-window-in-seconds 10
       --function-response-types ReportBatchItemFailures
       (uno por tabla)
   [trigger == direct]
     (nada)
```

Cada paso registra su identificador en `LambdaState.resources` ANTES de
pasar al siguiente. Asi, si el paso 7 falla, el estado ya tiene
`role_arn` y `log_group` y el comando es re-ejecutable (AC-2.8).

## Secuencia de update

- `UPDATE_CODE`: `aws lambda update-function-code --zip-file fileb://build.zip`.
- `UPDATE_CONFIG`: `aws lambda update-function-configuration` (memory,
  timeout, env, handler, runtime) + `aws iam put-role-policy` (re-aplica
  el inline policy, idempotente).
- `UPDATE_BOTH`: ambas.
- El wiring del trigger (API method, event source mapping) se reconcilia
  solo si cambio: `provisioner` compara el `trigger` renderizado vs el
  guardado en `state.resources`.

## Secuencia de borrado (`deprovision`)

Orden INVERSO:

```text
1. [http]              aws lambda remove-permission
                       aws apigateway delete-method / delete-resource
   [on-table-changes]  aws lambda delete-event-source-mapping (por UUID)
2. aws lambda delete-function
3. aws iam delete-role-policy + aws iam detach-role-policy
4. aws iam delete-role
5. aws logs delete-log-group
```

## Criterios de aceptacion

- **AC-2.1**: Given un `manifest.yaml` con `uses.tables`, When `render`,
  Then `iam_policy` tiene un Statement DynamoDB por tabla con las
  acciones del nivel de acceso (read / write / read-write).
- **AC-2.2**: Given `uses.secrets`, When `render`, Then `iam_policy`
  tiene un Statement `ssm:GetParameter` con los ARNs y un Statement
  `kms:Decrypt`.
- **AC-2.3**: Given `uses.sends-email: true`, When `render`, Then hay un
  Statement `ses:SendEmail` sobre las identidades verificadas.
- **AC-2.4**: Given `trigger.type: on-table-changes`, When `render`,
  Then el IAM tiene los permisos de Stream + SQS al DLQ.
- **AC-2.5**: Given un Lambda sin estado previo, When `provision` con
  `Action.CREATE`, Then las llamadas AWS CLI ocurren en el orden:
  create-role, put-role-policy, create-log-group, create-function,
  wiring.
- **AC-2.6**: Given un Lambda desplegado, When `Action.UPDATE_CODE`,
  Then solo se llama `update-function-code` (ni create-role ni
  create-function).
- **AC-2.7**: Given un Lambda desplegado, When `Action.UPDATE_CONFIG`,
  Then se llama `update-function-configuration` y `put-role-policy`,
  nunca `create-function`.
- **AC-2.8**: Given un `provision` que falla en `create-function`, When
  termina, Then el `LambdaState` devuelto registra `role_arn` y
  `log_group` ya creados (re-ejecucion idempotente).
- **AC-2.9**: Given un `LambdaState`, When `deprovision`, Then las
  llamadas de borrado ocurren en orden inverso al de creacion.
- **AC-2.10**: Given `render` sobre el mismo `manifest.yaml` y `stage`
  dos veces, Then el `RenderedLambda` es identico (funcion pura).
- **AC-2.11**: When se buscan archivos `lambda.yaml` en
  `serverless/lambda/services/`, Then no hay ninguno; los 4 servicios
  tienen `manifest.yaml`.
- **AC-2.12**: Given los 4 servicios con `manifest.yaml`, When
  `resolve_lambda` resuelve cualquiera de ellos, Then lo encuentra por
  la constante `MANIFEST_FILENAME` (no por el nombre viejo).

## Tests requeridos

`test_provisioner_render.py` — sin AWS, funcion pura, fixtures de
`manifest.yaml` por trigger:

- `test_render_iam_policy_when_uses_tables` [AC-2.1]
- `test_render_iam_policy_when_uses_secrets` [AC-2.2]
- `test_render_iam_policy_when_sends_email` [AC-2.3]
- `test_render_iam_policy_when_on_table_changes` [AC-2.4]
- `test_render_is_pure_same_input_same_output` [AC-2.10]
- `test_render_function_config_applies_defaults` (memory/timeout default)

`resolve.py` (test del CLI) — ampliar:

- `test_resolve_lambda_finds_service_by_manifest_yaml` [AC-2.12]

`test_provisioner_provision.py` — `aws_cli.aws` mockeado, captura el
orden de llamadas:

- `test_provision_create_call_order` [AC-2.5]
- `test_provision_update_code_only_calls_update_function_code` [AC-2.6]
- `test_provision_update_config_calls_config_and_role_policy` [AC-2.7]
- `test_provision_partial_failure_records_created_resources` [AC-2.8]
- `test_deprovision_reverse_order` [AC-2.9]

## Verificacion incremental con comandos devtools

El rename de esta fase toca la resolucion de lambdas del CLI, asi que el
foco es confirmar que el CLI sigue encontrando los 4 servicios y que la
suite de tests no se rompio:

```bash
# El CLI resuelve los 4 lambdas por manifest.yaml
python devtools/run.py serverless tests --type=unit --lambda=contact-form
python devtools/run.py serverless tests --type=unit --lambda=tracking-pixel
python devtools/run.py serverless tests --type=unit --lambda=stream-processor
python devtools/run.py serverless tests --type=unit --lambda=db
python devtools/run.py serverless tests --type=unit --shared
python devtools/run.py serverless tests --type=unit            # toda la suite
python devtools/run.py serverless help
```

Los 4 `tests --lambda` DEBEN pasar: si el CLI siguiera buscando
`lambda.yaml` no resolveria ningun servicio. `provisioner.py` aun no se
invoca desde el CLI (eso es la Fase 5), por eso aqui no hay `deploy`.

## Verificacion (Definition of Done de la fase)

```bash
devtools/.venv/bin/python -m pytest devtools/tests/unit/src/serverless/test_provisioner_render.py devtools/tests/unit/src/serverless/test_provisioner_provision.py -v
python devtools/run.py docker lint --module=devtools
devtools/.venv/bin/python -m mypy devtools/serverless/provisioner.py
# rename verificado:
rg --files serverless/lambda/services/ | rg 'lambda\.yaml$'   # 0
rg --files serverless/lambda/services/ | rg 'manifest\.yaml$' # 4
# comandos devtools que no deben romperse tras el rename:
python devtools/run.py serverless tests --type=unit
python devtools/run.py serverless help
```

- [ ] AC-2.1..AC-2.12 cubiertos por tests verdes
- [ ] Coverage >= 80% per-file en `provisioner.py`
- [ ] `packaging.py` produce `build.zip` y sus tests siguen verdes
- [ ] Rename `lambda.yaml` -> `manifest.yaml` aplicado en los 4
      servicios + el scaffold; `MANIFEST_FILENAME` centralizada en
      `resolve.py`; los 7 modulos de devtools que lo leian actualizados
- [ ] `serverless tests --type=unit` sigue verde (el rename no rompe la
      resolucion de lambdas)
- [ ] Ruff + mypy sin errores

---

[Anterior: 03](03-fase-1-capa-base.md) | [README](README.md) | [Siguiente: 05](05-fase-3-provisioner-infra.md)
