"""Builders compartidos para los tests unit del Lambda `db`.

Prefijo `_` para que pytest NO recolecte este archivo como tests.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock


def lambda_context() -> MagicMock:
    """Devuelve un Lambda context falso valido para Powertools.

    `logger.inject_lambda_context` lee `function_name`, `memory_limit_in_mb`,
    `invoked_function_arn` y `aws_request_id` del context.
    """
    ctx = MagicMock()
    ctx.function_name = 'portfolio-db-test'
    ctx.memory_limit_in_mb = 512
    ctx.invoked_function_arn = (
        'arn:aws:lambda:us-east-1:000000000000:function:portfolio-db-test'
    )
    ctx.aws_request_id = 'test-request-id'
    return ctx


def invoke_event(command: str, args: dict[str, Any] | None = None) -> dict:
    """Construye el payload de invocacion `{command, args}`."""
    event: dict[str, Any] = {'command': command}
    if args is not None:
        event['args'] = args
    return event
