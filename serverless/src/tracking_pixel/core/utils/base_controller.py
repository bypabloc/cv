"""
Clase base para los controllers del servicio Lambda.

Define el ciclo de vida estandar: preload -> validate -> execute.
Cada controller concreto solo implementa execute().
"""

from abc import ABC
from abc import abstractmethod
from typing import Any

from pydantic import BaseModel
from pydantic import ValidationError

from settings.config import ErrorCode
from settings.config import LogMetricType
from settings.config import app_config
from settings.config import logger


class BaseController(ABC):
    """
    Clase base para todos los controllers del servicio.

    El metodo run() orquesta tres fases:
      1. preload  - carga configuracion (ej. ARN de un Lambda downstream).
      2. validate - valida el evento contra event_model (Pydantic).
      3. execute  - logica de negocio del controller (abstracto).

    Atributos de clase a definir en cada subclase:
      - event_model    : modelo Pydantic que valida el payload.
      - arn_config_key : nombre del campo de AppConfig con el ARN
                         downstream. Vacio si el controller no invoca
                         otro Lambda.
    """

    event_model: type[BaseModel] | None = None
    arn_config_key: str = ''

    def __init__(self, event: dict[str, Any]) -> None:
        self.event = event
        self.validated_data: BaseModel | None = None
        self.arn: str = ''

    def preload(self) -> dict:
        """
        Carga configuracion previa a la ejecucion.

        Por defecto resuelve el ARN downstream desde arn_config_key.
        Sobrescribir si el controller necesita otra preparacion.
        """
        if not self.arn_config_key:
            return {'is_valid': True, 'data': {}, 'code': 0}

        self.arn = getattr(app_config, self.arn_config_key, '')
        if not self.arn:
            return {
                'is_valid': False,
                'data': {
                    'error_code': 'CONFIGURATION_MISSING',
                    'message': (
                        f'{self.arn_config_key.upper()} no configurado'
                    ),
                },
                'code': ErrorCode.CONFIGURATION_MISSING.value,
            }
        return {'is_valid': True, 'data': {}, 'code': 0}

    def validate(self) -> dict:
        """Valida el evento contra event_model (Pydantic)."""
        if not self.event_model:
            return {'is_valid': True, 'data': {}, 'code': 0}

        try:
            self.validated_data = self.event_model.model_validate(
                self.event,
            )
        except ValidationError:
            return {
                'is_valid': False,
                'data': {
                    'error': 'INVALID_EVENT_DATA',
                    'message': 'Event validation failed',
                },
                'code': ErrorCode.VALIDATION_ERROR.value,
            }
        except Exception as exc:  # noqa: BLE001 - se reporta como error
            return {
                'is_valid': False,
                'data': {
                    'error': 'UNEXPECTED_VALIDATION_ERROR',
                    'message': (
                        f'Error de validacion inesperado: {exc}'
                    ),
                },
                'code': ErrorCode.UNEXPECTED_ERROR.value,
            }

        return {
            'is_valid': True,
            'data': self.validated_data.model_dump(),
            'code': 0,
        }

    @abstractmethod
    def execute(self) -> dict:
        """
        Logica principal del controller. Debe implementarse en cada
        subclase y devolver {is_valid, data, code}.
        """

    def run(self) -> dict:
        """Ejecuta el ciclo preload -> validate -> execute con logging."""
        # --- Preload ---
        logger.info(
            'Starting preload phase',
            extra={
                'metric_type': LogMetricType.PHASE_START.value,
                'phase': 'PRELOAD',
            },
        )
        preload_result = self.preload()
        if not preload_result.get('is_valid', True):
            logger.error(
                'Preload phase failed',
                extra={
                    'metric_type': (
                        LogMetricType.PRELOAD_PHASE_FAILED.value
                    ),
                },
            )
            return preload_result

        # --- Validate ---
        logger.info(
            'Starting validate phase',
            extra={
                'metric_type': LogMetricType.PHASE_START.value,
                'phase': 'VALIDATE',
            },
        )
        validate_result = self.validate()
        if not validate_result.get('is_valid', True):
            logger.error(
                'Validate phase failed',
                extra={
                    'metric_type': (
                        LogMetricType.VALIDATE_PHASE_FAILED.value
                    ),
                },
            )
            return validate_result

        # Guard: validated_data debe estar seteado si hay event_model
        if self.event_model and self.validated_data is None:
            logger.error(
                'validated_data is None after validate phase',
                extra={
                    'metric_type': (
                        LogMetricType.VALIDATE_PHASE_FAILED.value
                    ),
                },
            )
            return {
                'is_valid': False,
                'data': {
                    'error': 'VALIDATION_STATE_ERROR',
                    'message': 'validated_data not set after validation',
                },
                'code': ErrorCode.UNEXPECTED_ERROR.value,
            }

        # --- Execute ---
        logger.info(
            'Starting execute phase',
            extra={
                'metric_type': LogMetricType.PHASE_START.value,
                'phase': 'EXECUTE',
            },
        )
        execute_result = self.execute()

        logger.info(
            'Execute phase completed',
            extra={
                'metric_type': LogMetricType.PHASE_COMPLETE.value,
                'phase': 'EXECUTE',
                'is_valid': execute_result.get('is_valid'),
            },
        )

        if not execute_result.get('is_valid'):
            logger.error(
                'Execute phase failed',
                extra={
                    'metric_type': (
                        LogMetricType.EXECUTE_PHASE_FAILED.value
                    ),
                },
            )

        return execute_result
