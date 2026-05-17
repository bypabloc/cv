"""
Business logic del contact form (orchestracion de Turnstile + persistence + SES).

El service layer es agnostico al transport (Lambda event). Recibe un dict ya
validado por Pydantic y retorna el resultado.
"""

from __future__ import annotations

from typing import Any

from aws_lambda_powertools.metrics import MetricUnit

from common.logger import logger
from common.metrics import metrics
from common.turnstile import verify_turnstile_token
from contact_form.notification import send_owner_email
from contact_form.persistence import save_contact


def process_contact_form(
    *,
    validated_input: dict[str, Any],
    cf_response: str,
    ip: str,
    bypass_secret: str | None = None,
    country: str | None = None,
    user_agent: str | None = None,
) -> dict[str, str]:
    """
    Orquesta validacion Turnstile + persistence DynamoDB + envio de email.

    Args:
        validated_input: dict del Pydantic ContactFormInput (sin cf_token).
        cf_response: token Turnstile separado de los campos del form.
        ip: IP del cliente (CF-Connecting-IP).
        bypass_secret: header X-Turnstile-Bypass-Secret (opcional, tests).
        country: country code (CF-IPCountry).
        user_agent: user-agent de la request.

    Returns:
        Dict con `contact_id` y `created_at` ISO 8601.

    Raises:
        TurnstileError: si el captcha falla.
        ClientError: si DynamoDB o SES fallan.
    """
    # 1. Verify Turnstile token
    verify_turnstile_token(
        cf_response,
        remote_ip=ip,
        bypass_secret=bypass_secret,
    )

    # 2. Persist en DynamoDB (incluir metadata de la request)
    payload = {**validated_input, 'ip': ip}
    if country:
        payload['country'] = country
    if user_agent:
        payload['user_agent'] = user_agent

    result = save_contact(payload)
    logger.info(
        'contact persisted',
        extra={'contact_id': result['contact_id']},
    )

    # 3. Send email al owner (NO bloquear la response del usuario si falla)
    try:
        contact_with_meta = {**payload, **result}
        send_owner_email(contact_with_meta)
    except Exception:
        logger.exception(
            'failed to send owner email (contact already persisted)',
            extra={'contact_id': result['contact_id']},
        )
        # NO re-raise: el form se guardo en DynamoDB y el lead no se pierde.
        # El fallo se hace VISIBLE con una metrica CloudWatch para poder
        # detectarlo sin romper la respuesta 201 del usuario.
        metrics.add_metric(
            name='OwnerEmailFailed',
            unit=MetricUnit.Count,
            value=1,
        )

    return result
