# Lambda Controller Architecture (formato de Lambdas Python)

> Formato obligatorio para crear o refactorizar AWS Lambdas en Python:
> patron `operation + action` -> controller (orquestador) + service
> (logica de negocio), validacion Pydantic, ciclo de vida
> `preload -> validate -> execute` y un estandar de testing unit +
> integration.

## Activacion

Aplica SIEMPRE que se trabaje con un AWS Lambda en Python en este
contexto: crearlo desde cero, refactorizar uno monolitico, agregar una
operacion/accion, o escribir sus tests. Tres artefactos lo sostienen:

- Scaffold reproducible: `.claude/templates/lambda-controller/`
- Documentacion conceptual: `.claude/docs/lambda-controller/` (6 docs)
- Skill: `lambda-controller` (invocable con `/lambda-controller`)

NO aplica al frontend Astro del portfolio: es un formato de backend
serverless Python, pensado para repos de Lambdas (ej. legolambda,
legolambda-stacks).

## Reglas criticas (SIEMPRE / NUNCA)

- **SIEMPRE** el entrypoint se llama `handler.py`, vive DENTRO de
  `core/` (al nivel de las demas carpetas) y expone `lambda_handler`.
  El Handler de la funcion AWS es `core.handler.lambda_handler`.
- **SIEMPRE** el evento de entrada tiene la forma
  `{operation, action, data}` — `operation` el dominio, `action` el
  verbo, `data` el payload (objeto).
- **SIEMPRE** el archivo del controller es la forma snake_case de
  `action` (`create` -> `create.py`, `verify-magic-link` ->
  `verify_magic_link.py`).
- **SIEMPRE** el nombre de la clase controller es la forma PascalCase
  de `action` — capitaliza la primera letra de cada segmento separado
  por guion (`create` -> `Create`, `verify-magic-link` ->
  `VerifyMagicLink`, `set-password` -> `SetPassword`).
- **SIEMPRE** todo controller hereda de `BaseController` e implementa
  `execute()`.
- **SIEMPRE** la logica de negocio vive en `core/services/`, NUNCA en
  el handler ni en los controllers.
- **SIEMPRE** `execute()` y las fases (`preload`, `validate`) devuelven
  `{is_valid, data, code}`.
- **SIEMPRE** registrar cada operacion en `settings/operations.py`
  (dict `OPERATIONS`).
- **SIEMPRE** la validacion de estructura del payload va en un modelo
  Pydantic en `models/<operation>.py`.
- **SIEMPRE** los tests siguen el estandar de testing (ver abajo): un
  archivo por escenario, en `tests/unit/` o `tests/integration/`.
- **SIEMPRE** el lambda trae un `manifest.yaml` (manifiesto simple con la
  config). devtools lo lee directamente: `provisioner.py` lo traduce a
  llamadas AWS CLI. NO hay paso intermedio ni template efimero — el
  manifiesto es la unica entrada.
- **SIEMPRE** las dependencias se declaran en un `pyproject.toml` (PEP 621)
  en la raiz del lambda: deps de runtime en `[project.dependencies]`, deps
  de testing en `[dependency-groups]` dev. NUNCA usar `requirements*.txt`
  ni `pytest.ini` — la config de pytest del backend vive en
  `serverless/pyproject.toml` (`[tool.pytest.ini_options]`).
- **SIEMPRE** el lambda se opera con el script `serverless` de devtools
  (`run --stage=...`, `deploy`, `destroy`, `status`, `tests --type=...`)
  — ver "Operacion con devtools" abajo.
- **SIEMPRE** los `core/**/*.py` del service importan paquetes externos
  (pydantic, sqlalchemy, boto3, aws-lambda-powertools, ...) SOLO via
  `shared.<subpaquete>`. NUNCA `from pydantic`, `from sqlalchemy`,
  `import boto3` ni `from aws_lambda_powertools` en `core/`. El
  catalogo de portadores y procedimientos esta en
  `.claude/rules/lambda-shared-imports.md`; `serverless lint-deps`
  valida el contrato.
