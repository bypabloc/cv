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
- Documentacion conceptual: `.claude/docs/lambda-controller/` (5 docs)
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
- **SIEMPRE** el nombre de la clase controller es `action.capitalize()`
  (`create` -> `Create`, `check` -> `Check`).
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
- **SIEMPRE** el lambda trae un `lambda.yaml` (manifiesto simple con la
  config). devtools genera el `template.yaml` SAM a partir de el.
- **SIEMPRE** el lambda se opera con el script `serverless` de devtools
  (`run-local`, `deploy`, `invoke-remote`, `test-unit`,
  `test-integration`) — ver "Operacion con devtools" abajo.
- **NUNCA** poner logica de negocio en `handler.py` ni en los
  controllers — el handler enruta, el controller orquesta.
- **NUNCA** registrar controllers a mano: se descubren por convencion
  de nombres (`controllers.<controller>.<action>.<Action>`).
- **NUNCA** editar ni commitear el `template.yaml` generado: es efimero
  (esta en `.gitignore`). Se cambia el `lambda.yaml` y se regenera.
- **NUNCA** hardcodear secretos ni ARNs en el codigo — van en
  `AppConfig` via variables de entorno (declaradas en `lambda.yaml`).
- **NUNCA** atribucion de IA en codigo, commits ni docstrings.

## Estructura obligatoria

```text
<lambda-name>/
├── lambda.yaml                   # MANIFIESTO: fuente de verdad de la config
├── template.yaml                 # SAM generado (EFIMERO, en .gitignore)
├── .gitignore                    # excluye template.yaml + .aws-sam/
├── requirements.txt              # deps de runtime
├── requirements-dev.txt          # + pytest, coverage
├── pytest.ini                    # rootdir = raiz del lambda
├── core/
│   ├── handler.py                # ENTRYPOINT (router delgado)
│   ├── controllers/<operation>/  # ORQUESTADORES por operation
│   │   └── <action>.py           # clase <Action>(BaseController)
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

## Lambdas autonomos + libreria comun vendorizada

Cada Lambda es **autonomo en el artefacto desplegado**: el zip que sube
a AWS contiene TODO lo que el Lambda necesita. Pero en el repo, los
Lambdas de un mismo backend pueden COMPARTIR codigo (clientes AWS,
logger, helpers de dominio) sin duplicarlo.

La libreria comun vive UNA sola vez en el repo (en el backend del
portfolio: `serverless/shared/`, hermano de `src/`). devtools la
**vendoriza** — la copia dentro de `<lambda>/core/shared/` — antes de
cada accion que necesita el codigo completo:

- `run-local` / `test-unit` / `test-integration`: copia `shared/` a
  `core/shared/` para que `sam local invoke` y `pytest` la resuelvan.
- `deploy`: copia `shared/` a `core/shared/` antes de `sam build`, asi
  el zip la incluye.

Reglas del vendoring:

- **SIEMPRE** `core/shared/` esta en el `.gitignore` del Lambda: es
  EFIMERO, se regenera en cada accion y se limpia despues. La fuente de
  verdad unica es la copia maestra (`serverless/shared/`).
- **SIEMPRE** el codigo del Lambda importa la libreria comun como
  `from shared...` — resuelve igual en la copia maestra (via el
  `sys.path` del backend) y en el vendor (`core/` esta en el `sys.path`
  del handler).
- **NUNCA** se edita `core/shared/`: es una copia. El cambio va en la
  copia maestra.
- **NUNCA** se commitea `core/shared/`.
- Un Lambda que no comparte codigo simplemente no tiene `core/shared/`.

Asi se concilian las dos propiedades: los Lambdas son **independientes**
(deploy por separado, un stack cada uno) y a la vez **comparten** la
libreria comun sin copiar-pegar codigo en el repo.

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
Todos los comandos requieren `--path=<dir>` (la raiz del lambda, con
`lambda.yaml`). `--module` es alias de `--path`.

```bash
# Generar el SAM template desde lambda.yaml (efimero)
python devtools/run.py serverless sam-generate --path=<dir> --stage=dev

# Ejecutar en local (sam local invoke)
python devtools/run.py serverless run-local \
  --path=<dir> --event=events/create.json

# Deployar a un entorno (sam build + sam deploy)
python devtools/run.py serverless deploy --path=<dir> --stage=dev
python devtools/run.py serverless deploy --path=<dir> --stage=stage
python devtools/run.py serverless deploy --path=<dir> --stage=prod

# Invocar el Lambda ya deployado (aws lambda invoke)
python devtools/run.py serverless invoke-remote \
  --path=<dir> --stage=dev --event=events/create.json

# Tests
python devtools/run.py serverless test-unit --path=<dir>
python devtools/run.py serverless test-integration --path=<dir>
```

`lambda.yaml` es la unica fuente de verdad de la config; el
`template.yaml` SAM se regenera desde el en cada `run-local`/`deploy`.
Sin `--path`, los comandos `deploy`/`test-unit`/`test-integration`
operan sobre el backend SAM del portfolio (modo legacy).

Detalle completo:
[.claude/docs/lambda-controller/06-devtools-operations.md](../docs/lambda-controller/06-devtools-operations.md).

## Verificacion (antes de declarar listo)

```bash
python -m compileall -q core            # sintaxis de todo el codigo
pip install -r requirements-dev.txt
pytest tests/unit                        # suite unitaria verde
pytest tests/unit --cov=core --cov-report=term-missing

# o via devtools (resuelve cwd + deps):
python devtools/run.py serverless test-unit --path=<dir>
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
| Editar el `template.yaml` a mano | Es efimero, se pierde al regenerar | Cambiar `lambda.yaml` |
| Commitear el `template.yaml` generado | Drift con `lambda.yaml` | Esta en `.gitignore` |
| Escribir el SAM sin `lambda.yaml` | No hay fuente de verdad simple | `lambda.yaml` + `sam-generate` |

## Referencias cruzadas

- Scaffold: `.claude/templates/lambda-controller/`
- Docs (5 capitulos): `.claude/docs/lambda-controller/`
- Skill: `lambda-controller`
- AWS Lambda Python (runtime, Powertools, SAM, IAM, costos):
  `.claude/docs/aws-lambda/` o skill `aws-lambda-python`
- Python (estilo, estructura, Ruff): `.claude/rules/python.md`
- Verify-before-done: `.claude/rules/verify-before-done.md`
