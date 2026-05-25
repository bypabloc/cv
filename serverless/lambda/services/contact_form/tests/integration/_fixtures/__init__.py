"""Builders compartidos para los integration tests del Lambda `contact_form`.

Prefijo `_` en el paquete y en cada helper para que pytest NO los
recolecte como tests. Los integration tests invocan el `lambda_handler`
real con un evento API Gateway crudo; estos builders arman ese evento y
el Lambda context, y exponen helpers para inspeccionar el estado
observable (DynamoDB + SES) tras la invocacion.
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock

import boto3

_REGION = 'us-east-1'
_VALID_BODY: dict[str, Any] = {
    'name': 'Pablo Contreras',
    'email': 'user@example.com',
    'message': 'Hola, me interesa colaborar contigo en un proyecto.',
    'cf_token': 'x' * 30,
}


def _lambda_context() -> MagicMock:
    """Devuelve un Lambda context falso valido para Powertools.

    `logger.inject_lambda_context` lee `function_name`,
    `memory_limit_in_mb`, `invoked_function_arn` y `aws_request_id`.
    """
    ctx = MagicMock()
    ctx.function_name = 'portfolio-contact-form-test'
    ctx.memory_limit_in_mb = 512
    ctx.invoked_function_arn = (
        'arn:aws:lambda:us-east-1:000000000000:function:'
        'portfolio-contact-form-test'
    )
    ctx.aws_request_id = 'integration-request-id'
    ctx.get_remaining_time_in_millis = lambda: 30000
    return ctx


def _api_gw_event(
    *,
    body: dict[str, Any] | str | None = None,
    ip: str = '198.51.100.10',
    origin: str = 'https://the-full-stack.com',
    country: str = 'CL',
    user_agent: str = 'Mozilla/5.0',
    extra_headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Construye un evento API Gateway REST proxy crudo para `POST /contact`.

    Parameters
    ----------
    body : dict | str | None
        Cuerpo del request. Un dict se serializa a JSON; un str se usa
        tal cual (util para probar JSON malformado); None deja el body
        vacio.
    ip : str
        IP del cliente (header CF-Connecting-IP + requestContext).
    origin : str
        Header Origin (para el echo CORS).
    country : str
        Header CF-IPCountry (country del visitante).
    user_agent : str
        Header User-Agent.
    extra_headers : dict | None
        Headers adicionales (ej. X-Turnstile-Bypass-Secret).
    """
    headers = {
        'Content-Type': 'application/json',
        'Origin': origin,
        'CF-Connecting-IP': ip,
        'CF-IPCountry': country,
        'User-Agent': user_agent,
    }
    if extra_headers:
        headers.update(extra_headers)

    if isinstance(body, dict):
        body_str: str = json.dumps(body)
    elif isinstance(body, str):
        body_str = body
    else:
        body_str = ''

    return {
        'httpMethod': 'POST',
        'path': '/contact',
        'headers': headers,
        'body': body_str,
        'isBase64Encoded': False,
        'requestContext': {
            'identity': {'sourceIp': ip},
            'requestId': 'integration-request-id',
            'stage': 'test',
        },
    }


def _valid_body(**overrides: Any) -> dict[str, Any]:
    """Devuelve un body de form valido, con overrides opcionales."""
    return {**_VALID_BODY, **overrides}


def _count_contacts() -> int:
    """Cantidad de items en la tabla `contacts` (DynamoDB mockeada)."""
    table = boto3.resource('dynamodb', region_name=_REGION).Table(
        'portfolio-contacts-test'
    )
    return table.scan(Select='COUNT')['Count']


def _get_contact(contact_id: str) -> dict[str, Any] | None:
    """Lee un contacto persistido en DynamoDB por `contact_id`."""
    table = boto3.resource('dynamodb', region_name=_REGION).Table(
        'portfolio-contacts-test'
    )
    return table.get_item(Key={'id': contact_id}).get('Item')


def _ses_sent_count() -> int:
    """Cantidad de emails que SES (moto) registro como enviados.

    El service envia via la API SES v2 (`sesv2`), pero moto comparte el
    mismo backend con la API v1: `ses.get_send_quota()` expone el contador
    `SentLast24Hours`. `sesv2.get_account()` no esta implementado en moto.
    """
    ses = boto3.client('ses', region_name=_REGION)
    return int(ses.get_send_quota()['SentLast24Hours'])


def _ses_last_email() -> Any:
    """Devuelve el ultimo email registrado por el backend SES de moto.

    El objeto expone `source` (remitente), `subject` y `destinations`.
    """
    from moto.core import DEFAULT_ACCOUNT_ID
    from moto.ses.models import ses_backends

    backend = ses_backends[DEFAULT_ACCOUNT_ID][_REGION]
    return backend.sent_messages[-1]


def _get_blacklist_rule(ip: str) -> dict[str, Any] | None:
    """Lee la rule `ip_blacklist` de una IP en la tabla rate-limit-rules."""
    table = boto3.resource('dynamodb', region_name=_REGION).Table(
        'portfolio-rate-limit-rules-test'
    )
    return table.get_item(
        Key={'rule_key': f'ip#{ip}', 'kind': 'ip_blacklist'}
    ).get('Item')


def _put_endpoint_rule(*, endpoint: str, limit: int, window_seconds: int) -> None:
    """Crea una rule de endpoint en la tabla rate-limit-rules.

    Permite forzar un limite bajo para ejercitar el HTTP 429 sin emitir
    decenas de requests.
    """
    table = boto3.resource('dynamodb', region_name=_REGION).Table(
        'portfolio-rate-limit-rules-test'
    )
    table.put_item(
        Item={
            'rule_key': f'endpoint#{endpoint}',
            'kind': 'endpoint',
            'limit': limit,
            'window_seconds': window_seconds,
            'action': 'throttle',
        }
    )
