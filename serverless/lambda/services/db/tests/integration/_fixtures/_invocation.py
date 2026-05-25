"""Builders de integration para invocar el Lambda `db` end-to-end.

Prefijo `_` para que pytest NO recolecte este archivo como tests.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock


def lambda_context() -> MagicMock:
    """Devuelve un Lambda context falso valido para Powertools.

    `logger.inject_lambda_context` lee `function_name`,
    `memory_limit_in_mb`, `invoked_function_arn` y `aws_request_id`.
    """
    ctx = MagicMock()
    ctx.function_name = 'portfolio-db-itest'
    ctx.memory_limit_in_mb = 512
    ctx.invoked_function_arn = (
        'arn:aws:lambda:us-east-1:000000000000:function:portfolio-db-itest'
    )
    ctx.aws_request_id = 'itest-request-id'
    return ctx


def invoke_event(command: str, args: dict[str, Any] | None = None) -> dict:
    """Construye el payload crudo de invocacion `{command, args}`.

    Es el evento que el Lambda `db` recibe de un `aws lambda invoke` o de
    un deploy hook — el mismo que los integration tests pasan al
    `lambda_handler` real.
    """
    event: dict[str, Any] = {'command': command}
    if args is not None:
        event['args'] = args
    return event
