"""@module shared.lambda_kit.log_metrics — tipos de metrica de logging.

`LogMetricType` enumera los `metric_type` del logging estructurado del
estandar lambda-controller. Cada log lleva uno en su `extra`, lo que
permite construir metricas y filtros en CloudWatch.

Estos eran la base comun de los 4 Lambdas. Se unificaron aca. Los tipos
de metrica de DOMINIO (ej. `CONTACT_PERSISTED`) los define cada Lambda
en su `settings/config.py`.
"""

from __future__ import annotations

from enum import Enum


class LogMetricType(Enum):
    """Tipos de metrica para logging estructurado del lambda-controller."""

    # Lambda lifecycle
    LAMBDA_START = 'LAMBDA_START'
    LAMBDA_SUCCESS = 'LAMBDA_SUCCESS'
    LAMBDA_UNEXPECTED_ERROR = 'LAMBDA_UNEXPECTED_ERROR'

    # Phase lifecycle
    PHASE_START = 'PHASE_START'
    PHASE_COMPLETE = 'PHASE_COMPLETE'

    # Event validation
    EVENT_VALIDATION_FAILED = 'EVENT_VALIDATION_FAILED'
    EVENT_VALIDATION_PYDANTIC_ERROR = 'EVENT_VALIDATION_PYDANTIC_ERROR'
    EVENT_VALIDATION_UNEXPECTED_ERROR = 'EVENT_VALIDATION_UNEXPECTED_ERROR'

    # Controller lifecycle
    CONTROLLER_NOT_FOUND = 'CONTROLLER_NOT_FOUND'
    CONTROLLER_EXECUTE_START = 'CONTROLLER_EXECUTE_START'
    CONTROLLER_SUCCESS = 'CONTROLLER_SUCCESS'
    CONTROLLER_ERROR = 'CONTROLLER_ERROR'

    # Phase failures
    PRELOAD_PHASE_FAILED = 'PRELOAD_PHASE_FAILED'
    VALIDATE_PHASE_FAILED = 'VALIDATE_PHASE_FAILED'
    EXECUTE_PHASE_FAILED = 'EXECUTE_PHASE_FAILED'

    # Import controller
    INVALID_OPERATION = 'INVALID_OPERATION'
    CONTROLLER_IMPORT_ERROR = 'CONTROLLER_IMPORT_ERROR'
    CONTROLLER_CLASS_NOT_FOUND = 'CONTROLLER_CLASS_NOT_FOUND'
