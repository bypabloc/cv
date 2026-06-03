"""Base comun de TODOS los controllers del Lambda `analytics`.

Cada controller `<operation>/<action>` sigue el mismo ciclo en `execute()`:

1. **auth** — `auth_guard.require_auth(_meta.authorization)`: valida el
   access JWT. Sin JWT valido -> ApplicationError(401) (la mapea
   http_handler). Es lo PRIMERO: un 401 NO consume slot del rate-limit.
2. **rate-limit** — `rate_limit_guard.guard(ip, country)`: segunda capa.
3. **service** — llama a la funcion del service del dominio con los kwargs
   que extrae `self.service_kwargs()`.
4. **shape** — normaliza a `{is_valid, data, code}`; traduce `ServiceError`
   a `{is_valid: False, code}`.

Cada subclase concreta solo declara `event_model`, `service` (la callable
del service del dominio) e implementa `service_kwargs()`. Asi cada
controller es de pocas lineas.

Prefijo `_` en el modulo: helper compartido, no es una action.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from services._errors import ServiceError
from shared.lambda_kit.base_controller import BaseController
from utils.auth_guard import require_auth
from utils.rate_limit_guard import guard as rate_limit_guard


class AnalyticsControllerBase(BaseController):
    """Base de todos los controllers del Lambda `analytics`.

    Las subclases declaran:
      - `event_model`: el modelo Pydantic de input (subclase con `meta`).
      - `service`: la callable del service del dominio (resuelta por
        nombre en cada `execute()` para que el patch de tests intercepte).

    e implementan `service_kwargs(data)` devolviendo los kwargs del service.
    """

    # Cada subclase setea estos:
    service: Callable[..., Any]

    def service_kwargs(self, data: Any) -> dict[str, Any]:
        """Devuelve los kwargs a pasar al service. Subclase lo implementa."""
        raise NotImplementedError

    def _meta(self, data: Any) -> Any:
        """Devuelve el sub-modelo `_meta` del input validado."""
        return data.meta

    def execute(self) -> dict[str, Any]:
        """Orquesta auth -> rate-limit -> service -> shape."""
        data = self.validated_data
        meta = self._meta(data)

        # 1. Auth (ApplicationError 401/403 se propaga a http_handler).
        require_auth(authorization=meta.authorization)

        # 2. Rate-limit (segunda capa).
        rate_limit_guard(ip=meta.ip, country=meta.country)

        # 3. Service.
        service_fn = type(self).service
        try:
            result = service_fn(**self.service_kwargs(data))
        except ServiceError as exc:
            return {
                'is_valid': False,
                'data': {
                    'error_code': exc.error_code,
                    'message': exc.message,
                },
                'code': exc.code,
            }

        # 4. Shape.
        return {'is_valid': True, 'data': result, 'code': 0}
