"""@module shared.lambda_kit.http_dispatch — handler HTTP generico.

Concentra el adaptador HTTP que antes vivia duplicado en cada
`handler.py` de los Lambdas HTTP del backend. Define el CONTRATO uniforme:

- `operation` y `action` los provee el CLIENTE en cada request:
  - GET: `queryStringParameters['operation']` + `['action']`.
  - POST/PUT/PATCH: `body['operation']` + `body['action']`.
- El resto de los argumentos viajan por el mismo canal (query params o
  body) y los valida el modelo Pydantic del controller.

`extract_request` es una funcion pura sobre el evento API Gateway REST
proxy. `http_handler` envuelve el ciclo completo: extraer el contrato,
inyectar metadata de transporte (IP, country, user-agent), invocar el
controller via `run_controller` y traducir el resultado a una respuesta
HTTP.

`http_handler` NO conoce ningun dominio: las diferencias entre Lambdas
(CORS echo vs publico, status de exito, nombres de metricas) se expresan
por parametros, no por hardcodeos.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from aws_lambda_powertools.metrics import MetricUnit

from shared.core.exceptions import ApplicationError, ValidationError
from shared.core.types import JsonResponse
from shared.http.cors import public_cors_origin, resolve_origin
from shared.http.ip_extractor import (
    extract_cloudfront_meta,
    extract_country,
    extract_ip,
)
from shared.http.responses import (
    error_response,
    json_response,
    no_content_response,
)
from shared.lambda_kit.dispatch import run_controller
from shared.lambda_kit.validation.event import EventModelClass
from shared.observability.logger import logger
from shared.observability.metrics import metrics

# Metodos HTTP que llevan body (operation/action y data en el body JSON).
_BODY_METHODS = frozenset({'POST', 'PUT', 'PATCH'})


@dataclass
class ExtractedRequest:
    """Resultado de `extract_request`.

    Attributes
    ----------
    operation : str
        Nombre de la operacion del Lambda (ej. 'cv', 'contact', 'tracking').
    action : str
        Accion a ejecutar (ej. 'get', 'create', 'track').
    data : dict[str, Any]
        Resto de los argumentos del request (sin operation/action). Los
        valida el modelo Pydantic del controller.
    method : str
        Metodo HTTP de la request (GET, POST, ...).
    """

    operation: str
    action: str
    data: dict[str, Any] = field(default_factory=dict)
    method: str = 'GET'


def _method(event: dict[str, Any]) -> str:
    """Extrae el metodo HTTP del evento API Gateway REST proxy."""
    method = event.get('httpMethod') or ''
    return str(method).upper()


def _header(headers: dict[str, str], name: str) -> str | None:
    """Lookup case-insensitive de un header HTTP."""
    target = name.lower()
    return next(
        (v for k, v in headers.items() if k.lower() == target),
        None,
    )


def _query_params(event: dict[str, Any]) -> dict[str, str]:
    """Devuelve los query string parameters como dict de strings."""
    params = event.get('queryStringParameters') or {}
    # API Gateway REST proxy puede devolver None cuando no hay query.
    if not isinstance(params, dict):
        return {}
    # Los valores siempre son strings en API GW; tolerar None defensivamente.
    return {k: v for k, v in params.items() if v is not None}


def _parse_body(event: dict[str, Any]) -> dict[str, Any]:
    """Parsea el body JSON del evento. Lanza ValidationError si no es valido."""
    body_raw = event.get('body') or ''
    if not body_raw:
        return {}
    try:
        parsed = json.loads(body_raw)
    except json.JSONDecodeError as exc:
        msg = 'Invalid JSON body'
        raise ValidationError(msg, code='INVALID_JSON') from exc
    if not isinstance(parsed, dict):
        msg = 'Invalid JSON body'
        raise ValidationError(msg, code='INVALID_JSON')
    return parsed


def extract_request(event: dict[str, Any]) -> ExtractedRequest:
    """Extrae el contrato `{operation, action, data}` del evento API GW.

    Reglas:
    - GET: `operation`/`action` y resto de args en `queryStringParameters`.
    - POST/PUT/PATCH: `operation`/`action` y resto de campos en el body JSON.
    - Otro metodo (DELETE, ...): se trata como POST (body) para uniformidad.
    - Si falta `operation` o `action` -> `ValidationError(INVALID_REQUEST)`.
    - Si el body no es JSON valido (en metodos con body) -> `INVALID_JSON`.

    Parameters
    ----------
    event : dict[str, Any]
        Evento crudo de API Gateway REST proxy.

    Returns
    -------
    ExtractedRequest
        El operation, action, data y method resueltos.

    Raises
    ------
    ValidationError
        `INVALID_REQUEST` si falta operation/action, `INVALID_JSON` si el
        body no es JSON valido.
    """
    method = _method(event)
    params = _query_params(event) if method == 'GET' else _parse_body(event)

    operation = params.get('operation')
    action = params.get('action')

    if not operation or not isinstance(operation, str):
        msg = 'Missing or invalid operation'
        raise ValidationError(msg, code='INVALID_REQUEST')
    if not action or not isinstance(action, str):
        msg = 'Missing or invalid action'
        raise ValidationError(msg, code='INVALID_REQUEST')

    # data = todos los campos restantes (sin operation/action).
    data = {k: v for k, v in params.items() if k not in ('operation', 'action')}

    return ExtractedRequest(
        operation=operation.strip(),
        action=action.strip(),
        data=data,
        method=method or 'GET',
    )


def _resolve_origin_value(
    headers: dict[str, str],
    cors_origin: str,
) -> str:
    """Resuelve el Origin a usar para el header CORS.

    `'echo'` -> `resolve_origin(headers)` (echo del Origin matcheado).
    `'public'` -> `public_cors_origin()` (`'*'`).
    Cualquier otro valor literal se devuelve tal cual (uso avanzado).
    """
    if cors_origin == 'echo':
        return resolve_origin(headers)
    if cors_origin == 'public':
        return public_cors_origin()
    return cors_origin


def http_handler(
    event: dict[str, Any],
    *,
    event_model: EventModelClass,
    cors_origin: str = 'echo',
    success_status: int = 200,
    metric_names: dict[str, str] | None = None,
) -> JsonResponse:
    """Envuelve el ciclo completo de un Lambda HTTP del backend.

    Reemplaza el cuerpo del `lambda_handler` de cada Lambda HTTP:
    1. resuelve el origin CORS y extrae metadata de transporte;
    2. `extract_request(event)` -> `(operation, action, data, method)`;
    3. inyecta `data['_meta']` con `ip/country/user_agent/bypass_token`;
    4. invoca `run_controller(synthetic_event, event_model)`;
    5. traduce el `DispatchResult` a una respuesta HTTP.

    Parameters
    ----------
    event : dict[str, Any]
        Evento crudo de API Gateway REST proxy.
    event_model : EventModelClass
        Clase `EventModel` del Lambda (de `build_event_model(OPERATIONS)`).
    cors_origin : str
        `'echo'` (refleja el Origin matcheado, default; usalo para contact
        form) o `'public'` (`'*'`; usalo para tracking pixel via sendBeacon
        ping o APIs publicas como `cv`). Cualquier otro valor se usa tal
        cual.
    success_status : int
        Codigo HTTP de exito (200, 201, 204). Para `204` no se serializa el
        body (`no_content_response`).
    metric_names : dict[str, str] | None
        Mapeo opcional `{submitted, rejected, error}` -> nombres de metricas
        CloudWatch a emitir. Si es None, no se emiten metricas.

    Returns
    -------
    JsonResponse
        Respuesta lista para API Gateway REST proxy.
    """
    headers = event.get('headers') or {}
    origin = _resolve_origin_value(headers, cors_origin)
    # Origin header raw del request (sin echo / public translation).
    # Lo usan los modelos Pydantic que necesitan inferir niche del
    # subdominio (spec sessions-normalize: contact_form/niche fallback).
    raw_origin = _header(headers, 'origin')
    ip = extract_ip(event)
    country = extract_country(event)
    user_agent = _header(headers, 'user-agent')
    bypass_token = _header(headers, 'x-turnstile-bypass-token')
    # Authorization header (Bearer <access JWT>): lo consumen los
    # endpoints autenticados (ej. mfa.*, webauthn.* del plan 02) via
    # `require_active_user`. Los modelos `_Meta` lo ignoran si no aplica.
    authorization = _header(headers, 'authorization')
    # cloudfront_meta: TODOS los headers cloudfront-* del request, en
    # lowercase canonico. Cuando el custom domain es Edge-Optimized
    # llegan ~22 headers (geo/device/tls/asn/ja3). Vacio si REGIONAL.
    cloudfront_meta = extract_cloudfront_meta(event)

    metric_names = metric_names or {}

    try:
        # 1. Extraer operation/action/data del request.
        extracted = extract_request(event)

        # 2. Inyectar metadata de transporte en data._meta (lo consume el
        #    modelo Pydantic del controller cuando lo necesita).
        synthetic_event = {
            'operation': extracted.operation,
            'action': extracted.action,
            'data': {
                **extracted.data,
                '_meta': {
                    'ip': ip,
                    'country': country,
                    'user_agent': user_agent,
                    'bypass_token': bypass_token,
                    'cloudfront_meta': cloudfront_meta,
                    'origin': raw_origin,
                    'authorization': authorization,
                },
            },
        }

        # 3. Validar evento + resolver controller + ejecutar.
        result = run_controller(synthetic_event, event_model)

        # 4. Fallo de resolucion del evento (operation/action invalida).
        if result.stage == 'validation':
            logger.warning(
                'http_handler: validation failed',
                extra={
                    'operation': extracted.operation,
                    'action': extracted.action,
                    'detail': result.data,
                },
            )
            # NO emitir la metrica 'error' aqui: ValidationError es una
            # ApplicationError, asi que el `except ApplicationError` de abajo
            # emite 'rejected' (el contador correcto para un 4xx de cliente).
            # Emitir 'error' aqui ademas duplicaba la metrica por request.
            # La metrica 'error' queda reservada para los 5xx reales (el
            # `except Exception` final).
            raise ValidationError(
                'Validation failed',
                code='INVALID_REQUEST',
                extra={'detail': result.data},
            )

        # 5. Controller ejecuto pero devolvio is_valid=False (puede ser
        #    una ApplicationError de negocio embebida en data).
        if not result.is_valid:
            app_error = result.data.get('application_error') if isinstance(
                result.data, dict
            ) else None
            if isinstance(app_error, ApplicationError):
                raise app_error
            # Si el controller pidio un status HTTP explicito (404, 409,
            # 423, 429, 401, ...), se respeta y se devuelve el `data` del
            # controller tal cual (sin envolver en INVALID_REQUEST). Es
            # la via para errores de negocio con status especifico sin
            # construir una ApplicationError. Para 429 se agrega
            # Retry-After si el data trae `retry_after`.
            if result.status is not None:
                if 'rejected' in metric_names:
                    metrics.add_metric(
                        name=metric_names['rejected'],
                        unit=MetricUnit.Count,
                        value=1,
                    )
                extra_headers: dict[str, str] = {}
                retry_after = (
                    result.data.get('retry_after')
                    if isinstance(result.data, dict)
                    else None
                )
                if result.status == 429 and retry_after is not None:
                    extra_headers['Retry-After'] = str(retry_after)
                return json_response(
                    result.status,
                    result.data,
                    origin=origin,
                    extra_headers=extra_headers or None,
                )
            raise ValidationError(
                'Validation failed',
                code='INVALID_REQUEST',
                extra={'detail': result.data},
            )

        # 6. Exito. El controller puede pedir un status explicito (ej.
        #    204 en session.logout); si no, usa el `success_status` del
        #    handler.
        if 'submitted' in metric_names:
            metrics.add_metric(
                name=metric_names['submitted'],
                unit=MetricUnit.Count,
                value=1,
            )

        effective_status = result.status or success_status
        if effective_status == 204:
            return no_content_response(origin=origin)
        return json_response(effective_status, result.data, origin=origin)

    except ApplicationError as exc:
        logger.warning(
            'http_handler: request rejected',
            extra={'code': exc.code, 'reason': exc.message, 'ip': ip},
        )
        if 'rejected' in metric_names:
            metrics.add_metric(
                name=metric_names['rejected'],
                unit=MetricUnit.Count,
                value=1,
            )
        return error_response(exc, origin=origin)

    except Exception:
        logger.exception('http_handler: unhandled error')
        if 'error' in metric_names:
            metrics.add_metric(
                name=metric_names['error'],
                unit=MetricUnit.Count,
                value=1,
            )
        return error_response(Exception('internal'), origin=origin)
