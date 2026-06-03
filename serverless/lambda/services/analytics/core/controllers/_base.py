"""Base comun de TODOS los controllers del Lambda `analytics`.

Cada controller `<operation>/<action>` sigue el mismo ciclo en `execute()`:

1. **auth** — `auth_guard.require_auth(_meta.authorization)`: valida el
   access JWT. Sin JWT valido -> ApplicationError(401) (la mapea
   http_handler). Es lo PRIMERO: un 401 NO consume slot del rate-limit
   (AC-23).
2. **rate-limit** — `rate_limit_guard.guard(ip, country)`: segunda capa.
3. **service** — resuelve la funcion del service POR NOMBRE en cada
   `execute()` (no por referencia capturada en clase) y la llama con los
   kwargs que extrae `self.service_kwargs(data)`. Resolver por nombre hace
   que `patch('services.<X>.<fn>')` en los tests intercepte de verdad.
4. **shape** — normaliza a `{is_valid, data, code}`; traduce `ServiceError`
   a `{is_valid: False, code}`.

Cada subclase concreta declara `event_model`, `service_module` (modulo del
service, ej. 'services.funnel_service') y `service_name` (la funcion, ej.
'conversion'), e implementa `service_kwargs(data)`.

Prefijo `_` en el modulo: helper compartido, no es una action.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from services._errors import ServiceError
from shared.lambda_kit.base_controller import BaseController
from utils.auth_guard import require_auth
from utils.rate_limit_guard import guard as rate_limit_guard


class AnalyticsControllerBase(BaseController):
    """Base de todos los controllers del Lambda `analytics`."""

    # Cada subclase setea estos tres:
    service_module: str
    service_name: str

    def service_kwargs(self, data: Any) -> dict[str, Any]:
        """Devuelve los kwargs a pasar al service. La subclase lo implementa."""
        raise NotImplementedError

    def _resolve_service(self) -> Any:
        """Resuelve la callable del service por nombre (testeable con patch)."""
        module = import_module(type(self).service_module)
        return getattr(module, type(self).service_name)

    def execute(self) -> dict[str, Any]:
        """Orquesta auth -> rate-limit -> service -> shape."""
        data = self.validated_data
        meta = data.meta

        # 1. Auth (ApplicationError 401/403 se propaga a http_handler).
        require_auth(authorization=meta.authorization)

        # 2. Rate-limit (segunda capa).
        rate_limit_guard(ip=meta.ip, country=meta.country)

        # 3. Service (resuelto por nombre para testeabilidad).
        service_fn = self._resolve_service()
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
