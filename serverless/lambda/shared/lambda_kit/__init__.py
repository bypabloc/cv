"""@package shared.lambda_kit — kit comun del estandar lambda-controller.

Unifica el codigo que era identico en los 4 Lambdas del backend:

- `base_controller` : `BaseController` (ciclo preload->validate->execute).
- `base_settings`   : `BaseSettings` (config por variables de entorno).
- `import_controller` : import dinamico de controllers por operation+action.
- `event_model`     : factory `build_event_model(OPERATIONS)`.
- `validation.event`: `validate_event` (wrapper con manejo de errores).
- `dispatch`        : `run_controller` (nucleo del handler).
- `error_codes` / `log_metrics` : enums base (`ErrorCode`,
  `LogMetricType`).

Las dependencias que antes venian del `settings/` de cada Lambda se
resuelven por inyeccion (`set_app_config`) o por parametro (`OPERATIONS`,
`EventModel`), de modo que `lambda_kit` no depende de ningun Lambda.
"""

from shared.lambda_kit.base_controller import BaseController, set_app_config
from shared.lambda_kit.base_settings import BaseSettings
from shared.lambda_kit.dispatch import DispatchResult, run_controller
from shared.lambda_kit.error_codes import ErrorCode
from shared.lambda_kit.event_model import build_event_model
from shared.lambda_kit.import_controller import (
    import_controller,
    resolve_operation,
)
from shared.lambda_kit.log_metrics import LogMetricType
from shared.lambda_kit.validation.event import validate_event

__all__ = [
    'BaseController',
    'BaseSettings',
    'DispatchResult',
    'ErrorCode',
    'LogMetricType',
    'build_event_model',
    'import_controller',
    'resolve_operation',
    'run_controller',
    'set_app_config',
    'validate_event',
]