- **NUNCA** poner logica de negocio en `handler.py` ni en los
  controllers — el handler enruta, el controller orquesta.
- **NUNCA** registrar controllers a mano: se descubren por convencion
  de nombres (`controllers.<controller>.<action>.<Action>`).
- **NUNCA** hardcodear secretos ni ARNs en el codigo — van en
  `AppConfig` via variables de entorno (declaradas en `manifest.yaml`).
- **NUNCA** atribucion de IA en codigo, commits ni docstrings.

## Estructura obligatoria

```text
<lambda-name>/
├── manifest.yaml                 # MANIFIESTO: fuente de verdad de la config
├── .gitignore                    # excluye build/ + build.zip
├── pyproject.toml                # PEP 621: deps de runtime + grupo dev
│                                 #   (pytest, coverage). Reemplaza los
│                                 #   requirements*.txt y el pytest.ini.
├── core/
│   ├── handler.py                # ENTRYPOINT (router delgado)
│   ├── controllers/<operation>/  # ORQUESTADORES por operation
│   │   └── <action_snake>.py     # clase <ActionPascal>(BaseController)
│   ├── services/                 # LOGICA DE NEGOCIO
│   │   └── <operation>_service.py
│   ├── models/
│   │   ├── event.py              # EventModel: valida operation/action/data
│   │   └── <operation>.py        # modelos Pydantic del payload
│   ├── settings/
│   │   ├── config.py             # AppConfig + ErrorCode + LogMetricType + logger
│   │   └── operations.py         # OPERATIONS: codename -> controller + arn_key
│   └── utils/
│       ├── base_controller.py    # BaseController (ABC): preload/validate/execute
│       ├── base_settings.py      # BaseSettings: carga env vars
│       ├── import_controller.py  # import dinamico de controllers
│       ├── invoker.py            # invocacion de Lambdas downstream (boto3)
│       ├── logger.py             # logger JSON estructurado
│       └── validation/event.py   # validate_event: wrapper con manejo de errores
├── core/shared/                  # LIBRERIA COMUN VENDORIZADA (EFIMERA)
└── tests/
    ├── conftest.py               # mocks unit + env vars + sys.path
    ├── unit/                     # 1 archivo = 1 escenario
    │   ├── _helpers.py           # builders compartidos (prefijo _)
    │   └── test_<unidad>_<escenario>.py
    └── integration/              # E2E con recursos reales
        ├── conftest.py           # SIN mocks; fixtures + cleanup autouse
        ├── _fixtures/            # builders de integracion (prefijo _)
        └── test_<escenario>_e2e.py
```

> **Variante del backend del portfolio (mayo 2026).** En este repo, los
> 4 Lambdas comparten el "kit" del estandar (`base_controller`,
> `base_settings`, `import_controller`, `EventModel`, `validate_event` y
> el nucleo `run_controller`) via el subpaquete
> `serverless/lambda/shared/lambda_kit/` — esos archivos NO se duplican
> en el `core/utils/` de cada Lambda. El `core/` de un Lambda importa
> `from shared.lambda_kit import BaseController, build_event_model,
> run_controller, ...`. Ademas, cada Lambda tiene su `pyproject.toml` +
> `uv.lock` + `.venv` AISLADO (sin workspace uv compartido) y NO declara
> deps que ya le aporta el cierre de `shared/` (regla de dedup,
> enforced por `serverless lint-deps`).

## Lambdas autonomos + libreria comun vendorizada

Cada Lambda es **autonomo en el artefacto desplegado**: el zip que sube
a AWS contiene TODO lo que el Lambda necesita. Pero en el repo, los
Lambdas de un mismo backend pueden COMPARTIR codigo (clientes AWS,
logger, helpers de dominio) sin duplicarlo.

