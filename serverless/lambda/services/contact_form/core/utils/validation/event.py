"""
Validacion del evento Lambda con manejo uniforme de errores.

Envuelve EventModel.validate_event y convierte cualquier excepcion en
una respuesta de error normalizada.
"""

from traceback import format_exc as traceback_format_exc
from typing import Any

from models.event import EventModel
from pydantic import ValidationError
from settings.config import LogMetricType, logger

# Mapeo de tipos de error a codigos internos
_ERROR_CODES = {
    'missing_event': 1000,
    'invalid_event_type': 1000,
    'pydantic_error': 1000,
    'custom_validation_error': 1000,
    'invalid_operation': 1001,
    'unexpected_error': 6000,
}


def validate_event(event: dict[str, Any]) -> dict:
    """
    Valida el evento y resuelve el controller.

    Parameters
    ----------
    event : dict[str, Any]
        Evento a validar.

    Returns
    -------
    dict
        {is_valid: True, data: EventModel} si OK,
        {is_valid: False, code, status, message, data} si falla.
    """
    if event is None:
        return _error_response(
            error_code=_ERROR_CODES['missing_event'],
            message='Event no puede ser nulo',
        )

    if not isinstance(event, dict):
        return _error_response(
            error_code=_ERROR_CODES['invalid_event_type'],
            message='Event debe ser un objeto JSON valido',
        )

    try:
        validated_event = EventModel.validate_event(event)
        return {
            'is_valid': True,
            'data': validated_event,
            'code': 0,
        }

    except ValidationError as exc:
        logger.warning(
            'Event validation pydantic error',
            extra={
                'metric_type': (
                    LogMetricType.EVENT_VALIDATION_PYDANTIC_ERROR.value
                ),
                'event_preview': str(event)[:200],
                'validation_errors': str(exc),
            },
        )
        return _error_response(
            error_code=_ERROR_CODES['pydantic_error'],
            message='Error de validacion de estructura',
        )

    except ValueError as exc:
        original_message = str(exc) if exc.args else 'Validation error'
        is_invalid_op = 'no es valida' in original_message
        error_key = (
            'invalid_operation' if is_invalid_op
            else 'custom_validation_error'
        )
        return _error_response(
            error_code=_ERROR_CODES[error_key],
            message=original_message,
        )

    except Exception:
        logger.error(
            'Unexpected error during event validation',
            extra={
                'metric_type': (
                    LogMetricType.EVENT_VALIDATION_UNEXPECTED_ERROR.value
                ),
                'event_preview': str(event)[:200],
                'traceback': traceback_format_exc(),
            },
        )
        return _error_response(
            error_code=_ERROR_CODES['unexpected_error'],
            message='Error inesperado durante la validacion',
        )


def _error_response(error_code: int, message: str) -> dict:
    """Construye una respuesta de error de validacion normalizada."""
    return {
        'is_valid': False,
        'code': error_code,
        'status': error_code,
        'message': message,
        'data': {},
    }
