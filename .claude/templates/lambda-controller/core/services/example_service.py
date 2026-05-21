"""
Service de la operacion 'example': logica de negocio.

Un service concentra la logica de negocio reutilizable de una operacion,
desacoplada del transporte (el evento Lambda) y de la orquestacion (el
controller). Recibe datos ya validados y devuelve resultados o lanza
ServiceError; no conoce el formato del evento ni de la respuesta Lambda.

Regla de separacion:
  - controller : orquesta (valida -> llama al service -> normaliza salida).
  - service    : logica de negocio pura (este archivo).
  - utils      : infraestructura generica (invoker, logger, ...).

:Authors:
    - <Autor>

:Created:
    - YYYY-MM-DD
"""

from typing import Any

from settings.config import LogMetricType
from settings.config import logger
from utils.invoker import invoker_dispatch


class ServiceError(Exception):
    """
    Error de negocio lanzado por un service.

    El controller lo captura y lo traduce a la respuesta normalizada
    {is_valid: False, data, code}.

    :Authors:
        - <Autor>

    :Created:
        - YYYY-MM-DD
    """

    def __init__(
        self,
        message: str,
        *,
        code: int,
        error_code: str = 'SERVICE_ERROR',
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.error_code = error_code


def create_resource(
    *,
    resource_id: str,
    amount: int,
    arn: str,
) -> dict[str, Any]:
    """
    Crea un recurso invocando al Lambda downstream.

    Parameters
    ----------
    resource_id : str
        Identificador del recurso a crear.
    amount : int
        Monto asociado al recurso (ya validado como positivo).
    arn : str
        ARN del Lambda downstream.

    Returns
    -------
    dict[str, Any]
        Payload de respuesta del downstream.

    Raises
    ------
    ServiceError
        Si la invocacion al downstream falla.

    :Authors:
        - <Autor>

    :Created:
        - YYYY-MM-DD
    """
    logger.info(
        'Example service - create_resource',
        extra={
            'metric_type': LogMetricType.OPERATION_START.value,
            'resource_id': resource_id,
        },
    )

    request_data = {
        'action': 'create',
        'resource_id': resource_id,
        'amount': amount,
    }
    response = invoker_dispatch(arn=arn, data=request_data)

    if not response:
        raise ServiceError(
            'Error invocando Lambda downstream',
            code=5003,
            error_code='LAMBDA_INVOKE_ERROR',
        )

    return response


def check_resource(*, resource_id: str) -> dict[str, Any]:
    """
    Verifica el estado de un recurso.

    Parameters
    ----------
    resource_id : str
        Identificador del recurso a verificar.

    Returns
    -------
    dict[str, Any]
        Estado del recurso.

    :Authors:
        - <Autor>

    :Created:
        - YYYY-MM-DD
    """
    logger.info(
        'Example service - check_resource',
        extra={
            'metric_type': LogMetricType.OPERATION_START.value,
            'resource_id': resource_id,
        },
    )

    # ... logica de negocio real aqui ...
    return {
        'resource_id': resource_id,
        'status': 'ok',
    }
