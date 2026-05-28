"""@module send_service — wrapper sobre shared.aws.send_email.

Resuelve el `from_address` desde SSM (`ses-from-address`) y delega el
envio a `shared.aws.send_email`. Convierte las excepciones de boto3 SES
a errores de dominio:

  - `SesThrottledError`: retryable (SQS reintenta).
  - `SesSendError`: no-retryable (bounce permanente, identidad no
    verificada, etc.) — el caller registra `email.send.failed` y deja
    que SQS borre el mensaje.

NUNCA `import boto3` ni `from botocore`: las excepciones se detectan por
nombre (`type(exc).__name__`) para no tener que importar las clases de
botocore directamente — eso violaria el contrato shared-only.
"""

from __future__ import annotations

from typing import Any

from shared.aws import send_email
from shared.aws.ssm import get_secret_by_name
from shared.observability.logger import logger

__all__ = ['SesSendError', 'SesThrottledError', 'send_auth_email']


class SesSendError(Exception):
    """SES rechazo el envio de forma permanente (no-retryable)."""


class SesThrottledError(Exception):
    """SES throttled la cuenta o el sending rate (retryable)."""


# Nombres de excepciones botocore que indican throttling de SES (caso
# retryable). El resto de errores `ClientError` se consideran permanentes.
_THROTTLE_ERROR_NAMES: frozenset[str] = frozenset({
    'ThrottlingException',
    'TooManyRequestsException',
    'Throttling',
    'RequestThrottled',
    'SendingPausedException',
})


def send_auth_email(
    *,
    to: str,
    subject: str,
    text_body: str,
    html_body: str,
) -> str:
    """Envia un email transaccional de auth via SES.

    Parameters
    ----------
    to : str
        Destinatario (el modelo Pydantic ya valida formato).
    subject : str
        Asunto.
    text_body : str
        Cuerpo plano (obligatorio para deliverability).
    html_body : str
        Cuerpo HTML.

    Returns
    -------
    str
        SES MessageId.

    Raises
    ------
    SesThrottledError
        Si SES esta throttling (retryable via SQS).
    SesSendError
        Si SES rechazo el mensaje de forma permanente.
    """
    from_address = get_secret_by_name(
        'ses-from-address',
        local_env='EMAIL_FROM',
    )

    try:
        response: dict[str, Any] = send_email(
            from_address=f'The Full Stack <{from_address}>',
            to_addresses=[to],
            subject=subject,
            text_body=text_body,
            html_body=html_body,
        )
    except Exception as exc:
        exc_name = type(exc).__name__
        if exc_name in _THROTTLE_ERROR_NAMES:
            raise SesThrottledError(str(exc)) from exc
        # Cualquier otro `ClientError` de SES o `MessageRejected` -> permanente.
        raise SesSendError(str(exc)) from exc

    message_id: str = response.get('MessageId', '')
    logger.info(
        'SES send_email succeeded',
        extra={'message_id': message_id, 'recipient_count': 1},
    )
    return message_id
