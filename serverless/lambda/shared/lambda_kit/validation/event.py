"""@module shared.lambda_kit.validation.event — validacion del evento.

Envuelve `EventModel.validate_event` y convierte cualquier excepcion en
una respuesta de error normalizada.

Era identico en los 4 Lambdas del backend; se unifico aca. El acople al
Lambda se rompe pasando la clase `EventModel` como PARAMETRO (la
construye el Lambda con `build_event_model(OPERATIONS)`).
"""

from __future__ import annotations

from traceback import format_exc as traceback_format_exc
from typing import Any, Protocol

from pydantic import ValidationError

from shared.lambda_kit.log_metrics import LogMetricType
from shared.observability.logger import logger

# Mapeo de tipos de error a codigos internos.
_ERROR_CODES = {
    'missing_event': 1000,
    'invalid_event_type': 1000,
    'pydantic_error': 1000,
    'custom_validation_error': 1000,
    'invalid_operation': 1001,
    'unexpected_error': 6000,
}


class EventModelClass(Protocol):
    """Contrato de la clase `EventModel` que `validate_event` consume.

    `build_event_model(OPERATIONS)` produce una clase que lo cumple.
    """

    def validate_event(self, event: dict[str, Any]) -> object:
        """Valida el evento y devuelve la instancia del modelo."""
        ...


def validate_event(
    event: object,
    event_model: EventModelClass,
) -> dict[str, Any]:
    """Valida el evento y resuelve el controller.

    Parameters
    ----------
    event : object
        Evento a validar (se espera un dict; otros tipos se rechazan).
    event_model : EventModelClass
        Clase `EventModel` del Lambda, construida con
        `build_event_model(OPERATIONS)`.

    Returns
    -------
    dict
        `{is_valid: True, data: EventModel}` si OK,
        `{is_valid: False, code, status, message, data}` si falla.
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
        validated_event = event_model.validate_event(event)
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
            'invalid_operation'
            if is_invalid_op
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


def _error_response(error_code: int, message: str) -> dict[str, Any]:
    """Construye una respuesta de error de validacion normalizada."""
    return {
        'is_valid': False,
        'code': error_code,
        'status': error_code,
        'message': message,
        'data': {},
    }
