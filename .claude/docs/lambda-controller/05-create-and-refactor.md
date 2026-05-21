# 05 - Crear y refactorizar

> Anterior: [04 - Testing](04-testing.md) | [README](README.md)

## Crear un Lambda nuevo

### 1. Copiar el scaffold

```bash
cp -r .claude/templates/lambda-controller <ruta-destino>/<lambda-name>
cd <ruta-destino>/<lambda-name>
```

### 2. Reemplazar placeholders

En todos los archivos, reemplazar:

- `<NOMBRE_DEL_SERVICIO>` - nombre del servicio.
- `<Autor>` - autor (sin atribucion de IA).
- `YYYY-MM-DD` - fecha de creacion.

### 3. Adaptar la primera operacion

`controllers/example/` y `models/example.py` y
`services/example_service.py` son ejemplos. Para la operacion real:

- Renombrar `controllers/example/` a `controllers/<operation>/`.
- Renombrar `models/example.py` a `models/<operation>.py` y ajustar los
  campos Pydantic al payload real.
- Renombrar `services/example_service.py` a
  `services/<operation>_service.py` y escribir la logica de negocio.
- En cada `controllers/<operation>/<action>.py`, ajustar imports y
  dejar la clase `<Action>` (= `action.capitalize()`).

### 4. Registrar la operacion

En `settings/operations.py`:

```python
OPERATIONS = {
    '<operation>': {
        'controller': '<operation>',
        'arn_key': 'arn_<operation>',  # omitir si no invoca downstream
    },
}
```

### 5. Configurar AppConfig

En `settings/config.py`, declarar en `AppConfig` los campos que el
servicio necesita (ARNs downstream, parametros). Eliminar `arn_example`
y `utils/invoker.py` si el Lambda no invoca otros Lambdas.

### 6. Ajustar enums

Renombrar los `LogMetricType.OPERATION_*` al dominio del servicio
(ej. `PAYMENT_ROUTING_START`). Agregar `ErrorCode` si hace falta.

### 7. Declarar dependencias

El scaffold trae un `pyproject.toml` (PEP 621) en la raiz del lambda.
Declarar las deps de runtime en `[project.dependencies]` y las de
testing ya estan en el grupo `dev` (`[dependency-groups]`). No hay
`requirements*.txt` ni `pytest.ini` — la config de pytest del backend
vive en `serverless/pyproject.toml`.

### 8. Escribir tests

Por cada accion, al menos:

- 1 test del modelo (payload invalido rechazado).
- 1 test del service (logica + `ServiceError` ante fallo).
- 1 test del controller (traduccion de resultado/error).
- 1 test del handler (routing del evento).

Un archivo por escenario, en `tests/unit/`. Ver [04 - Testing](04-testing.md).

### 9. Verificar

```bash
python -m compileall -q core
uv sync
pytest tests/unit
```

## Refactorizar un Lambda monolitico al patron

Punto de partida tipico: un `handler.py` (o `lambda_function.py`) con
toda la logica y un `if action == ...`.

### Paso a paso

1. **Crear la estructura** `core/` con el scaffold (handler, settings,
   utils, carpetas vacias controllers/services/models).
2. **Mover el entrypoint** a `core/handler.py`. El handler queda solo
   con el routing; ajustar el Handler de AWS a
   `core.handler.lambda_handler`.
3. **Identificar las operaciones**: cada rama del `if`/`switch` por
   `action` (o por tipo de evento) es una `operation` o una `action`.
4. **Por cada operacion**:
   - Crear `controllers/<operation>/<action>.py` con la clase `<Action>`.
   - Extraer la **logica de negocio** a `services/<operation>_service.py`.
   - Crear el **modelo Pydantic** en `models/<operation>.py` con los
     campos que esa rama leia del evento.
5. **Registrar** cada operacion en `OPERATIONS`.
6. **Mover la config** (env vars, constantes) a `AppConfig` y los
   codigos de error a `ErrorCode`.
7. **Reemplazar el manejo de errores** ad-hoc por el contrato
   `{is_valid, data, code}` + `ServiceError`.
8. **Escribir tests** de los escenarios que antes no estaban cubiertos.
9. **Verificar** que el comportamiento observable no cambio: mismos
   eventos de entrada -> mismas respuestas.

### Mapa de refactor

| Codigo monolitico | Va a |
|-------------------|------|
| `def lambda_handler` con `if action` | `core/handler.py` (solo routing) |
| Cada rama `if`/`elif` por action | un controller + un service |
| Logica de negocio dentro de las ramas | `services/<operation>_service.py` |
| `event['campo']` accesos directos | modelo Pydantic en `models/` |
| `os.environ[...]` dispersos | `AppConfig` en `settings/config.py` |
| `print()` / `logging` ad-hoc | `logger` de `settings/config.py` |
| Codigos de error magicos | enum `ErrorCode` |
| `boto3.client('lambda').invoke(...)` | `utils/invoker.invoker_dispatch` |

### Migracion incremental

Si el Lambda no puede reescribirse de una sola vez:

1. Empezar moviendo solo el routing al patron, dejando los controllers
   como wrappers finos que llaman al codigo viejo.
2. Migrar una operacion a la vez (controller -> service -> model).
3. Cada operacion migrada gana sus tests antes de pasar a la siguiente.

## Checklist de Definition of Done

- [ ] Placeholders reemplazados en todos los archivos.
- [ ] El handler se llama `core/handler.py`, funcion `lambda_handler`.
- [ ] El handler NO tiene logica de negocio (solo routing).
- [ ] Cada operacion tiene controller + service + modelo.
- [ ] La logica de negocio vive en `services/`, no en controllers.
- [ ] Toda operacion esta registrada en `OPERATIONS`.
- [ ] Las clases controller se llaman `action.capitalize()`.
- [ ] `execute()` y las fases devuelven `{is_valid, data, code}`.
- [ ] `python -m compileall -q core` pasa.
- [ ] `pytest tests/unit` pasa; cada accion tiene tests.
- [ ] Sin atribucion de IA en codigo, commits ni docstrings.

---

[README](README.md) | Anterior: [04](04-testing.md)
