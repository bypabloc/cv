"""@module shared.aws.lambda_invoke — invocacion async Lambda -> Lambda.

Portador unico de `boto3` para invocar otra Lambda de forma asincrona
(`InvocationType='Event'`, fire-and-forget). El `core/` de los Lambdas NUNCA
importa `boto3` directo: usa `from shared.aws.lambda_invoke import invoke_async`.

Reemplaza a SQS para el desacople de trabajo no-critico (envio de email,
escritura de tracking): el caller publica un evento y NO espera la respuesta;
AWS encola el invoke y reintenta automaticamente (2 reintentos para el target
async). El cliente se crea LAZY (PEP 562) para no penalizar el cold start de
un Lambda que importe el modulo sin invocar. Ver `.claude/rules/lambda-config.md`.
"""

from __future__ import annotations

import json
from typing import Any

from shared.core.config import settings
from shared.core.exceptions import ApplicationError
from shared.observability.logger import logger


class LambdaInvokeError(ApplicationError):
    """Fallo al invocar una Lambda downstream (el caller decide si degradar).

    Es una `ApplicationError` con `status_code=502` (Bad Gateway): cuando un
    encoder NO la captura y la deja propagar (caso `tracking_pixel`), el
    `http_handler` la mapea a HTTP 502 — la semantica correcta para "la
    dependencia downstream no respondio, reintenta". Los encoders que SI la
    capturan (`contact_form.notify_owner`) degradan a best-effort: el 201/202
    sale igual, el invoke fallido queda en un log.
    """

    default_code = 'UPSTREAM_UNAVAILABLE'
    status_code = 502


_client_cache: dict[str, Any] = {}


def _client() -> Any:
    """Devuelve el cliente Lambda (lazy singleton, materializado al 1er uso)."""
    if 'c' not in _client_cache:
        import boto3

        _client_cache['c'] = boto3.client(
            'lambda', region_name=settings.aws_region
        )
    return _client_cache['c']


def __getattr__(name: str) -> Any:
    """PEP 562: expone `lambda_client` lazy sin crear el cliente en import."""
    if name == 'lambda_client':
        return _client()
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')


def invoke_async(*, function_name: str, payload: dict[str, Any]) -> None:
    """Invoca `function_name` de forma asincrona (fire-and-forget).

    Usa `InvocationType='Event'`: AWS encola el evento y devuelve 202 sin
    ejecutar el handler en linea. El caller NO recibe el resultado. Una
    excepcion se loggea y se re-lanza como `LambdaInvokeError` para que el
    caller decida (los encoders la capturan y degradan a un log — best-effort,
    el 201/202 sale igual).

    Args:
        function_name: nombre (o ARN) de la Lambda target.
        payload: evento JSON-serializable que recibe el handler target.

    Raises:
        LambdaInvokeError: si el invoke falla (red, permisos, target inexistente).
    """
    try:
        _client().invoke(
            FunctionName=function_name,
            InvocationType='Event',
            Payload=json.dumps(payload, default=str).encode('utf-8'),
        )
    except Exception as exc:
        logger.warning(
            'lambda invoke_async failed',
            extra={'function_name': function_name, 'error': str(exc)},
        )
        raise LambdaInvokeError(
            f'invoke_async to {function_name} failed: {exc}'
        ) from exc

    logger.debug('lambda event_invoked', extra={'function_name': function_name})