La libreria comun vive UNA sola vez en el repo (en el backend del
portfolio: `serverless/lambda/shared/`, hermana de `services/`). NO es un
arbol plano de `.py`: esta organizada en **subpaquetes por dominio**, cada
uno con su propio `pyproject.toml` que declara sus deps externas en
`[project.dependencies]` y sus deps internas a otros subpaquetes en
`[tool.shared]` `internal-deps`. La raiz de `shared/` solo tiene un
`__init__.py` (no re-exporta nada). Subpaquetes actuales:

- `shared/core/` — config, exceptions, types, ulid.
- `shared/aws/` — clientes AWS: dynamodb, ses, ssm.
- `shared/observability/` — logger, tracer, metrics.
- `shared/http/` — cors, responses, ip_extractor, turnstile, validators.
- `shared/db/`, `shared/dynamodb/`, `shared/cache/`, `shared/rate_limit/`.

devtools **vendoriza** la libreria — la copia dentro de
`<lambda>/build/core/shared/` — pero de forma **selectiva**: solo copia
los subpaquetes que el Lambda realmente usa. `shared_resolver.py`
escanea el AST del `core/` del Lambda, detecta los
`from shared.<subpaquete>` y resuelve el **cierre transitivo** leyendo
los `internal-deps` de cada `pyproject.toml`. Un Lambda que no usa
`shared.db` no recibe ese subpaquete ni su dep `sqlalchemy` en el zip.

- `run --stage=local` / `tests`: la libreria se resuelve via el
  `sys.path` del backend (la copia maestra).
- `deploy`: `packaging.py` instala las deps con uv, vendoriza SOLO los
  subpaquetes del cierre transitivo en `build/core/shared/` y arma el
  `build.zip` que se sube a AWS.

Reglas del vendoring:

- **SIEMPRE** `build/` esta en el `.gitignore` del Lambda: es EFIMERO,
  se regenera en cada `deploy` y contiene el artefacto vendorizado. La
  fuente de verdad unica es la copia maestra (`serverless/lambda/shared/`).
- **SIEMPRE** el codigo del Lambda importa la libreria comun apuntando
  al subpaquete explicito: `from shared.observability.logger import
  logger`, `from shared.aws.dynamodb import get_table`,
  `from shared.core.exceptions import ...`. NUNCA importar desde la
  raiz de `shared` (el `__init__.py` no re-exporta).
- **NUNCA** se edita `build/core/shared/`: es una copia. El cambio va
  en la copia maestra.
- **NUNCA** se commitea `build/`.
- El vendoring es selectivo: solo los subpaquetes del cierre transitivo
  llegan al zip. Un Lambda que no comparte codigo no tiene `core/shared/`.

Asi se concilian las dos propiedades: los Lambdas son **independientes**
(deploy por separado, cada uno con su propio archivo de estado) y a la
vez **comparten** la libreria comun sin copiar-pegar codigo en el repo.

## Handlers HTTP genericos (`shared.lambda_kit.http_handler`)

Los Lambdas con `trigger.type=http` NO hardcodean `operation`/`action`
en su `handler.py`: el cliente los envia en cada request y el handler
HTTP generico `shared.lambda_kit.http_handler` los resuelve uniformemente
para todo el backend.

Contrato uniforme del request:

- **GET**: `operation` y `action` son query params; el resto de
  argumentos tambien viajan por query params.
- **POST/PUT/PATCH**: `operation`, `action` y el resto de campos van en
  el body JSON.

`http_handler` realiza el ciclo completo:
1. `extract_request(event)` resuelve `(operation, action, data, method)`
   del evento crudo de API Gateway.
2. Inyecta `data['_meta']` con `{ip, country, user_agent, bypass_secret}`
   extraidos de headers/`requestContext`.
3. Llama a `run_controller({operation, action, data}, event_model)`.
4. Traduce el `DispatchResult` a respuesta API GW.

Cada Lambda HTTP solo declara las DIFERENCIAS via parametros:

