"""
Lambda handler: POST /track

Diferencias vs contact_form:
- No Turnstile estricto (best-effort, no enforced)
- Sin SES email
- Response 204 No Content (fire-and-forget)
- Rate-limit mas laxo (30/min vs 3/min en contact)
"""

from __future__ import annotations

import json
from typing import Any

from aws_lambda_powertools.metrics import MetricUnit
from pydantic import ValidationError as PydanticValidationError

from shared.cors import public_cors_origin
from shared.exceptions import ApplicationError, ValidationError
from shared.ip_extractor import extract_country, extract_ip
from shared.logger import logger
from shared.metrics import metrics
from shared.rate_limit import check_or_raise
from shared.responses import error_response, no_content_response
from shared.tracer import tracer
from tracking_pixel.schemas import TrackingEventInput
from tracking_pixel.service import process_tracking_event


@logger.inject_lambda_context(log_event=False, correlation_id_path='requestContext.requestId')
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Entry point Lambda tracking_pixel."""
    headers = event.get('headers') or {}
    # /track lo invoca navigator.sendBeacon (modo `ping`), que exige
    # Access-Control-Allow-Origin: '*' literal. Un echo del Origin hace
    # fallar la request con CORS error. /track es tracking anonimo sin
    # credenciales, asi que '*' es correcto (ver shared.cors).
    origin = public_cors_origin()
    ip = extract_ip(event)
    country = extract_country(event)
    user_agent = next(
        (v for k, v in headers.items() if k.lower() == 'user-agent'),
        None,
    )

    try:
        # 1. Parse body
        body_raw = event.get('body') or ''
        try:
            body_dict = json.loads(body_raw) if body_raw else {}
        except json.JSONDecodeError as e:
            msg = 'Invalid JSON body'
            raise ValidationError(msg, code='INVALID_JSON') from e

        # 2. Validate
        try:
            parsed = TrackingEventInput(**body_dict)
        except PydanticValidationError as e:
            raise ValidationError(
                'Validation failed',
                code='INVALID_INPUT',
                extra={'errors': e.errors(include_url=False)},
            ) from e

        # 3. Rate-limit check (limit mas alto que /contact)
        check_or_raise(
            ip=ip,
            endpoint='/track',
            country=country,
            turnstile_validated=False,
        )

        # 4. Service: enrichment + persist (sin Turnstile siteverify)
        validated_data = parsed.model_dump(exclude={'cf_token'}, exclude_none=True)
        process_tracking_event(
            validated_input=validated_data,
            ip=ip,
            user_agent=user_agent,
            country=country,
        )

        # 5. Metrics
        metrics.add_metric(name='TrackingEventReceived', unit=MetricUnit.Count, value=1)

        # 6. 204 No Content (fire-and-forget)
        return no_content_response(origin=origin)

    except ApplicationError as e:
        logger.warning(
            'tracking event rejected',
            extra={'code': e.code, 'reason': e.message, 'ip': ip},
        )
        metrics.add_metric(name='TrackingEventRejected', unit=MetricUnit.Count, value=1)
        return error_response(e, origin=origin)

    except Exception:
        logger.exception('unhandled error in tracking_pixel')
        metrics.add_metric(name='TrackingEventError', unit=MetricUnit.Count, value=1)
        return error_response(Exception('internal'), origin=origin)
