"""Lambda `contact_form` — endpoint HTTP `POST /contact`.

Entrypoint del Lambda. Router delgado: traduce el evento HTTP de API
Gateway (REST proxy) al contrato del estandar lambda-controller
`{operation, action, data}`, resuelve el controller `contact/create` y
devuelve una respuesta HTTP para API Gateway.

El Handler de la funcion AWS es `core.handler.lambda_handler`.

Flujo:
  1. Parsear el body JSON del evento HTTP.
  2. Extraer la metadata de transporte de los headers (IP, country,
     user-agent, bypass-secret) y resolver el origin para el echo CORS.
  3. Sintetizar el evento `{operation: 'contact', action: 'create',
     data: <body + _meta>}`.
  4. Validar el evento + resolver el controller (`validate_event`).
  5. Ejecutar el controller (`preload -> validate -> execute`).
  6. Devolver HTTP 201 con el `contact_id`, o `error_response` en error.

Sobre la metadata de transporte: el rate-limit y la verificacion
Turnstile que orquesta el controller necesitan datos del evento HTTP
(IP, country, user-agent, bypass-secret) que NO son campos del form. El
handler los empaqueta en `data._meta`; `ContactCreateModel` (modelo
Pydantic) los valida como un sub-objeto `RequestMeta`. Asi el controller
recibe TODO via el evento sintetico, sin tocar el evento Lambda crudo.

El comportamiento observable (HTTP 201 con `contact_id` en exito, el
`error_response` del backend en error, los headers CORS, las metricas
`ContactFormSubmitted/Rejected/Error`) es IDENTICO al Lambda plano que
este modulo reemplaza.
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

from typing import Any

from aws_lambda_powertools.metrics import MetricUnit
from settings.operations import OPERATIONS
from utils.validation.event import validate_event

from shared.core.exceptions import ApplicationError, ValidationError
from shared.http.cors import resolve_origin
from shared.http.ip_extractor import extract_country, extract_ip
from shared.http.responses import error_response, json_response
from shared.observability.logger import logger
from shared.observability.metrics import metrics
from shared.observability.tracer import tracer

__version__ = '2.0.0'


def _header(headers: dict[str, str], name: str) -> str | None:
    """Lookup case-insensitive de un header HTTP."""
    target = name.lower()
    return next(
        (v for k, v in headers.items() if k.lower() == target),
        None,
    )


@logger.inject_lambda_context(
    log_event=False, correlation_id_path='requestContext.requestId'
)
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Entrypoint Lambda contact_form (POST /contact)."""
    headers = event.get('headers') or {}
    origin = resolve_origin(headers)
    ip = extract_ip(event)
    country = extract_country(event)
    user_agent = _header(headers, 'user-agent')
    bypass_secret = _header(headers, 'x-turnstile-bypass-secret')

    try:
        # --- 1. Parsear el body JSON ---
        body_raw = event.get('body') or ''
        try:
            body_dict = json.loads(body_raw) if body_raw else {}
        except json.JSONDecodeError as exc:
            msg = 'Invalid JSON body'
            raise ValidationError(msg, code='INVALID_JSON') from exc

        if not isinstance(body_dict, dict):
            msg = 'Invalid JSON body'
            raise ValidationError(msg, code='INVALID_JSON')

        # --- 2. Sintetizar el evento {operation, action, data} ---
        # data = campos del form + _meta (metadata de transporte que el
        # controller necesita para rate-limit y Turnstile).
        synthetic_event = {
            'operation': 'contact',
            'action': 'create',
            'data': {
                **body_dict,
                '_meta': {
                    'ip': ip,
                    'country': country,
                    'user_agent': user_agent,
                    'bypass_secret': bypass_secret,
                },
            },
        }

        # --- 3. Validar evento + resolver controller ---
        validation_result = validate_event(synthetic_event)
        if not validation_result.get('is_valid'):
            # El evento sintetico siempre tiene operation/action/data; un
            # fallo aqui es defensivo (controller mal registrado).
            logger.error(
                'synthetic event validation failed',
                extra={'detail': validation_result.get('message')},
            )
            metrics.add_metric(
                name='ContactFormError', unit=MetricUnit.Count, value=1
            )
            return error_response(Exception('internal'), origin=origin)

        validated_event = validation_result['data']
        controller_data = validated_event.controller_info.get('data', {})
        controller_class = controller_data.get('controller_class')

        # --- 4. Ejecutar el controller (preload -> validate -> execute) ---
        instance = controller_class(event=validated_event.controller_event)
        result = instance.run()

        if not result.get('is_valid'):
            # El payload no paso la validacion Pydantic del modelo.
            raise ValidationError(
                'Validation failed',
                code='INVALID_INPUT',
                extra={'detail': result.get('data', {})},
            )

        # --- 5. Respuesta 201 con el contact_id ---
        metrics.add_metric(
            name='ContactFormSubmitted', unit=MetricUnit.Count, value=1
        )
        return json_response(201, result['data'], origin=origin)

    except ApplicationError as exc:
        logger.warning(
            'contact form rejected',
            extra={'code': exc.code, 'reason': exc.message, 'ip': ip},
        )
        metrics.add_metric(
            name='ContactFormRejected', unit=MetricUnit.Count, value=1
        )
        return error_response(exc, origin=origin)

    except Exception:
        logger.exception('unhandled error in contact_form')
        metrics.add_metric(
            name='ContactFormError', unit=MetricUnit.Count, value=1
        )
        return error_response(Exception('internal'), origin=origin)


# OPERATIONS se importa para forzar el registro de la operacion `contact`
# (descubrimiento por convencion); referenciado para evitar F401.
_ = OPERATIONS
