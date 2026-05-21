"""
Servicio Lambda: <NOMBRE_DEL_SERVICIO>

Descripcion: <que hace este lambda en una linea>.

Punto de entrada del Lambda. Es un router delgado: valida el evento,
resuelve el controller (operation + action) y devuelve una respuesta
normalizada. La logica de negocio vive en los services; los controllers
orquestan validacion -> service -> respuesta.

:Authors:
    - <Autor>

:Created:
    - YYYY-MM-DD
"""

import os
import sys

# El handler vive dentro de core/. Serverless invoke local no agrega ese
# directorio al sys.path: lo agregamos aqui para que los imports absolutos
# (models., settings., utils., services.) resuelvan tanto en AWS como en
# invoke local. En AWS, el Handler de la funcion es
# 'core.handler.lambda_handler'.
_core_dir = os.path.dirname(os.path.abspath(__file__))
if _core_dir not in sys.path:
    sys.path.insert(0, _core_dir)

from traceback import format_exc as traceback_format_exc
from typing import Any

from settings.config import LogMetricType
from settings.config import logger
from utils.validation.event import validate_event

__version__ = '1.0.0'


def lambda_handler(
    event: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    """
    Lambda handler: enruta el evento al controller correspondiente.

    Parameters
    ----------
    event : dict[str, Any]
        Evento con operation, action y data.
    context : dict[str, Any]
        Contexto Lambda de AWS.

    Returns
    -------
    dict[str, Any]
        Respuesta normalizada: {is_valid, code, status, message, data}.

    :Authors:
        - <Autor>

    :Created:
        - YYYY-MM-DD
    """
    _ = context

    operation = event.get('operation', 'unknown')
    action = event.get('action', 'unknown')

    logger.info(
        'Lambda invocation started',
        extra={
            'metric_type': LogMetricType.LAMBDA_START.value,
            'phase': 'INIT',
            'operation': operation,
            'action': action,
        },
    )

    try:
        # Validar evento y resolver controller (operation + action)
        validation_result = validate_event(event)

        if not validation_result.get('is_valid'):
            logger.error(
                'Event validation failed',
                extra={
                    'metric_type': (
                        LogMetricType.EVENT_VALIDATION_FAILED.value
                    ),
                    'operation': operation,
                    'action': action,
                },
            )
            return validation_result

        validated_event = validation_result.get('data')
        controller_result = validated_event.controller_info
        controller_data = controller_result.get('data', {})
        operation = controller_data.get('operation', 'unknown')
        action = controller_data.get('action', 'unknown')
        controller_class = controller_data.get('controller_class')

        if not controller_class:
            logger.error(
                'Controller class not found',
                extra={
                    'metric_type': (
                        LogMetricType.CONTROLLER_NOT_FOUND.value
                    ),
                    'operation': operation,
                    'action': action,
                },
            )
            return {
                'is_valid': False,
                'code': 2000,
                'status': 2000,
                'message': (
                    f"Controller for '{operation}/{action}' not found"
                ),
                'data': {},
            }

        # Ejecutar controller (preload -> validate -> execute)
        instance = controller_class(
            event=validated_event.controller_event,
        )
        result = instance.run()

        if not result.get('is_valid'):
            result_data = result.get('data', {})
            result_code = result.get('code', 5100)

            # Mapear code ranges a error codes del handler
            if result_code >= 5000:
                error_code = 5100
            elif result_code >= 2000:
                error_code = 2000
            else:
                error_code = 1000

            return {
                'is_valid': False,
                'code': error_code,
                'status': error_code,
                'message': result_data.get(
                    'message', 'Operation failed',
                ),
                'data': result_data,
            }

        logger.info(
            'Lambda invocation completed successfully',
            extra={
                'metric_type': LogMetricType.LAMBDA_SUCCESS.value,
                'phase': 'COMPLETE',
                'operation': operation,
                'action': action,
            },
        )
        return {
            'is_valid': True,
            'data': result.get('data', {}),
        }

    except Exception as exc:
        logger.critical(
            'Unexpected error during lambda execution',
            exception=exc,
            extra={
                'metric_type': (
                    LogMetricType.LAMBDA_UNEXPECTED_ERROR.value
                ),
                'operation': event.get('operation', 'unknown'),
                'traceback': traceback_format_exc(),
            },
        )
        return {
            'is_valid': False,
            'code': 6000,
            'status': 6000,
            'message': 'Error interno del servidor',
            'data': {},
        }
