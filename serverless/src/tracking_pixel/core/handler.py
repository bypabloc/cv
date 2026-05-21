"""Lambda `tracking_pixel` — registro de eventos de tracking (POST /track).

Entrypoint del Lambda. Router delgado: traduce el evento HTTP de API
Gateway REST proxy al contrato del estandar lambda-controller
`{operation, action, data}`, resuelve el controller y traduce el
resultado normalizado a una respuesta HTTP.

Diferencias vs contact_form:
  - No Turnstile estricto (best-effort, no enforced).
  - Sin SES email.
  - Respuesta HTTP 204 No Content en exito (fire-and-forget).
  - Rate-limit mas laxo (30/min vs 3/min en contact).

Sintesis del evento: tracking_pixel atiende UNA sola operacion/accion:
`operation='tracking'`, `action='track'`. El evento real es API Gateway
REST proxy (`{body, headers, requestContext, ...}`). El handler:
  1. parsea el body JSON del POST.
  2. extrae IP / country / user-agent del evento HTTP.
  3. sintetiza `{operation, action, data}` donde `data` es el body
     parseado mas una clave `meta` con la IP / country / user-agent
     (el controller necesita esos datos para el rate-limit + enrichment;
     viajan dentro de `data` para que el modelo Pydantic los valide en un
     solo objeto, sin un segundo canal paralelo).
  4. valida el evento via `validate_event` y ejecuta el controller.

La RESPUESTA es HTTP 204 No Content en exito (`no_content_response`) y
`error_response` en error — comportamiento IDENTICO al handler original.
El CORS usa `public_cors_origin()` (`'*'`), NO el echo: /track lo invoca
`navigator.sendBeacon` (modo `ping`), que exige `Allow-Origin: '*'`.

El Handler de la funcion AWS es `core.handler.lambda_handler`.
"""

from __future__ import annotations

import json
import os
import sys

# El handler vive dentro de core/. Agregamos core/ al sys.path para que
# los imports absolutos (models., services., settings., utils., shared.)
# resuelvan en AWS y en invoke local. shared/ se vendoriza en core/shared/.
_CORE_DIR = os.path.dirname(os.path.abspath(__file__))
if _CORE_DIR not in sys.path:
    sys.path.insert(0, _CORE_DIR)

from typing import Any  # noqa: E402

from aws_lambda_powertools.metrics import MetricUnit  # noqa: E402

from settings.operations import OPERATIONS  # noqa: E402
from shared.cors import public_cors_origin  # noqa: E402
from shared.exceptions import ApplicationError, ValidationError  # noqa: E402
from shared.ip_extractor import extract_country, extract_ip  # noqa: E402
from shared.logger import logger  # noqa: E402
from shared.metrics import metrics  # noqa: E402
from shared.responses import error_response, no_content_response  # noqa: E402
from shared.tracer import tracer  # noqa: E402
from utils.validation.event import validate_event  # noqa: E402

__version__ = '2.0.0'


def _parse_body(event: dict[str, Any]) -> dict[str, Any]:
    """Parsea el body JSON del POST. Lanza ValidationError si es invalido."""
    body_raw = event.get('body') or ''
    try:
        return json.loads(body_raw) if body_raw else {}
    except json.JSONDecodeError as exc:
        msg = 'Invalid JSON body'
        raise ValidationError(msg, code='INVALID_JSON') from exc


def _user_agent(headers: dict[str, str]) -> str | None:
    """Extrae el header User-Agent (lookup case-insensitive)."""
    return next(
        (v for k, v in headers.items() if k.lower() == 'user-agent'),
        None,
    )


@logger.inject_lambda_context(
    log_event=False, correlation_id_path='requestContext.requestId'
)
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Traduce el evento API GW a {operation, action, data} y enruta."""
    headers = event.get('headers') or {}
    # /track lo invoca navigator.sendBeacon (modo `ping`), que exige
    # Access-Control-Allow-Origin: '*' literal. Un echo del Origin hace
    # fallar la request con CORS error. /track es tracking anonimo sin
    # credenciales, asi que '*' es correcto (ver shared.cors).
    origin = public_cors_origin()
    ip = extract_ip(event)
    country = extract_country(event)
    user_agent = _user_agent(headers)

    try:
        # 1. Parse body
        body_dict = _parse_body(event)

        # 2. Sintetizar el evento estandar {operation, action, data}.
        #    `data` = body parseado + `meta` (contexto HTTP). El modelo
        #    Pydantic TrackEventModel valida ambos en un solo objeto.
        synthetic_event = {
            'operation': 'tracking',
            'action': 'track',
            'data': {
                **body_dict,
                'meta': {
                    'ip': ip,
                    'country': country,
                    'user_agent': user_agent,
                },
            },
        }

        # 3. Validar evento + resolver controller (operation + action)
        validation_result = validate_event(synthetic_event)
        if not validation_result.get('is_valid'):
            raise ValidationError(
                'Validation failed',
                code='INVALID_INPUT',
            )

        validated_event = validation_result['data']
        controller_data = validated_event.controller_info.get('data', {})
        controller_class = controller_data.get('controller_class')

        # 4. Ejecutar el controller (preload -> validate -> execute)
        instance = controller_class(event=validated_event.controller_event)
        result = instance.run()

        # 5. El controller normaliza {is_valid, data, code}. Un is_valid
        #    False lo provoca una validacion fallida del payload (modelo
        #    Pydantic) o el rate-limit. Se traduce a la respuesta HTTP.
        if not result.get('is_valid'):
            result_data = result.get('data', {})
            app_error = result_data.get('application_error')
            if isinstance(app_error, ApplicationError):
                raise app_error
            raise ValidationError(
                'Validation failed',
                code='INVALID_INPUT',
            )

        # 6. Metrics + 204 No Content (fire-and-forget)
        metrics.add_metric(
            name='TrackingEventReceived', unit=MetricUnit.Count, value=1
        )
        return no_content_response(origin=origin)

    except ApplicationError as exc:
        logger.warning(
            'tracking event rejected',
            extra={'code': exc.code, 'reason': exc.message, 'ip': ip},
        )
        metrics.add_metric(
            name='TrackingEventRejected', unit=MetricUnit.Count, value=1
        )
        return error_response(exc, origin=origin)

    except Exception:
        logger.exception('unhandled error in tracking_pixel')
        metrics.add_metric(
            name='TrackingEventError', unit=MetricUnit.Count, value=1
        )
        return error_response(Exception('internal'), origin=origin)


# OPERATIONS se importa para forzar el registro de la operacion
# `tracking` (descubrimiento por convencion); referenciado para evitar F401.
_ = OPERATIONS
