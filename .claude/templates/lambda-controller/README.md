# Plantilla: Lambda con arquitectura de controllers

> Scaffold reproducible para crear AWS Lambdas en Python con el patron
> `operation + action` -> controller polimorfico (orquestador) +
> service (logica de negocio), validacion Pydantic y ciclo de vida
> `preload -> validate -> execute`.

Este directorio es una **plantilla**: se copia entera al crear un Lambda
nuevo. No se ejecuta desde aqui. La documentacion conceptual completa
vive en [.claude/docs/lambda-controller/](../../docs/lambda-controller/).

## Que resuelve

Un solo Lambda atiende muchas operaciones discretas. El evento trae
`operation` (que dominio) y `action` (que hacer). El handler resuelve
dinamicamente la clase controller correcta, que valida su payload con
un modelo Pydantic, delega la logica de negocio a un service y
normaliza la respuesta.

## Estructura

```text
<lambda-name>/
├── pyproject.toml               # PEP 621: deps de runtime + grupo dev
│                                #   (pytest, coverage). Un solo archivo;
│                                #   reemplaza requirements*.txt y pytest.ini.
├── core/
│   ├── handler.py               # ENTRYPOINT: lambda_handler(event, context)
│   ├── controllers/             # ORQUESTADORES: un paquete por operation
│   │   └── <operation>/
│   │       ├── create.py        # clase Create  (action 'create')
│   │       └── check.py         # clase Check   (action 'check')
│   ├── services/                # LOGICA DE NEGOCIO del lambda
│   │   └── <operation>_service.py
│   ├── models/
│   │   ├── event.py             # EventModel: valida operation/action/data
│   │   └── <operation>.py       # modelos Pydantic del payload por accion
│   ├── settings/
│   │   ├── config.py            # AppConfig + ErrorCode + LogMetricType + logger
│   │   └── operations.py        # OPERATIONS: codename -> controller + arn_key
│   └── utils/
│       ├── base_controller.py   # BaseController (ABC): preload/validate/execute
│       ├── base_settings.py     # BaseSettings: carga env vars
│       ├── import_controller.py # import dinamico de controllers
│       ├── invoker.py           # invocacion de Lambdas downstream (boto3)
│       ├── logger.py            # logger JSON estructurado
│       └── validation/
│           └── event.py         # validate_event: wrapper con manejo de errores
└── tests/
    ├── conftest.py              # mocks unit + env vars + sys.path
    ├── unit/                    # tests aislados (1 archivo = 1 escenario)
    │   ├── _helpers.py          # builders compartidos (prefijo _)
    │   └── test_<unidad>_<escenario>.py
    └── integration/             # tests E2E con recursos reales
        ├── conftest.py          # SIN mocks; fixtures + cleanup autouse
        ├── _fixtures/           # builders de integracion (prefijo _)
        └── test_<escenario>_e2e.py
```

`handler.py` vive DENTRO de `core/`, al nivel de las demas carpetas.
En AWS el Handler de la funcion es `core.handler.lambda_handler`.

### Separacion de responsabilidades

| Capa | Responsabilidad | NO debe |
|------|-----------------|---------|
| `handler.py` | Enrutar `operation+action` -> controller | Tener logica de negocio |
| `controllers/` | Orquestar: validar -> llamar service -> normalizar | Tener logica de negocio |
| `services/` | Logica de negocio del lambda | Conocer el formato del evento Lambda |
| `models/` | Validacion de estructura (Pydantic) | Tener logica de negocio |
| `utils/` | Infraestructura generica (logger, invoker, ...) | Conocer el dominio |

## Flujo de una invocacion

```text
event {operation, action, data}
  -> core/handler.lambda_handler
       -> validate_event           (utils/validation/event.py)
            -> EventModel.validate_event  (models/event.py)
                 -> import_controller     (utils/import_controller.py)
                      -> OPERATIONS       (settings/operations.py)
       -> controller_class(data).run()    (BaseController)
            -> preload   (resuelve ARN downstream desde AppConfig)
            -> validate  (event_model Pydantic valida 'data')
            -> execute   (orquesta: llama al service, normaliza salida)
                 -> services/<operation>_service.py  (logica de negocio)
  -> respuesta normalizada {is_valid, code, status, message, data}
```

## Como instanciar la plantilla

1. Copiar este directorio al destino y renombrarlo:
   `cp -r .claude/templates/lambda-controller <ruta>/<lambda-name>`
2. Reemplazar los placeholders `<NOMBRE_DEL_SERVICIO>`, `<Autor>`,
   `YYYY-MM-DD` en todos los archivos.
