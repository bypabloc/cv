# 02 - Handler y routing

> Anterior: [01 - Arquitectura](01-architecture.md) | Siguiente: [03 - Controllers y models](03-controllers-and-models.md)

## El handler es un router delgado

`core/handler.py` NO contiene logica de negocio. Su unico trabajo:

1. Loguear el inicio de la invocacion.
2. Validar el evento y resolver el controller (`validate_event`).
3. Instanciar el controller y ejecutar `run()`.
4. Normalizar el resultado a la respuesta final del Lambda.
5. Capturar cualquier excepcion no manejada -> `code 6000`.

## sys.path: por que el handler lo ajusta

`handler.py` vive dentro de `core/`. Para que los imports absolutos
(`from models...`, `from settings...`, `from services...`) resuelvan,
`core/` debe estar en `sys.path`. AWS Lambda y Serverless invoke local
no siempre lo agregan, asi que el handler lo hace al inicio:

```python
import os
import sys

_core_dir = os.path.dirname(os.path.abspath(__file__))
if _core_dir not in sys.path:
    sys.path.insert(0, _core_dir)
```

Esto debe ejecutarse ANTES de cualquier `from models...`. Por eso esas
lineas van arriba de todo, con la excepcion de `import os`/`import sys`.

En la consola AWS y en el `manifest.yaml`, el Handler de la funcion es
`core.handler.lambda_handler`.

## Flujo de routing

```text
event
  -> validate_event(event)                  utils/validation/event.py
       -> EventModel.validate_event(event)   models/event.py
            valida: event es dict
                    'operation' presente y string no vacio
                    'action'    presente y string no vacio
                    'data'      presente y es dict
            -> import_controller(operation, action)  utils/import_controller.py
                 -> resolve_operation(operation)     OPERATIONS lookup
                 -> import_module('controllers.<folder>.<action>')
                 -> getattr(module, '<Action>')
                 -> verifica issubclass(cls, BaseController)
```

`validate_event` envuelve todo y traduce cualquier excepcion
(`ValidationError`, `ValueError`, `Exception`) a una respuesta de error
uniforme `{is_valid: False, code, status, message, data}`.

## Resolucion operation -> controller

`settings/operations.py` define el mapa:

```python
OPERATIONS = {
    'payments': {'controller': 'payments', 'arn_key': 'arn_payments'},
    # alias: otro codename que reusa el mismo controller
    'payments_legacy': {'controller': 'payments', 'arn_key': 'arn_payments'},
}
```

- `controller` -> carpeta dentro de `controllers/`.
- `arn_key` -> campo de `AppConfig` con el ARN downstream (lo usa la
  fase `preload`). Omitir o ignorar si la operacion no invoca otro Lambda.

Si `operation` no esta en `OPERATIONS`, `resolve_operation` devuelve el
nombre tal cual, y el `import_module` fallara con un error descriptivo
(`MODULE_NOT_FOUND`) en vez de un `KeyError` opaco.

## Resolucion action -> clase

`action` se usa de dos formas:

- Como nombre de archivo: `controllers/<folder>/<action_snake>.py`
  (kebab-case del wire se convierte a snake_case en el filesystem).
- Como nombre de clase: PascalCase de `action` — capitaliza la primera
  letra de cada segmento separado por guion.

| action (wire) | archivo | clase |
| --- | --- | --- |
| `create` | `create.py` | `Create` |
| `check` | `check.py` | `Check` |
| `cancel` | `cancel.py` | `Cancel` |
| `verify-code` | `verify_code.py` | `VerifyCode` |
| `verify-magic-link` | `verify_magic_link.py` | `VerifyMagicLink` |
| `set-password` | `set_password.py` | `SetPassword` |

Reglas:

- El `action` del wire (en el evento `{operation, action, data}`) es
  **kebab-case** o **una sola palabra**.
- El archivo del controller convierte los `-` a `_`
  (`verify-magic-link` -> `verify_magic_link.py`).
- La clase capitaliza cada segmento: la formula es
  `''.join(seg.capitalize() for seg in action.split('-'))`.
- Acciones de una sola palabra (lo mas comun) funcionan directo
  (`create` -> `Create`). Las multi-segmento son aceptables para
  acciones compuestas semanticamente (`verify-code`, `set-password`).
- Evitar `snake_case` o `camelCase` en el wire: romperian la
  convencion (siempre kebab-case o palabra simple).

## Respuesta final del Lambda

El handler colapsa el `code` interno del controller a un codigo de
salida estable:

```python
if result_code >= 5000:   error_code = 5100   # API / externo
elif result_code >= 2000: error_code = 2000   # configuracion
else:                     error_code = 1000   # validacion / negocio
```

Forma de la respuesta:

```jsonc
// exito
{ "is_valid": true, "data": { ... } }

// error
{ "is_valid": false, "code": 5100, "status": 5100,
  "message": "...", "data": { ... } }
```

`code` y `status` llevan el mismo valor (compatibilidad con consumidores
que esperan uno u otro nombre).

## Que NO poner en el handler

- Logica de negocio -> va en `services/`.
- Validacion de payloads -> va en `models/` (Pydantic).
- Llamadas a APIs externas / otros Lambdas -> va en `services/` +
  `utils/invoker.py`.

El handler solo enruta y normaliza. Si crece, algo esta mal ubicado.

---

[README](README.md) | Anterior: [01](01-architecture.md) | Siguiente: [03](03-controllers-and-models.md)
