"""@module shared.lambda_kit.base_controller — clase base de los controllers.

Define el ciclo de vida estandar del estandar lambda-controller:
`preload -> validate -> execute`. Cada controller concreto solo
implementa `execute()`.

Era identico en los 4 Lambdas del backend; se unifico aca. Las dos
dependencias que antes venian de `settings.config` del Lambda se
resuelven asi:

- `logger`              : viene de `shared.observability` (ya es shared).
- `ErrorCode` / `LogMetricType` : vienen de `shared.lambda_kit` (los
  enums base se unificaron — ver `error_codes.py` / `log_metrics.py`).
- `app_config`          : lo INYECTA cada Lambda en su cold start con
  `set_app_config(app_config)`. `preload()` lo usa para resolver el ARN
  de un Lambda downstream. Un Lambda sin `arn_config_key` no necesita
  inyectarlo.
- `permission checker`  : lo INYECTA cada Lambda en su cold start con
  `set_permission_checker(fn)`. La fase Authorize de `run()` lo invoca
  para los controllers que declaran `required_permission`. El kit NUNCA
  importa `shared.auth`/`shared.db` (arrastraria pyjwt/sqlalchemy al
  vendoring de todos los Lambdas): el checker es del dominio del Lambda.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol

from pydantic import BaseModel, ValidationError

from shared.lambda_kit.error_codes import ErrorCode
from shared.lambda_kit.log_metrics import LogMetricType
from shared.observability.logger import logger

# AppConfig inyectado por el Lambda en su cold start. Solo lo necesita un
# controller con `arn_config_key` (resuelve el ARN de un Lambda
# downstream). Se mantiene como modulo-global para no cambiar la firma de
# los controllers ni del handler.
_app_config: object | None = None


class PermissionChecker(Protocol):
    """Contrato del checker de permisos inyectado por el Lambda.

    Recibe el permiso declarado por el controller, el `_meta` CRUDO del
    event (ip, authorization, ...) y el nombre de la action (clase del
    controller) para logging/auditoria. Si el caller NO tiene el permiso,
    RAISEA una `ApplicationError` (401/403/404 segun el dominio) que
    propaga hasta el `except ApplicationError` de `http_handler`. Si lo
    tiene, devuelve el subject autenticado (ej. `AuthUser`).
    """

    def __call__(
        self,
        permission: str,
        meta: dict[str, Any],
        *,
        action: str,
    ) -> Any: ...


_permission_checker: PermissionChecker | None = None


def set_app_config(app_config: object) -> None:
    """Inyecta el `AppConfig` del Lambda para que `preload()` resuelva ARNs.

    El Lambda lo llama una vez en el cold start (tipicamente desde
    `settings/config.py` o el `handler.py`). Un Lambda cuyos controllers
    no tienen `arn_config_key` no necesita llamarlo.
    """
    global _app_config
    _app_config = app_config


def set_permission_checker(checker: PermissionChecker | None) -> None:
    """Inyecta el checker que resuelve `required_permission` en Authorize.

    El Lambda lo llama una vez en el cold start (desde su `handler.py`).
    Un Lambda cuyos controllers no declaran `required_permission` no
    necesita llamarlo. Pasar `None` lo des-registra (util en tests).
    """
    global _permission_checker
    _permission_checker = checker


class BaseController(ABC):
    """Clase base para todos los controllers de un Lambda.

    El metodo `run()` orquesta tres fases:
      1. `preload`  - carga configuracion (ej. ARN de un Lambda downstream).
      2. `validate` - valida el evento contra `event_model` (Pydantic).
      3. `execute`  - logica de negocio del controller (abstracto).

    El metodo `run()` antepone una fase Authorize cuando la subclase
    declara `required_permission`: invoca el checker inyectado con
    `set_permission_checker()` ANTES de preload/validate (un caller sin
    permiso recibe su 401/403/404 sin filtrar detalles de validacion ni
    consumir rate-limit del execute).

    Atributos de clase a definir en cada subclase:
      - `event_model`         : modelo Pydantic que valida el payload.
      - `arn_config_key`      : nombre del campo de `AppConfig` con el ARN
                                downstream. Vacio si el controller no
                                invoca otro Lambda.
      - `required_permission` : permiso que el caller debe tener (ej.
                                'admin'). None (default) = endpoint sin
                                auth declarativa.
    """

    event_model: type[BaseModel] | None = None
    arn_config_key: str = ''
    required_permission: str | None = None

    def __init__(self, event: dict[str, Any]) -> None:
        self.event = event
        self.validated_data: BaseModel | None = None
        self.arn: str = ''
        # Subject autenticado que devolvio el permission checker en la
        # fase Authorize (ej. AuthUser). None si no hay required_permission.
        self.permission_subject: Any = None

    def preload(self) -> dict[str, Any]:
        """Carga configuracion previa a la ejecucion.

        Por defecto resuelve el ARN downstream desde `arn_config_key`
        contra el `AppConfig` inyectado. Sobrescribir si el controller
        necesita otra preparacion.
        """
        if not self.arn_config_key:
            return {'is_valid': True, 'data': {}, 'code': 0}

        self.arn = getattr(_app_config, self.arn_config_key, '')
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

    def validate(self) -> dict[str, Any]:
        """Valida el evento contra `event_model` (Pydantic)."""
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
        except Exception as exc:
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
    def execute(self) -> dict[str, Any]:
        """Logica principal del controller.

        Debe implementarse en cada subclase y devolver
        `{is_valid, data, code}`.
        """

    def authorize(self) -> dict[str, Any]:
        """Resuelve `required_permission` contra el checker inyectado.

        No-op si el controller no declara `required_permission`. Si lo
        declara y no hay checker inyectado -> CONFIGURATION_MISSING (el
        Lambda olvido llamar `set_permission_checker` en su cold start).
        El rechazo de permiso NO devuelve `{is_valid: False}`: el checker
        RAISEA una `ApplicationError` (401/403/404) que propaga limpia
        por `run_controller` hasta `http_handler` (metrica rejected).
        """
        if self.required_permission is None:
            return {'is_valid': True, 'data': {}, 'code': 0}

        if _permission_checker is None:
            return {
                'is_valid': False,
                'data': {
                    'error_code': 'CONFIGURATION_MISSING',
                    'message': 'permission checker no configurado',
                },
                'code': ErrorCode.CONFIGURATION_MISSING.value,
            }

        # _meta del event CRUDO: validate aun no corrio (validated_data
        # es None en esta fase).
        meta: dict[str, Any] = (self.event or {}).get('_meta') or {}
        self.permission_subject = _permission_checker(
            self.required_permission,
            meta,
            action=type(self).__name__,
        )
        return {'is_valid': True, 'data': {}, 'code': 0}

    def run(self) -> dict[str, Any]:
        """Ejecuta `authorize -> preload -> validate -> execute` con logging."""
        # --- Authorize ---
        if self.required_permission is not None:
            logger.info(
                'Starting authorize phase',
                extra={
                    'metric_type': LogMetricType.PHASE_START.value,
                    'phase': 'AUTHORIZE',
                },
            )
            authorize_result = self.authorize()
            if not authorize_result.get('is_valid', True):
                logger.error(
                    'Authorize phase failed',
                    extra={
                        'metric_type': (
                            LogMetricType.AUTHORIZE_PHASE_FAILED.value
                        ),
                    },
                )
                return authorize_result

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

        # Guard: validated_data debe estar seteado si hay event_model.
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