```python
return http_handler(
    event,
    event_model=_EVENT_MODEL,
    cors_origin='echo',      # 'echo' (form) | 'public' (sendBeacon / API)
    success_status=201,      # 200 | 201 | 204
    metric_names={           # opcional
        'submitted': 'ContactFormSubmitted',
        'rejected':  'ContactFormRejected',
        'error':     'ContactFormError',
    },
)
```

Reglas asociadas:

- **SIEMPRE** los modelos Pydantic que reciben `_meta` deben usar
  `alias='_meta'` + `populate_by_name=True` (ver `contact_form` y
  `tracking_pixel` como referencia).
- **SIEMPRE** el frontend envia `operation` y `action` (query params en
  GET, body JSON en POST). Ningun handler los hardcodea.
- **NUNCA** duplicar el parsing del evento en cada handler — delegar
  SIEMPRE en `http_handler`.

## Separacion de responsabilidades

| Capa | Responsabilidad | NO debe |
|------|-----------------|---------|
| `handler.py` | Enrutar `operation+action` -> controller | Tener logica de negocio |
| `controllers/` | Orquestar: validar -> service -> normalizar | Tener logica de negocio |
| `services/` | Logica de negocio del lambda | Conocer el evento Lambda |
| `models/` | Validar estructura del payload (Pydantic) | Tener logica de negocio |
| `settings/` | Config (`AppConfig`), enums, `OPERATIONS` | Importar controllers |
| `utils/` | Infraestructura reutilizable | Conocer el dominio |

## Flujo de una invocacion

```text
event {operation, action, data}
  -> core/handler.lambda_handler
       -> validate_event -> EventModel -> import_controller -> OPERATIONS
       -> controller.run()
            -> preload   (resuelve ARN downstream desde AppConfig)
            -> validate  (event_model Pydantic valida 'data')
            -> execute   (orquesta: llama al service, normaliza salida)
  -> {is_valid, code, status, message, data}
```

## Contrato de codigos de error

`code == 0` exito. Rangos: `1xxx` validacion, `2xxx` configuracion,
`4xxx` negocio, `5xxx` API/externo, `6xxx` sistema. El handler colapsa
el `code` del controller a un codigo de salida estable
(`1000`/`2000`/`5100`/`6000`).

## Estandar de testing (basado en santander_offer_handler)

- **Dos niveles**: `tests/unit/` (aislado, sin red) y
  `tests/integration/` (E2E con recursos AWS reales).
- **Un archivo por escenario**: `test_<unidad>_<escenario>.py` con UNA
  funcion `test_*`. El nombre del archivo es el caso.
- **El docstring del modulo** describe el escenario (Given/When/Then);
  el cuerpo del test sigue Arrange-Act-Assert.
- **Builders compartidos** en `tests/unit/_helpers.py` y
  `tests/integration/_fixtures/` — prefijo `_` para que pytest no los
  recolecte.
- **`conftest.py` raiz**: mockea librerias propietarias (solo unit),
  setea env vars, agrega `core/` al `sys.path`.
- **`conftest.py` de integration**: NO mockea; fixtures con cleanup
  `autouse` para garantizar estado limpio.
- **Asserts EXACTOS** (`== valor`), nunca rangos.
- En unit, mockear E/S externa (`invoker_dispatch`, HTTP, libs
  propietarias); NUNCA mockear `models`/`controllers`/`services` propios.
- Por cada accion: test de modelo + service + controller + handler.

Detalle: [.claude/docs/lambda-controller/04-testing.md](../docs/lambda-controller/04-testing.md).

## Crear o refactorizar: receta corta

**Crear**: copiar `.claude/templates/lambda-controller/`, reemplazar
placeholders (`<NOMBRE_DEL_SERVICIO>`, `<Autor>`, `YYYY-MM-DD`),
adaptar la operacion de ejemplo, registrar en `OPERATIONS`, configurar
`AppConfig`, escribir tests.

