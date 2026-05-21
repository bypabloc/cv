"""Importacion dinamica de controllers por operation + action.

Lee el mapeo de operaciones desde settings/operations.py y luego importa
controllers.{controller}.{action}.{Action}.
"""

from importlib import import_module
from traceback import format_exc as traceback_format_exc

from settings.config import ErrorCode, LogMetricType, logger
from settings.operations import OPERATIONS
from utils.base_controller import BaseController


def resolve_operation(operation: str) -> str:
    """Resuelve un codename de operacion a su carpeta de controller.

    Busca en OPERATIONS. Si no existe, devuelve el operation original
    (para que el import falle con un error descriptivo).

    Parameters
    ----------
    operation : str
        Nombre de la operacion (puede ser un alias).

    Returns
    -------
    str
        Nombre de la carpeta de controller.
    """
    config = OPERATIONS.get(operation)
    if config:
        return config['controller']
    return operation


def import_controller(operation: str, action: str) -> dict:
    """Importa dinamicamente un controller por operation + action.

    Resuelve el codename via OPERATIONS y luego importa
    controllers.{controller}.{action}, tomando la clase {Action}
    (action.capitalize()).

    Parameters
    ----------
    operation : str
        Nombre de la operacion (o alias).
    action : str
        Nombre de la accion (create, check, etc.).

    Returns
    -------
    dict
        {is_valid: True, data: {controller_class, ...}} si OK,
        {is_valid: False, ...} si falla.
    """
    if not operation:
        return {
            'is_valid': False,
            'data': {
                'error_code': 'INVALID_OPERATION',
                'message': 'Operation name cannot be empty',
            },
            'code': ErrorCode.VALIDATION_ERROR.value,
            'class': None,
        }

    if not action:
        return {
            'is_valid': False,
            'data': {
                'error_code': 'INVALID_ACTION',
                'message': 'Action name cannot be empty',
            },
            'code': ErrorCode.VALIDATION_ERROR.value,
            'class': None,
        }

    resolved_operation = resolve_operation(operation)
    class_name = action.capitalize()
    module_path = f'controllers.{resolved_operation}.{action}'

    try:
        module = import_module(module_path)
    except (ImportError, ModuleNotFoundError) as exc:
        logger.warning(
            'Invalid operation/action requested',
            extra={
                'metric_type': LogMetricType.INVALID_OPERATION.value,
                'operation': operation,
                'resolved_operation': resolved_operation,
                'action': action,
                'error': str(exc),
            },
        )
        return {
            'is_valid': False,
            'data': {
                'error_code': 'MODULE_NOT_FOUND',
                'message': (
                    f"Controller module '{module_path}' not found"
                ),
            },
            'code': ErrorCode.VALIDATION_ERROR.value,
            'class': None,
        }
    except Exception as exc:
        logger.error(
            'Unexpected error importing controller module',
            extra={
                'metric_type': LogMetricType.CONTROLLER_IMPORT_ERROR.value,
                'operation': operation,
                'action': action,
                'error': str(exc),
                'traceback': traceback_format_exc(),
            },
        )
        return {
            'is_valid': False,
            'data': {
                'error_code': 'IMPORT_ERROR',
                'message': 'Unexpected error importing controller',
            },
            'code': ErrorCode.UNEXPECTED_ERROR.value,
            'class': None,
        }

    try:
        controller_class = getattr(module, class_name)
    except AttributeError as exc:
        logger.warning(
            'Controller class not found in module',
            extra={
                'metric_type': (
                    LogMetricType.CONTROLLER_CLASS_NOT_FOUND.value
                ),
                'operation': operation,
                'action': action,
                'class_name': class_name,
                'error': str(exc),
            },
        )
        return {
            'is_valid': False,
            'data': {
                'error_code': 'CLASS_NOT_FOUND',
                'message': (
                    f"Controller class '{class_name}' "
                    f"not found in module '{module_path}'"
                ),
            },
            'code': ErrorCode.VALIDATION_ERROR.value,
            'class': None,
        }

    if not (
        isinstance(controller_class, type)
        and issubclass(controller_class, BaseController)
    ):
        logger.warning(
            'Controller class does not inherit from BaseController',
            extra={
                'metric_type': (
                    LogMetricType.CONTROLLER_CLASS_NOT_FOUND.value
                ),
                'operation': operation,
                'action': action,
                'class_name': class_name,
            },
        )
        return {
            'is_valid': False,
            'data': {
                'error_code': 'INVALID_CONTROLLER',
                'message': (
                    f"Controller '{class_name}' in '{module_path}' "
                    f"must inherit from BaseController"
                ),
            },
            'code': ErrorCode.VALIDATION_ERROR.value,
            'class': None,
        }

    return {
        'is_valid': True,
        'data': {
            'class_name': class_name,
            'module': module,
            'controller_class': controller_class,
        },
        'code': 0,
        'class': controller_class,
    }
