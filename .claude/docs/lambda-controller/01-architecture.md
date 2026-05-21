# 01 - Arquitectura

> [README](README.md) | Siguiente: [02 - Handler y routing](02-handler-and-routing.md)

## Que problema resuelve

Un servicio Lambda suele atender varias operaciones discretas (crear un
recurso, verificar su estado, cancelarlo, ...). Sin estructura, todo
termina en un `handler.py` gigante con `if event['action'] == ...`.

Este patron descompone el Lambda en capas: el evento declara
`operation` (que dominio) y `action` (que hacer); el handler resuelve
dinamicamente la clase controller correcta, que valida su payload,
delega la logica de negocio a un service y normaliza la respuesta.

Agregar una operacion = crear archivos nuevos, sin tocar el handler.

## Las capas

```text
core/
├── handler.py     Router delgado. Resuelve operation+action -> controller.
├── controllers/   Orquestadores. Un paquete por operation.
├── services/      Logica de negocio del lambda.
├── models/        Validacion de estructura con Pydantic.
├── settings/      Configuracion (AppConfig), enums, mapa OPERATIONS.
└── utils/         Infraestructura generica: BaseController, BaseSettings,
                   import_controller, logger, invoker.
```

| Capa | Responsabilidad | NO debe |
|------|-----------------|---------|
| `handler.py` | Enrutar el evento a un controller | Tener logica de negocio |
| `controllers/` | Orquestar: validar -> service -> normalizar | Tener logica de negocio |
| `services/` | Logica de negocio del lambda | Conocer el evento Lambda |
| `models/` | Validacion de estructura (Pydantic) | Tener logica de negocio |
| `settings/` | Config, enums, mapa de operaciones | Importar controllers |
| `utils/` | Infraestructura reutilizable | Conocer el dominio |

## operation + action: el contrato del evento

El evento de entrada SIEMPRE tiene esta forma:

```jsonc
{
  "operation": "<dominio>",   // ej. "payments", "users"
  "action": "<verbo>",        // ej. "create", "check"
  "data": { ... }             // payload especifico de operation/action
}
```

- `operation` se resuelve via el dict `OPERATIONS` (en
  `settings/operations.py`) a una **carpeta de controller**. Varios
  codenames de `operation` pueden mapear al mismo controller (alias).
- `action` se mapea a un **archivo** (`<action>.py`) y a una **clase**
  (`<Action>` = `action.capitalize()`) dentro de esa carpeta.

Ejemplo: `operation="payments"`, `action="create"` resuelve
`controllers/payments/create.py` -> clase `Create`.

## Ciclo de vida de un controller: preload -> validate -> execute

`BaseController.run()` ejecuta tres fases, cada una con logging:

1. **preload** - prepara configuracion previa. Por defecto resuelve el
   ARN de un Lambda downstream desde `AppConfig` usando `arn_config_key`.
   Si el controller no invoca otro Lambda, `arn_config_key = ''` y la
   fase es un no-op.
2. **validate** - valida el `data` del evento contra el modelo Pydantic
   declarado en `event_model`. Deja el resultado en `self.validated_data`.
3. **execute** - unico metodo abstracto. Orquesta la operacion: extrae
   los datos validados, llama al **service** y normaliza el resultado.

Si una fase falla, `run()` corta y devuelve el error sin llegar a
`execute()`.

## Contrato de retorno: {is_valid, data, code}

Toda funcion del flujo (fases, `execute`, el handler) devuelve un dict
con la misma forma:

```python
# exito
{'is_valid': True, 'data': {...}, 'code': 0}

# error
{'is_valid': False, 'data': {'error_code': '...', 'message': '...'},
 'code': <int>}
```

Rangos de `code` (ver `ErrorCode` en `settings/config.py`):

| Rango | Significado |
|-------|-------------|
| `0` | Exito |
| `1000-1999` | Errores de validacion |
| `2000-2999` | Errores de configuracion |
| `4000-4999` | Errores de logica de negocio |
| `5000-5999` | Errores de API / servicios externos |
| `6000+` | Errores de sistema / inesperados |

El handler colapsa estos rangos a un codigo de salida estable
(`1000` / `2000` / `5100` / `6000`) en la respuesta final del Lambda.

## Descubrimiento por convencion, no por registro

No hay un registro manual de controllers. `import_controller`
(`utils/import_controller.py`) los descubre por convencion:

```text
operation --(OPERATIONS)--> controller folder
action    -------------- > <action>.py + clase <Action>
=> import_module('controllers.<folder>.<action>') -> getattr(mod, '<Action>')
```

Ademas valida que la clase herede de `BaseController`. Esto hace que
agregar una operacion sea puramente declarativo: crear los archivos +
una entrada en `OPERATIONS`.

## Origen del patron

Este formato esta basado en el servicio real `payment_router`
(legolambda-stacks), generalizado: el `bifrost.logger` y
`bifrost.connection_aws` propietarios se reemplazaron por
`utils/logger.py` y `utils/invoker.py` autocontenidos, y se extrajo la
capa `services/` para separar la logica de negocio de la orquestacion.

---

[README](README.md) | Siguiente: [02 - Handler y routing](02-handler-and-routing.md)
