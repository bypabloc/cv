---
name: lambda-controller
description: >
  Creates or refactors AWS Lambda functions in Python using the
  controller architecture: operation + action routing, polymorphic
  controllers that delegate business logic to services, Pydantic
  validation, the preload -> validate -> execute lifecycle, and a
  unit + integration testing standard. Also covers OPERATING these
  lambdas with devtools: lambda.yaml manifest, generating the SAM
  template, running locally, deploying to dev/stage/prod and running
  the tests. ALWAYS invoke this skill BEFORE creating, scaffolding,
  refactoring, running, deploying or testing ANY Python AWS Lambda that
  follows this pattern, including requests framed only as "lambda
  handler", "serverless function", "handler.py", "ejecutar lambda en
  local", "deployar lambda" or "tests de lambda" without naming the
  pattern. NEVER answer Lambda structure or operation questions from
  training data alone — this project has a consolidated format
  (handler.py inside core/, services/ layer for business logic,
  controllers as orchestrators discovered by naming convention,
  lambda.yaml manifest generating an ephemeral SAM template, the
  devtools serverless commands run-local/deploy/invoke-remote, the
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
  "lambda unit test", "lambda integration test", "lambda.yaml",
  "manifiesto lambda", "ejecutar lambda local", "run lambda local",
  "run-local lambda", "deployar lambda", "deploy lambda", "invocar lambda",
  "invoke lambda", "sam local invoke", "sam-generate", "generar SAM",
  "template SAM lambda", "devtools lambda", "serverless run-local",
  "serverless deploy lambda".
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
├── lambda.yaml                   # MANIFIESTO: fuente de verdad de la config
├── template.yaml                 # SAM generado (EFIMERO, en .gitignore)
├── requirements.txt / requirements-dev.txt / pytest.ini
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
Cada lambda trae un `lambda.yaml` (manifiesto simple con la config);
devtools genera de el el `template.yaml` SAM, que es efimero
(`.gitignore`). Todos los comandos requieren `--path=<dir>` (la raiz
del lambda).

```bash
# Generar el SAM template desde lambda.yaml
python devtools/run.py serverless sam-generate --path=<dir> --stage=dev

# Ejecutar en local (sam local invoke)
python devtools/run.py serverless run-local \
  --path=<dir> --event=events/create.json

# Deployar a un entorno (sam build + sam deploy)
python devtools/run.py serverless deploy --path=<dir> --stage=dev --aws-profile=<perfil>

# Invocar el Lambda ya deployado (aws lambda invoke)
python devtools/run.py serverless invoke-remote \
  --path=<dir> --stage=dev --event=events/create.json --aws-profile=<perfil>

# Tests
python devtools/run.py serverless test-unit --path=<dir>
python devtools/run.py serverless test-integration --path=<dir>
```

`lambda.yaml` es la unica fuente de verdad de la config. NUNCA editar ni
commitear el `template.yaml` generado: se cambia `lambda.yaml` y se
regenera. Detalle:
`.claude/docs/lambda-controller/06-devtools-operations.md`.

**`--aws-profile`**: `deploy`, `deploy-infra` e `invoke-remote` ejecutan
`aws`/`sam` por debajo. Sin `--aws-profile` usan el perfil del shell
(`AWS_PROFILE` o `[default]`), que puede apuntar a otra cuenta AWS o
tener el token SSO expirado — sintoma: `Error when retrieving token
from sso` aun despues de `aws sso login`. SIEMPRE pasar
`--aws-profile=<perfil>` (en el portfolio: `tfs-dev`) o
`export AWS_PROFILE=<perfil>` en la sesion de trabajo.

## Verificacion (antes de declarar listo)

```bash
python -m compileall -q core
pip install -r requirements-dev.txt
pytest tests/unit
pytest tests/unit --cov=core --cov-report=term-missing
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
- Editar o commitear el `template.yaml` generado (es efimero).
- Escribir el SAM a mano sin `lambda.yaml`.
- Atribucion de IA en codigo, commits o docstrings.