3. Renombrar `controllers/example/` a la primera operacion real y sus
   clases `Create`/`Check` segun las acciones que necesite.
4. Renombrar `models/example.py` y ajustar los campos Pydantic al
   payload real.
5. Renombrar `services/example_service.py` y escribir la logica de
   negocio real (los controllers solo delegan a el).
6. Registrar la operacion en `settings/operations.py` (`OPERATIONS`).
7. Declarar en `AppConfig` (`settings/config.py`) los ARNs downstream
   referenciados por los controllers (`arn_config_key`). Eliminar
   `arn_example` y `utils/invoker.py` si el Lambda no invoca otros.
8. Renombrar los `LogMetricType.OPERATION_*` al dominio real.
9. Editar `lambda.yaml`: `name`, `runtime`, `memory`/`timeout`, env vars
   por stage, layers, IAM policies. Es la fuente de verdad de la config.
10. Editar `pyproject.toml`: declarar las deps de runtime del Lambda en
    `[project.dependencies]`. El grupo `dev` (`[dependency-groups]`) ya
    trae pytest y coverage.

## Agregar una operacion o accion nueva

- **Accion nueva** en una operacion existente: crear
  `controllers/<operation>/<action>.py` con una clase
  `<Action>` (= `action.capitalize()`) que herede de `BaseController`,
  su modelo en `models/<operation>.py` y su logica en
  `services/<operation>_service.py`.
- **Operacion nueva**: crear `controllers/<operation>/`,
  `services/<operation>_service.py` y agregar la entrada en `OPERATIONS`.

No hay registro manual de clases: `import_controller` las descubre por
convencion de nombres (`controllers.<controller>.<action>.<Action>`).

## Reglas del contrato (invariantes)

- El nombre de la clase controller es SIEMPRE `action.capitalize()`.
- Todo controller hereda de `BaseController` e implementa `execute()`.
- `execute()` devuelve SIEMPRE `{is_valid, data, code}`.
- `code == 0` exito; rangos: 1xxx validacion, 2xxx config, 4xxx negocio,
  5xxx API externa, 6xxx sistema.
- El handler se llama `handler.py` y vive en `core/`; la funcion,
  `lambda_handler`.
- La logica de negocio vive en `services/`, NUNCA en el controller ni
  en el handler.

## Testing

La carpeta `tests/` separa dos tipos de prueba (estandar tomado de
`santander_offer_handler`):

- **`tests/unit/`** - tests aislados, sin red ni AWS. `conftest.py`
  raiz mockea librerias propietarias y setea env vars.
- **`tests/integration/`** - tests E2E con recursos reales.
  `tests/integration/conftest.py` NO mockea; provee fixtures con
  cleanup `autouse`.

Convenciones:

- **Un archivo por escenario**: `test_<unidad>_<escenario>.py`, con UNA
  funcion `test_*` dentro. El nombre describe el caso.
- El **docstring del modulo** describe el escenario (Given/When/Then).
- Builders compartidos en `_helpers.py` (unit) y `_fixtures/`
  (integration) — el prefijo `_` evita que pytest los recolecte.
- Asserts EXACTOS (`== valor`), nunca rangos.

```bash
uv sync                                 # deps de runtime + grupo dev

pytest tests/unit                       # rapido, sin red
pytest tests/integration                # requiere AWS / red
pytest tests/unit --cov=core --cov-report=term-missing
```

## Operacion con devtools

El Lambda se opera con el script `serverless` de devtools. `lambda.yaml`
es el manifiesto (fuente de verdad de la config); devtools genera de el
el `template.yaml` SAM, que es efimero (`.gitignore`).

```bash
# Generar el SAM template desde lambda.yaml
python devtools/run.py serverless sam-generate --path=<dir> --stage=dev

# Ejecutar en local (sam local invoke)
python devtools/run.py serverless run-local \
  --path=<dir> --event=events/create.json

# Deployar a un entorno
python devtools/run.py serverless deploy --path=<dir> --stage=dev

# Invocar el Lambda ya deployado
python devtools/run.py serverless invoke-remote \
  --path=<dir> --stage=dev --event=events/create.json

# Tests
python devtools/run.py serverless test-unit --path=<dir>
python devtools/run.py serverless test-integration --path=<dir>
```

Detalle: `.claude/docs/lambda-controller/06-devtools-operations.md`.

## Verificacion

```bash
# Sintaxis de todos los archivos
python -m compileall -q core

# Suite de tests
pytest tests/unit

# Detalle del estandar de testing:
# .claude/docs/lambda-controller/04-testing.md
```
