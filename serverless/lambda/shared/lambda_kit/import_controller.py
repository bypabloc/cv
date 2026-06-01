"""@module shared.lambda_kit.import_controller — import dinamico de controllers.

Importa el controller `controllers.<controller>.<action>.<Action>` de un
Lambda a partir de `operation` + `action`, resolviendo el codename via
el mapa `OPERATIONS` del Lambda.

Era identico en los 4 Lambdas; se unifico aca. El acoplamiento al
Lambda se rompe pasando `OPERATIONS` como PARAMETRO (antes lo importaba
de `settings.operations`). `logger` viene de `shared.observability`;
`ErrorCode` / `LogMetricType` de `shared.lambda_kit`.
"""

from __future__ import annotations

from importlib import import_module
from traceback import format_exc as traceback_format_exc
from typing import Any

from shared.lambda_kit.base_controller import BaseController
from shared.lambda_kit.error_codes import ErrorCode
from shared.lambda_kit.log_metrics import LogMetricType
from shared.observability.logger import logger


def resolve_operation(
    operation: str, operations: dict[str, dict[str, Any]]
) -> str:
    """Resuelve un codename de operacion a su carpeta de controller.

    Busca en `operations`. Si no existe, devuelve el `operation`
    original (para que el import falle con un error descriptivo).

    Parameters
    ----------
    operation : str
        Nombre de la operacion (puede ser un alias).
    operations : dict[str, dict[str, Any]]
        Mapa `OPERATIONS` del Lambda.

    Returns
    -------
    str
        Nombre de la carpeta de controller.
    """
    config = operations.get(operation)
    if config:
        return str(config['controller'])
    return operation


def import_controller(
    operation: str,
    action: str,
    operations: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Importa dinamicamente un controller por `operation` + `action`.

    Resuelve el codename via `operations` y luego importa
    `controllers.<controller>.<action>`, tomando la clase `<Action>`
    (`action.capitalize()`).

    Parameters
    ----------
    operation : str
        Nombre de la operacion (o alias).
    action : str
        Nombre de la accion (`create`, `check`, ...).
    operations : dict[str, dict[str, Any]]
        Mapa `OPERATIONS` del Lambda.

    Returns
    -------
    dict
        `{is_valid: True, data: {controller_class, ...}}` si OK,
        `{is_valid: False, ...}` si falla.
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

    resolved_operation = resolve_operation(operation, operations)
    # Normalizar el action a la convencion del estandar lambda-controller:
    # `verify-magic-link` -> module `verify_magic_link.py` + clase
    # `VerifyMagicLink`. El action puede llegar con guiones (URL/JSON),
    # underscores o ya en PascalCase; se resuelve en ambas variantes.
    action_snake = action.replace('-', '_')
    action_segments = [s for s in action.replace('_', '-').split('-') if s]
    class_name = ''.join(seg[:1].upper() + seg[1:] for seg in action_segments)
    module_path = f'controllers.{resolved_operation}.{action_snake}'

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
                    f'must inherit from BaseController'
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
