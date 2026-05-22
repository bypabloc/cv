---
name: lambda-controller
description: >
  Creates or refactors AWS Lambda functions in Python using the
  controller architecture: operation + action routing, polymorphic
  controllers that delegate business logic to services, Pydantic
  validation, the preload -> validate -> execute lifecycle, and a
  unit + integration testing standard. Also covers OPERATING these
  lambdas with devtools: the manifest.yaml manifest, running locally,
  deploying to dev/stage/prod, destroying and running the tests.
  ALWAYS invoke this skill BEFORE creating, scaffolding,
  refactoring, running, deploying or testing ANY Python AWS Lambda that
  follows this pattern, including requests framed only as "lambda
  handler", "serverless function", "handler.py", "ejecutar lambda en
  local", "deployar lambda" or "tests de lambda" without naming the
  pattern. NEVER answer Lambda structure or operation questions from
  training data alone — this project has a consolidated format
  (handler.py inside core/, services/ layer for business logic,
  controllers as orchestrators discovered by naming convention, the
  manifest.yaml manifest that devtools translates directly to AWS CLI
  calls with local state — NO SAM, NO CloudFormation — the devtools
  serverless commands run/deploy/destroy/status/tests, the
  santander_offer_handler testing standard) that overrides generic
  advice.
  Use when the user says "crear lambda", "create lambda", "nuevo lambda",
  "new lambda", "refactorizar lambda", "refactor lambda", "estructura de
  lambda", "lambda structure", "formato de lambda", "lambda controller",
  "controller lambda", "operation action lambda", "operation + action",
  "handler.py", "lambda handler", "scaffold lambda", "plantilla lambda",
  "lambda template", "estandar lambda", "lambda python", "base_controller",
  "import_controller", "payment_router structure", "agregar operacion
  lambda", "agregar action lambda", "tests de lambda", "lambda testing",
  "lambda unit test", "lambda integration test", "manifest.yaml",
  "manifiesto lambda", "ejecutar lambda local", "run lambda local",
  "deployar lambda", "deploy lambda", "destruir lambda", "invocar lambda",
  "invoke lambda", "devtools lambda", "serverless run",
  "serverless tests lambda", "serverless deploy lambda",
  "provisionar lambda", "estado del lambda".
user-invocable: true
disable-model-invocation: false
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
argument-hint: "[crear <nombre> | refactorizar <ruta> | agregar operacion <nombre>]"
---

# Lambda Controller Architecture

Formato para crear y refactorizar AWS Lambdas en Python con el patron
`operation + action` -> controller (orquestador) + service (logica de
negocio), validacion Pydantic y testing unit + integration.

ALWAYS read the project artifacts BEFORE answering — never rely on
generic Lambda knowledge:

- Rule: `.claude/rules/lambda-controller.md` — reglas SIEMPRE/NUNCA.
- Docs: `.claude/docs/lambda-controller/` — 5 capitulos conceptuales.
- Scaffold: `.claude/templates/lambda-controller/` — codigo a copiar.

## Cuando usar esta skill

- Crear un Lambda Python nuevo desde cero.
- Refactorizar un Lambda monolitico (`if action == ...`) a este patron.
- Agregar una operacion o accion a un Lambda que ya usa el patron.
- Escribir o revisar los tests de un Lambda de este tipo.
- Responder cualquier pregunta sobre la estructura de un Lambda Python
  en este contexto.

## El patron en una frase

Un Lambda atiende muchas operaciones. El evento trae `operation` (que
dominio) y `action` (que verbo). `core/handler.py` resuelve
dinamicamente la clase controller, que valida su payload con Pydantic,
delega la logica de negocio a un service y normaliza la respuesta.

## Estructura obligatoria

