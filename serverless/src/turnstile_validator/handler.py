"""
Lambda handler: POST /validate-turnstile

Endpoint interno para validar tokens Cloudflare Turnstile sin persistir nada.
Util para flujos en multiples pasos donde el validate ocurre antes que el
save (ej: validar al type del email, no al submit completo del form).

Reutiliza la funcion verify_turnstile_token de contact_form/turnstile.py.
"""

from __future__ import annotations

import json
from typing import Any

from aws_lambda_powertools.metrics import MetricUnit
from pydantic import BaseModel, Field
from pydantic import ValidationError as PydanticValidationError

from common.cors import resolve_origin
from common.exceptions import ApplicationError, ValidationError
from common.ip_extractor import extract_ip
from common.logger import logger
from common.metrics import metrics
from common.rate_limit import check_or_raise
from common.responses import error_response, json_response
from common.tracer import tracer

# Reutilizamos la funcion del contact_form module (Lambda comparte common
# pero contact_form NO esta en el deploy zip de turnstile_validator).
# Para evitar acoplamiento, copiamos solo la funcion verify aqui en service.
from turnstile_validator.service import verify_token_only


class ValidateTokenInput(BaseModel):
    """Body schema POST /validate-turnstile."""

    cf_token: str = Field(..., min_length=20, max_length=2048)
    action: str | None = Field(default=None, max_length=100)


class ValidateTokenOutput(BaseModel):
    """Respuesta 200 si el token es valido."""

    valid: bool
    hostname: str
    challenge_ts: str | None = None


@logger.inject_lambda_context(log_event=False, correlation_id_path='requestContext.requestId')
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Entry point Lambda turnstile_validator."""
    headers = event.get('headers') or {}
    origin = resolve_origin(headers)
    ip = extract_ip(event)
    bypass_secret = next(
        (v for k, v in headers.items() if k.lower() == 'x-turnstile-bypass-secret'),
        None,
    )

    try:
        body_raw = event.get('body') or ''
        try:
            body_dict = json.loads(body_raw) if body_raw else {}
        except json.JSONDecodeError as e:
            msg = 'Invalid JSON body'
            raise ValidationError(msg, code='INVALID_JSON') from e

        try:
            parsed = ValidateTokenInput(**body_dict)
        except PydanticValidationError as e:
            raise ValidationError(
                'Validation failed',
                code='INVALID_INPUT',
                extra={'errors': e.errors(include_url=False)},
            ) from e

        # Rate-limit estricto (5/min) por ser endpoint reusable
        check_or_raise(
            ip=ip,
            endpoint='/validate-turnstile',
            country=None,
            turnstile_validated=False,
        )

        result = verify_token_only(
            parsed.cf_token,
            remote_ip=ip,
            bypass_secret=bypass_secret,
        )

        metrics.add_metric(name='TurnstileValidated', unit=MetricUnit.Count, value=1)

        output = ValidateTokenOutput(
            valid=True,
            hostname=result.get('hostname', ''),
            challenge_ts=result.get('challenge_ts'),
        )
        return json_response(200, output.model_dump(), origin=origin)

    except ApplicationError as e:
        logger.warning(
            'turnstile validation rejected',
            extra={'code': e.code, 'reason': e.message, 'ip': ip},
        )
        metrics.add_metric(name='TurnstileRejected', unit=MetricUnit.Count, value=1)
        return error_response(e, origin=origin)

    except Exception:
        logger.exception('unhandled error in turnstile_validator')
        metrics.add_metric(name='TurnstileError', unit=MetricUnit.Count, value=1)
        return error_response(Exception('internal'), origin=origin)