**Refactorizar un monolitico**: cada rama `if action == ...` se vuelve
un controller + un service; los `event['campo']` se vuelven un modelo
Pydantic; los `os.environ` se centralizan en `AppConfig`; el manejo de
errores ad-hoc se reemplaza por `{is_valid, data, code}` + `ServiceError`.
El comportamiento observable no debe cambiar.

Receta detallada + checklist Definition of Done:
[.claude/docs/lambda-controller/05-create-and-refactor.md](../docs/lambda-controller/05-create-and-refactor.md).

## Operacion con devtools

El lambda-controller se opera con el script `serverless` de devtools.
devtools provisiona cada recurso AWS con AWS CLI imperativo (sin capas
de IaC declarativa) y mantiene un archivo de estado local por
`(scope, stage)`. Todos los comandos requieren apuntar al lambda con
`--lambda=<nombre>` (forma recomendada): el nombre corto se resuelve
contra `serverless/lambda/services/<nombre>/` y devtools valida que la
carpeta cumpla la estructura lambda-controller (que exista y traiga
`manifest.yaml`); si no, lanza un error listando los lambdas validos.
Como alternativa, `--path=<dir>` (o su alias `--module=<dir>`) apunta a
un directorio explicito en cualquier ubicacion.

```bash
# Ejecutar el lambda en local: --runtime-mode=rie -> contenedor con el
#   AWS Lambda Runtime Interface Emulator; --runtime-mode=direct -> el
#   handler corre en proceso. --stage=dev|stage|prod -> aws lambda invoke
#   contra el ya provisionado.
python devtools/run.py serverless run \
  --stage=local --lambda=<nombre> --event=events/create.json
python devtools/run.py serverless run \
  --stage=dev --lambda=<nombre> --event=events/create.json --aws-profile=<perfil>

# Deployar a un entorno: provisioner traduce manifest.yaml a llamadas
#   AWS CLI (rol IAM, LogGroup, funcion, wiring del trigger) y actualiza
#   el archivo de estado. El diff de hashes decide create/update/noop.
python devtools/run.py serverless deploy --lambda=<nombre> --stage=dev --aws-profile=<perfil>
python devtools/run.py serverless deploy --lambda=<nombre> --stage=stage --aws-profile=<perfil>
python devtools/run.py serverless deploy --lambda=<nombre> --stage=prod --aws-profile=<perfil>

# Estado: compara el estado local contra los describe-* de AWS
python devtools/run.py serverless status --lambda=<nombre> --stage=dev --aws-profile=<perfil>

# Destruir: borra los recursos del lambda en un stage (requiere --yes)
python devtools/run.py serverless destroy --lambda=<nombre> --stage=dev --yes --aws-profile=<perfil>

# Tests: un solo comando, --type=unit|integration|coverage. Cada lambda
#   corre con su .venv AISLADO (devtools lo prepara con uv sync + las
#   deps del cierre de shared/).
python devtools/run.py serverless tests --type=unit --lambda=<nombre>
python devtools/run.py serverless tests --type=integration --lambda=<nombre>
python devtools/run.py serverless tests --type=coverage --lambda=<nombre>

# Dedup D-3: valida que el lambda no declare deps que ya aporta shared/.
#   Sin --lambda valida los 4. El deploy/build lo corre de oficio.
python devtools/run.py serverless lint-deps --lambda=<nombre>

# Alternativa: apuntar a un directorio explicito con --path
python devtools/run.py serverless deploy --path=<dir> --stage=dev --aws-profile=<perfil>
```

`manifest.yaml` es la unica fuente de verdad de la config; `provisioner.py`
lo traduce a llamadas AWS CLI en cada `deploy`. devtools mantiene un
archivo de estado por `(scope, stage)` en
`serverless/lambda/.state/<scope>-<stage>.json` (gitignored): registra
los ARNs de lo creado y los hashes de config y codigo. El diff de esos
hashes decide la accion del `deploy` (`create` / `update-function-code`
/ `update-function-configuration` / `noop`), lo que hace el comando
idempotente y re-ejecutable. El comando `tests` sin target
(`--lambda`/`--path`/`--shared`) corre la suite completa: los 4 lambdas
+ la libreria comun.

