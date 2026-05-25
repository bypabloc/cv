"""Builders compartidos para los tests unit del Lambda `contact_form`.

Prefijo `_` para que pytest NO recolecte este archivo como tests.
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock


def lambda_context() -> MagicMock:
    """Devuelve un Lambda context falso valido para Powertools.

    `logger.inject_lambda_context` lee `function_name`,
    `memory_limit_in_mb`, `invoked_function_arn` y `aws_request_id` del
    context.
    """
    ctx = MagicMock()
    ctx.function_name = 'portfolio-contact-form-test'
    ctx.memory_limit_in_mb = 512
    ctx.invoked_function_arn = (
        'arn:aws:lambda:us-east-1:000000000000:function:'
        'portfolio-contact-form-test'
    )
    ctx.aws_request_id = 'test-request-id'
    ctx.get_remaining_time_in_millis = lambda: 30000
    return ctx


def api_gw_event(
    *,
    body: dict[str, Any] | str | None = None,
    ip: str = '203.0.113.10',
    origin: str = 'https://the-full-stack.com',
    user_agent: str = 'Mozilla/5.0',
    extra_headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Construye un evento API Gateway REST proxy para `POST /contact`.

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
    user_agent : str
        Header User-Agent.
    extra_headers : dict | None
        Headers adicionales (ej. X-Turnstile-Bypass-Secret).
    """
    headers = {
        'Content-Type': 'application/json',
        'Origin': origin,
        'CF-Connecting-IP': ip,
        'User-Agent': user_agent,
    }
    if extra_headers:
        headers.update(extra_headers)

    if isinstance(body, dict):
        # El contrato HTTP del backend exige operation y action en el body
        # (resueltos por shared.lambda_kit.http_handler). Los tests vieron
        # solo los campos del form historicamente; aqui se inyectan los
        # valores por defecto si el caller no los provee, manteniendo los
        # tests focales en sus campos de interes.
        body = {'operation': 'contact', 'action': 'create', **body}
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
            'requestId': 'test-request-id',
            'stage': 'test',
        },
    }