```text
<lambda-name>/
├── manifest.yaml                 # MANIFIESTO: fuente de verdad de la config
├── pyproject.toml                # PEP 621: deps de runtime + grupo dev
├── core/
│   ├── handler.py                # ENTRYPOINT (router delgado), DENTRO de core/
│   ├── controllers/<operation>/<action>.py   # clase <Action>
│   ├── services/<operation>_service.py        # logica de negocio
│   ├── models/{event.py, <operation>.py}      # validacion Pydantic
│   ├── settings/{config.py, operations.py}    # AppConfig + OPERATIONS
│   └── utils/{base_controller, base_settings, import_controller,
│              invoker, logger, validation/event}
└── tests/{conftest.py, unit/, integration/}
```

## Reglas duras (resumen — detalle en la rule)

- `handler.py` vive en `core/`; AWS Handler = `core.handler.lambda_handler`.
- Evento: `{operation, action, data}`.
- Clase controller = `action.capitalize()`; hereda de `BaseController`;
  implementa `execute()`.
- Logica de negocio SOLO en `core/services/`. El handler enruta, el
  controller orquesta.
- `execute()` y las fases devuelven `{is_valid, data, code}`.
- `code` por rango: 1xxx validacion, 2xxx config, 4xxx negocio, 5xxx
  externo, 6xxx sistema.
- Toda operacion registrada en `OPERATIONS` (`settings/operations.py`).
- Controllers descubiertos por convencion, NUNCA registrados a mano.

## Flujo: crear un Lambda nuevo

1. Leer `.claude/rules/lambda-controller.md` y los docs relevantes.
2. Copiar el scaffold:
   `cp -r .claude/templates/lambda-controller <destino>/<lambda-name>`
3. Reemplazar placeholders `<NOMBRE_DEL_SERVICIO>`, `<Autor>`,
   `YYYY-MM-DD` en todos los archivos.
4. Adaptar la operacion de ejemplo: renombrar `controllers/example/`,
   `models/example.py`, `services/example_service.py` al dominio real.
5. Registrar la operacion en `OPERATIONS`; declarar ARNs en `AppConfig`.
6. Renombrar los `LogMetricType.OPERATION_*` al dominio.
7. Escribir tests (un archivo por escenario): modelo + service +
   controller + handler por cada accion.
8. Verificar: `python -m compileall -q core` y `pytest tests/unit`.

## Flujo: refactorizar un Lambda monolitico

1. Crear la estructura `core/` desde el scaffold.
2. Mover el entrypoint a `core/handler.py` (solo routing).
3. Cada rama `if action == ...` se vuelve: un controller + un service +
   un modelo Pydantic.
4. Centralizar config en `AppConfig`, codigos en `ErrorCode`.
5. Reemplazar el manejo de errores ad-hoc por `{is_valid, data, code}`
   + `ServiceError`.
6. Escribir los tests faltantes.
7. Verificar que el comportamiento observable no cambio.

Mapa de refactor y checklist Definition of Done en
`.claude/docs/lambda-controller/05-create-and-refactor.md`.

## Flujo: agregar una operacion o accion

- **Accion nueva** (operacion existente): crear
  `controllers/<operation>/<action>.py` (clase `<Action>`), su modelo
  en `models/<operation>.py`, su logica en
  `services/<operation>_service.py`. No tocar `handler.py` ni `OPERATIONS`.
- **Operacion nueva**: crear `controllers/<operation>/`,
  `services/<operation>_service.py`, `models/<operation>.py`, y agregar
  la entrada en `OPERATIONS`.

## Estandar de testing

Basado en el lambda real `santander_offer_handler`:

- `tests/unit/` (aislado) y `tests/integration/` (E2E con recursos
  reales), cada uno con su `conftest.py`.
- Un archivo por escenario: `test_<unidad>_<escenario>.py` con UNA
  funcion `test_*`. El docstring del modulo describe el caso.
- Builders compartidos en `_helpers.py` (unit) y `_fixtures/`
  (integration), prefijo `_`.
- `conftest.py` raiz mockea libs propietarias (solo unit), setea env
  vars, ajusta `sys.path`. El de integration NO mockea; usa fixtures
  con cleanup `autouse`.
- Asserts EXACTOS. Mockear solo E/S externa, nunca codigo propio.

Detalle: `.claude/docs/lambda-controller/04-testing.md`.

