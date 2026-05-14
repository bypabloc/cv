"""
Lambda handler: POST /contact

Flow:
1. Parse + validate body (Pydantic ContactFormInput)
2. Resolve origin (CORS echo)
3. Rate-limit check (sliding window per-IP)
4. Service layer (Turnstile + persist + email)
5. Return 201 con contact_id
"""

from __future__ import annotations

import json
from typing import Any

from aws_lambda_powertools.metrics import MetricUnit
from pydantic import ValidationError as PydanticValidationError

from common.cors import resolve_origin
from common.exceptions import ApplicationError, ValidationError
from common.ip_extractor import extract_country, extract_ip
from common.logger import logger
from common.metrics import metrics
from common.rate_limit import check_or_raise
from common.responses import error_response, json_response
from common.tracer import tracer
from contact_form.schemas import ContactCreatedOutput, ContactFormInput
from contact_form.service import process_contact_form


@logger.inject_lambda_context(log_event=False, correlation_id_path='requestContext.requestId')
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Entry point Lambda contact_form."""
    headers = event.get('headers') or {}
    origin = resolve_origin(headers)
    ip = extract_ip(event)
    country = extract_country(event)
    user_agent = next(
        (v for k, v in headers.items() if k.lower() == 'user-agent'),
        None,
    )
    bypass_secret = next(
        (v for k, v in headers.items() if k.lower() == 'x-turnstile-bypass-secret'),
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

        # 2. Validate Pydantic
        try:
            parsed = ContactFormInput(**body_dict)
        except PydanticValidationError as e:
            raise ValidationError(
                'Validation failed',
                code='INVALID_INPUT',
                extra={'errors': e.errors(include_url=False)},
            ) from e

        # 3. Rate-limit check (puede levantar 429/403)
        check_or_raise(
            ip=ip,
            endpoint='/contact',
            country=country,
            turnstile_validated=False,
        )

        # 4. Service layer (Turnstile + persist + email)
        validated_data = parsed.model_dump(exclude={'cf_token'}, exclude_none=True)
        result = process_contact_form(
            validated_input=validated_data,
            cf_response=parsed.cf_token,
            ip=ip,
            bypass_secret=bypass_secret,
            country=country,
            user_agent=user_agent,
        )

        # 5. Auto-blacklist counter: mark turnstile_validated AFTER success
        # (este atomic ADD ya se hizo dentro de check_or_raise con turnstile_validated=False;
        # ahora hacemos un segundo INCREMENT marcando turnstile_validated=True)
        from common.rate_limit.auto_blacklist import (
            create_blacklist_rule,
            should_auto_blacklist,
        )
        from common.rate_limit.buckets import increment_bucket

        bucket = increment_bucket(
            ip=ip,
            endpoint='/contact',
            window_seconds=60,
            turnstile_validated=True,
        )
        if should_auto_blacklist(bucket['turnstile_tokens']):
            create_blacklist_rule(ip)
            logger.warning(
                'auto-blacklisted IP',
                extra={'ip': ip, 'turnstile_tokens': bucket['turnstile_tokens']},
            )

        # 6. Metrics
        metrics.add_metric(name='ContactFormSubmitted', unit=MetricUnit.Count, value=1)

        # 7. Success response
        output = ContactCreatedOutput(**result)
        return json_response(
            201, output.model_dump(), origin=origin,
        )

    except ApplicationError as e:
        logger.warning(
            'contact form rejected',
            extra={'code': e.code, 'reason': e.message, 'ip': ip},
        )
        metrics.add_metric(name='ContactFormRejected', unit=MetricUnit.Count, value=1)
        return error_response(e, origin=origin)

    except Exception:
        logger.exception('unhandled error in contact_form')
        metrics.add_metric(name='ContactFormError', unit=MetricUnit.Count, value=1)
        return error_response(Exception('internal'), origin=origin)
