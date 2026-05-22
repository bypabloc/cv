# 03 — Fase B: migrar `contact_form` + `tracking_pixel` al handler generico

[<- 02 Fase A](02-fase-http-kit.md) | [Siguiente: Fase C ->](04-fase-servicio-cv.md)

## Objetivo

Reemplazar el cuerpo hardcodeado del `lambda_handler` de `contact_form` y
`tracking_pixel` por una delegacion a `http_handler`. Tras esta fase ningun
Lambda HTTP hardcodea `operation`/`action`: vienen del request.

Depende de la Fase A. No depende del seed.

## Cambio de contrato (IMPORTANTE)

Hoy los handlers hardcodean `operation`/`action`. Tras el refactor el cliente
debe enviarlos:

- **`contact_form`** (`POST /contact`): el body JSON debe incluir
  `operation: 'contact'` y `action: 'create'` ademas de los campos del form.
- **`tracking_pixel`** (`POST /track`): el body JSON debe incluir
  `operation: 'tracking'` y `action: 'track'` ademas del evento.

Esto obliga a actualizar el frontend que llama a esos endpoints (componentes
Astro del form de contacto y del tracking pixel). Ver "Archivos afectados —
frontend" en [06-archivos-afectados.md](06-archivos-afectados.md).

> El comportamiento OBSERVABLE de la respuesta no cambia (mismos HTTP status
> 201/204, mismo CORS, mismas metricas). Lo unico que cambia es el shape del
> request de entrada. El AC-7 verifica que el form sigue respondiendo 201.

## Que se modifica

### `services/contact_form/core/handler.py`

El `lambda_handler` pasa de ~85 lineas a una delegacion:

```text
lambda_handler(event, context):
    return http_handler(
        event,
        event_model=_EVENT_MODEL,
        cors_origin='echo',
        success_status=201,
        metric_names={
            'submitted': 'ContactFormSubmitted',
            'rejected':  'ContactFormRejected',
            'error':     'ContactFormError',
        },
    )
```

Los decoradores Powertools (`@logger.inject_lambda_context`, `@tracer`,
`@metrics.log_metrics`) se quedan en el `handler.py` del Lambda.

El `_meta` que hoy el handler arma a mano (`ip`, `country`, `user_agent`,
`bypass_secret`) lo inyecta `http_handler`. El controller `contact/create` y
su modelo `ContactCreateModel` NO cambian — siguen leyendo `data._meta`.

### `services/tracking_pixel/core/handler.py`

Misma delegacion con `cors_origin='public'`, `success_status=204`,
`metric_names` de tracking. El controller y el modelo de tracking NO cambian.

### Tests de ambos Lambdas

- Los tests unit que hoy construyen el evento API Gateway deben incluir
  `operation`/`action` en el body (nuevo contrato).
- Los tests de integration E2E (`test_*_e2e.py`) deben mandar el body con
  `operation`/`action`.
- Verificar que NO hay regresion de comportamiento: mismos status, mismo
  CORS, mismas metricas.

## Verificacion de la fase

```bash
python devtools/run.py serverless tests --type=unit --lambda=contact_form
python devtools/run.py serverless tests --type=unit --lambda=tracking_pixel
python devtools/run.py serverless tests --type=coverage --lambda=contact_form
python devtools/run.py serverless tests --type=coverage --lambda=tracking_pixel
# E2E (requiere stack/recursos): contra dev tras deploy, o branch de prueba
python devtools/run.py serverless tests --type=integration --lambda=contact_form
python devtools/run.py serverless tests --type=integration --lambda=tracking_pixel
```

Criterio: suites verdes, coverage >= 80% per-file, cero regresion E2E.

## Done

- [ ] `contact_form/core/handler.py` delega en `http_handler`
- [ ] `tracking_pixel/core/handler.py` delega en `http_handler`
- [ ] tests unit de ambos Lambdas ajustados al nuevo contrato y verdes
- [ ] tests integration E2E verdes (sin regresion de status/CORS/metricas)
- [ ] frontend del form + tracking actualizado para enviar operation/action
- [ ] coverage >= 80% per-file en los handlers modificados

Continua en [04-fase-servicio-cv.md](04-fase-servicio-cv.md).