**`--aws-profile` (perfil AWS CLI)**: `deploy`, `destroy`, `status`,
`provision-infra` y `run` contra un stage provisionado ejecutan `aws`
por debajo. Sin `--aws-profile` usan el perfil del shell (`AWS_PROFILE`
o `[default]`), que puede apuntar a otra cuenta AWS o tener el token SSO
expirado — sintoma: `Error when retrieving token from sso` aun despues
de `aws sso login`. SIEMPRE pasar `--aws-profile=<perfil>` (en el
portfolio: `tfs-dev`) o `export AWS_PROFILE=<perfil>` en la sesion de
trabajo.

Detalle completo:
[.claude/docs/lambda-controller/06-devtools-operations.md](../docs/lambda-controller/06-devtools-operations.md).

## Verificacion (antes de declarar listo)

```bash
python -m compileall -q core            # sintaxis de todo el codigo
uv sync                                  # instala deps de runtime + grupo dev
pytest tests/unit                        # suite unitaria verde
pytest tests/unit --cov=core --cov-report=term-missing

# o via devtools (resuelve cwd + deps con uv):
python devtools/run.py serverless tests --type=unit --lambda=<nombre>
```

## Anti-patrones

| Anti-patron | Por que | Correccion |
|-------------|---------|------------|
| `handler.py` con `if action == ...` | Monolito sin estructura | Un controller por action |
| Logica de negocio en el controller | Mezcla orquestacion y dominio | Mover a `services/` |
| `handler.py` en la raiz del lambda | Rompe el estandar | Va en `core/` |
| Acceder a `event['campo']` directo | Sin validacion | Modelo Pydantic en `models/` |
| `os.environ[...]` disperso | Config no centralizada | `AppConfig` |
| Registrar controllers en un dict manual | Fragil, duplicado | Descubrimiento por convencion |
| Codigos de error magicos | Ilegible | enum `ErrorCode` |
| Varias funciones `test_*` en un archivo | Rompe el estandar de testing | Un archivo por escenario |
| Mockear `services`/`controllers` propios | Test que no prueba nada | Mockear solo E/S externa |
| `assert result['code'] > 1000` | Assert vago | `assert result['code'] == 1001` |
| `requirements.txt` / `pytest.ini` en el lambda | Formato viejo pre-uv | `pyproject.toml` (PEP 621) en la raiz |
| `from shared.logger import logger` (raiz) | El `__init__.py` ya no re-exporta | Import al subpaquete: `from shared.observability.logger import logger` |
| Commitear `build/` o `build.zip` | Son artefactos efimeros del deploy | Estan en `.gitignore` |
| Commitear el `.state/<scope>-<stage>.json` | Estado local de devtools, no versionado | Esta en `.gitignore` |
| Editar un recurso AWS a mano en la consola | devtools no detecta el drift | Cambiar `manifest.yaml` + `deploy`; auditar con `status` |

## Referencias cruzadas

- Scaffold: `.claude/templates/lambda-controller/`
- Docs (6 capitulos): `.claude/docs/lambda-controller/`
- Skill: `lambda-controller`
- Shared-only imports (catalogo de portadores + enforcement):
  `.claude/rules/lambda-shared-imports.md` + skill
  `lambda-shared-imports` + `.claude/docs/lambda-shared-imports/`
- AWS Lambda Python (runtime, Powertools, IAM, costos):
  `.claude/docs/aws-lambda/` o skill `aws-lambda-python`
- Estado local de devtools: `.claude/docs/serverless-backend/05-estado-local.md`
- Python (estilo, estructura, Ruff): `.claude/rules/python.md`
- Verify-before-done: `.claude/rules/verify-before-done.md`
