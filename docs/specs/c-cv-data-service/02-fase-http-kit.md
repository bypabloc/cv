# 02 — Fase A: handler HTTP generico en `shared.lambda_kit`

[<- 01 Contexto](01-contexto-y-decision.md) | [Siguiente: Fase B ->](03-fase-migracion-handlers.md)

## Objetivo

Concentrar en `shared.lambda_kit` el adaptador HTTP que hoy esta duplicado y
hardcodeado en cada `handler.py`. Tras esta fase, un Lambda HTTP nuevo no
reescribe el parsing de `operation`/`action`/`data`.

Esta fase NO depende del seed de la DB — puede arrancar de inmediato.

## Que se construye

### `shared/lambda_kit/http_dispatch.py` (NUEVO)

Dos piezas, ambas funciones puras / sin estado de Lambda concreto:

#### `extract_request(event) -> ExtractedRequest`

Funcion pura. Dado un evento API Gateway REST proxy, resuelve el contrato
`{operation, action, data}` segun el metodo HTTP:

```text
metodo == GET:
    operation = queryStringParameters['operation']
    action    = queryStringParameters['action']
    data      = { resto de queryStringParameters }   # sin operation/action

metodo en (POST, PUT, PATCH):
    body = json.loads(event['body'])
    operation = body['operation']
    action    = body['action']
    data      = { resto del body }                   # sin operation/action
```

Reglas:

- Si falta `operation` o `action` -> levanta `ValidationError` del backend
  (`shared.core.exceptions`) con `code='INVALID_REQUEST'` (AC-3).
- Si el metodo es GET y no hay `queryStringParameters` -> mismo error.
- Si el metodo es POST y el body no es JSON valido -> `ValidationError`
  `code='INVALID_JSON'`.
- `queryStringParameters` de API Gateway son SIEMPRE strings; el casteo a
  tipos lo hace el modelo Pydantic del controller (`int`, `bool`, etc.). NO
  castear en `extract_request`.
- Devuelve un dataclass `ExtractedRequest(operation, action, data, method)`.

#### `http_handler(event, *, event_model, cors_origin, metrics_hooks=None) -> dict`

Envuelve el ciclo completo del handler HTTP. Reemplaza el cuerpo del
`lambda_handler` de cada Lambda:

```text
1. resolver origin CORS (echo o '*' segun cors_origin)
2. extract_request(event) -> (operation, action, data, method)
3. inyectar data['_meta'] = { ip, country, user_agent, bypass_secret }
   (extraidos de headers/requestContext del evento)
4. synthetic_event = { operation, action, data }
5. run_controller(synthetic_event, event_model) -> DispatchResult
6. traducir DispatchResult a respuesta HTTP:
     - exito         -> success_response(result.data)  [status configurable]
     - validation    -> error_response(ValidationError(INVALID_REQUEST))
     - ApplicationError en data -> error_response(app_error)
7. devolver la respuesta de API Gateway
```

Parametros configurables (para cubrir las diferencias entre Lambdas sin
hardcodear):

- `event_model` — la clase `EventModel` del Lambda (de `build_event_model`).
- `cors_origin` — `'echo'` (refleja el Origin, como `contact_form`) o
  `'public'` (`'*'`, como `tracking_pixel`).
- `success_status` — `200` (default, para `cv`), `201` (`contact_form`),
  `204` (`tracking_pixel`, sin body).
- `metric_names` — dict opcional `{submitted, rejected, error}` para emitir
  las metricas CloudWatch que hoy cada handler emite a mano.

`http_handler` NO conoce ningun dominio: es generico. Toda la diferencia
entre Lambdas se expresa por estos parametros.

### `shared/lambda_kit/__init__.py` (MODIFICAR)

Re-exportar `extract_request`, `http_handler`, `ExtractedRequest`.

## Tests (TDD — escribir primero)

Estandar de testing lambda-controller: un archivo por escenario en
`serverless/lambda/shared/tests/unit/lambda_kit/`.

| Archivo | Escenario |
|---------|-----------|
| `test_extract_request_get_returns_operation_action_data.py` | AC-1 |
| `test_extract_request_post_returns_operation_action_data.py` | AC-2 |
| `test_extract_request_get_without_operation_raises.py` | AC-3 |
| `test_extract_request_post_invalid_json_raises.py` | INVALID_JSON |
| `test_extract_request_strips_operation_action_from_data.py` | data limpio |
| `test_http_handler_success_returns_configured_status.py` | success_status |
| `test_http_handler_missing_operation_returns_400.py` | AC-3 end-to-end |
| `test_http_handler_injects_meta_from_headers.py` | `_meta` inyectado |
| `test_http_handler_application_error_maps_to_http.py` | ApplicationError |

Asserts EXACTOS (`== valor`). Mockear solo E/S externa; NUNCA el
`run_controller` propio (se prueba con un `EventModel` y un controller fake
minimo definido en `_helpers.py`).

## Verificacion de la fase

```bash
python devtools/run.py serverless tests --type=unit --shared
python devtools/run.py serverless tests --type=coverage --shared
```

Criterio: suite verde, coverage >= 80% per-file en `http_dispatch.py`.

## Done

- [ ] `http_dispatch.py` creado con `extract_request` + `http_handler`
- [ ] `__init__.py` re-exporta las piezas nuevas
- [ ] 9 archivos de test, un escenario cada uno, todos verdes
- [ ] coverage >= 80% en `http_dispatch.py`
- [ ] `serverless lint-deps --shared` sin nuevas deps no declaradas

Continua en [03-fase-migracion-handlers.md](03-fase-migracion-handlers.md).
