"""
Invocacion de Lambdas downstream via boto3.

Reemplaza a librerias propietarias tipo `bifrost.connection_aws`. Si el
servicio no invoca otros Lambdas, este modulo puede eliminarse.

:Authors:
    - <Autor>

:Created:
    - YYYY-MM-DD
"""

import json
from typing import Any

try:
    import boto3
except ImportError:  # pragma: no cover - boto3 viene en el runtime AWS
    boto3 = None

from settings.config import LogMetricType
from settings.config import logger

_lambda_client = None


def _get_client() -> Any:
    """Devuelve un cliente Lambda boto3 cacheado a nivel de modulo."""
    global _lambda_client
    if _lambda_client is None:
        if boto3 is None:
            raise RuntimeError('boto3 no esta disponible en el entorno')
        _lambda_client = boto3.client('lambda')
    return _lambda_client


def invoker_dispatch(
    *,
    arn: str,
    data: dict[str, Any],
) -> dict[str, Any] | None:
    """
    Invoca un Lambda downstream de forma sincrona.

    Parameters
    ----------
    arn : str
        ARN (o nombre) de la funcion Lambda a invocar.
    data : dict[str, Any]
        Payload del evento para el Lambda downstream.

    Returns
    -------
    dict[str, Any] | None
        Payload de respuesta parseado, o None si la invocacion fallo.

    :Authors:
        - <Autor>

    :Created:
        - YYYY-MM-DD
    """
    logger.info(
        'Invoking downstream lambda',
        extra={
            'metric_type': LogMetricType.LAMBDA_INVOKE_START.value,
            'arn': arn,
        },
    )
    try:
        response = _get_client().invoke(
            FunctionName=arn,
            InvocationType='RequestResponse',
            Payload=json.dumps(data, default=str).encode('utf-8'),
        )
        raw_payload = response['Payload'].read()
        if not raw_payload:
            return None
        result: dict[str, Any] = json.loads(raw_payload)

        if response.get('FunctionError'):
            logger.error(
                'Downstream lambda returned a function error',
                extra={
                    'metric_type': LogMetricType.LAMBDA_INVOKE_FAILED.value,
                    'arn': arn,
                    'function_error': response['FunctionError'],
                },
            )
            return None

        logger.info(
            'Downstream lambda invoked successfully',
            extra={
                'metric_type': LogMetricType.LAMBDA_INVOKE_SUCCESS.value,
                'arn': arn,
            },
        )
        return result
    except Exception as exc:  # noqa: BLE001 - se loguea y se degrada a None
        logger.error(
            'Failed to invoke downstream lambda',
            exception=exc,
            extra={
                'metric_type': LogMetricType.LAMBDA_INVOKE_FAILED.value,
                'arn': arn,
            },
        )
        return None