## Operar el Lambda con devtools

El lambda-controller se opera con el script `serverless` de devtools.
Cada lambda trae un `manifest.yaml` (manifiesto simple con la config);
devtools lo lee directamente: `provisioner.py` lo traduce a llamadas
AWS CLI y mantiene un archivo de estado local por `(scope, stage)`. NO
hay SAM ni CloudFormation. Los comandos apuntan al lambda con
`--lambda=<nombre>` (se resuelve contra
`serverless/lambda/services/<nombre>/`) o `--path=<dir>`. Verbos:
`run` (ejecutar, local o remoto), `deploy` (provisionar), `destroy`
(eliminar), `status` (estado) y `tests` (suite).

```bash
# Ejecutar el Lambda: --stage=local -> RIE via Docker (o --runtime-mode=direct);
#   --stage=dev|stage|prod -> aws lambda invoke contra el ya deployado.
python devtools/run.py serverless run \
  --stage=local --lambda=<nombre> --event=events/create.json
python devtools/run.py serverless run \
  --stage=dev --lambda=<nombre> --event=events/create.json --aws-profile=<perfil>

# Deployar a un entorno (uv arma el build.zip, provisioner lo sube con AWS CLI)
python devtools/run.py serverless deploy --lambda=<nombre> --stage=dev --aws-profile=<perfil>

# Estado y destroy
python devtools/run.py serverless status --lambda=<nombre> --stage=dev --aws-profile=<perfil>
python devtools/run.py serverless destroy --lambda=<nombre> --stage=dev --yes --aws-profile=<perfil>

# Tests: un solo comando, --type=unit|integration|coverage
python devtools/run.py serverless tests --type=unit --lambda=<nombre>
python devtools/run.py serverless tests --type=integration --lambda=<nombre>
```

`run` SIEMPRE necesita `--stage` y `--lambda` (o `--path`). `tests`
SIEMPRE necesita `--type`; sin target corre la suite completa, con
`--shared` corre la libreria comun. `manifest.yaml` es la unica fuente
de verdad de la config; provisioner lo traduce a AWS CLI en cada
`deploy`, y el diff de hashes del estado local decide si crea, actualiza
o no hace nada. Detalle:
`.claude/docs/lambda-controller/06-devtools-operations.md`.

**`--aws-profile`**: `deploy`, `destroy`, `status` y `run` contra un
stage deployado ejecutan `aws` por debajo. Sin `--aws-profile` usan el
perfil del shell (`AWS_PROFILE` o `[default]`), que puede apuntar a otra
cuenta AWS o tener el token SSO expirado — sintoma: `Error when
retrieving token from sso` aun despues de `aws sso login`. SIEMPRE pasar
`--aws-profile=<perfil>` (en el portfolio: `tfs-dev`) o
`export AWS_PROFILE=<perfil>` en la sesion de trabajo.

## Verificacion (antes de declarar listo)

```bash
python -m compileall -q core
uv sync                              # deps de runtime + grupo dev
pytest tests/unit
pytest tests/unit --cov=core --cov-report=term-missing

# o via devtools:
python devtools/run.py serverless tests --type=unit --lambda=<nombre>
```

NUNCA declarar el Lambda listo sin que `compileall` y `pytest tests/unit`
pasen.

## Anti-patrones (rechazar)

- `handler.py` en la raiz del lambda (va en `core/`).
- Logica de negocio en el handler o en el controller (va en `services/`).
- `if action == ...` en el handler (un controller por accion).
- Acceder a `event['campo']` sin un modelo Pydantic.
- Registrar controllers en un dict manual.
- Varias funciones `test_*` en un mismo archivo.
- Mockear `services`/`controllers` propios en los tests.
- Commitear `build/`, `build.zip` o el archivo de estado local
  (`serverless/lambda/.state/`) — son efimeros / locales.
- Modificar un recurso AWS a mano en la consola (devtools no detecta el
  drift; cambiar `manifest.yaml` + re-deployar, auditar con `status`).
- Atribucion de IA en codigo, commits o docstrings.
