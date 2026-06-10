"""Base comun de TODOS los controllers del Lambda `cv_admin`.

Cada controller `<operation>/<action>` sigue el mismo ciclo en `execute()`:

1. **auth** — `require_active_user(_meta.authorization)`: valida el access
   JWT (firma + blacklist + status en Neon). Sin JWT valido ->
   ApplicationError(401) (la mapea http_handler). Es lo PRIMERO: un 401
   NO consume slot del rate-limit.
2. **admin** — `require_admin_user(user)`: whitelist SSM `admin-emails`.
   NO-admin -> AdminAuthzError(404 NOT_FOUND, anti-enumeration).
3. **rate-limit** — `RateLimitService.check_or_raise` con el `endpoint`
   declarado por la subclase (`turnstile_validated=False`, JWT-authed).
4. **service** — resuelve la funcion del service POR NOMBRE en cada
   `execute()` (no por referencia capturada en clase) y la llama con los
   kwargs que extrae `self.service_kwargs(data)`. Resolver por nombre hace
   que `monkeypatch` del modulo del service intercepte de verdad.
5. **shape** — normaliza a `{is_valid, data, code}`; traduce `ServiceError`
   a `{is_valid: False, code, status}`.

Cada subclase concreta declara `event_model`, `endpoint`, `service_module`
y `service_name`, e implementa `service_kwargs(data)`. Las dos familias de
content (upsert/delete) tienen bases intermedias que solo piden `entity`.

Prefijo `_` en el modulo: helper compartido, no es una action.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from services._errors import ServiceError
from services.admin_guard import require_admin_user
from services.jwt_service import require_active_user
from services.rate_limit_service import RateLimitService
from settings.config import app_config
from shared.lambda_kit.base_controller import BaseController

# Mapeo del code interno del ServiceError al HTTP status que el controller
# le pide a http_handler (via el campo `status` del resultado).
_CODE_TO_STATUS: dict[int, int] = {
    1100: 400,  # UNKNOWN_NICHE (validacion contra el catalogo)
    1101: 400,  # REORDER_SLUGS_MISMATCH
    4404: 404,  # SLUG_NOT_FOUND / NICHE_NOT_FOUND
    5200: 502,  # GITHUB_API_ERROR
}


class CvAdminControllerBase(BaseController):
    """Base de todos los controllers de `cv_admin` (admin-only)."""

    # Cada subclase setea estos tres + event_model:
    endpoint: str
    service_module: str
    service_name: str

    def service_kwargs(self, data: Any) -> dict[str, Any]:
        """Devuelve los kwargs a pasar al service. La subclase lo define."""
        raise NotImplementedError

    def _resolve_service(self) -> Any:
        """Resuelve la callable del service por nombre (testeable)."""
        module = import_module(type(self).service_module)
        return getattr(module, type(self).service_name)

    @staticmethod
    def _payload(data: Any) -> dict[str, Any]:
        """Vuelca el modelo al shape YAML del seed (camelCase, sin _meta)."""
        return data.model_dump(
            by_alias=True, exclude_none=True, exclude={'meta'},
        )

    def execute(self) -> dict[str, Any]:
        """Orquesta auth -> admin -> rate-limit -> service -> shape."""
        data = self.validated_data
        meta = data.meta  # type: ignore[union-attr]

        # 1. Auth (ApplicationError 401/403 se propaga a http_handler).
        user = require_active_user(meta.authorization, app_config=app_config)

        # 2. Scope admin (AdminAuthzError 404 anti-enumeration).
        require_admin_user(
            user,
            ip=meta.ip,
            audit_action=f'cv-admin.{type(self).service_name}',
        )

        # 3. Rate-limit (segunda capa, sin Turnstile).
        RateLimitService(app_config).check_or_raise(
            ip=meta.ip or '',
            endpoint=type(self).endpoint,
            country=meta.country,
        )

        # 4. Service (resuelto por nombre para testeabilidad).
        service_fn = self._resolve_service()
        try:
            result = service_fn(**self.service_kwargs(data))
        except ServiceError as exc:
            # `status` HTTP explicito para que http_handler NO colapse el
            # error a INVALID_REQUEST/400 generico.
            error_data: dict[str, Any] = {
                'error_code': exc.error_code,
                'message': exc.message,
            }
            if exc.detail:
                error_data['detail'] = exc.detail
            return {
                'is_valid': False,
                'status': _CODE_TO_STATUS.get(exc.code, 400),
                'data': error_data,
                'code': exc.code,
            }

        # 5. Shape.
        return {'is_valid': True, 'data': result, 'code': 0}


class ContentUpsertBase(CvAdminControllerBase):
    """Base de los upsert-<entidad> de la operation `content`.

    La subclase declara `event_model` (el modelo de la entidad) y
    `entity` (la clave del upsert en `content_service`).
    """

    entity: str
    endpoint = '/cv-admin#content'
    service_module = 'services.content_service'
    service_name = 'upsert_entity'

    def service_kwargs(self, data: Any) -> dict[str, Any]:
        """Pasa la entidad + el payload en shape YAML del seed."""
        return {'entity': type(self).entity, 'data': self._payload(data)}


class ContentDeleteBase(CvAdminControllerBase):
    """Base de los delete-<entidad> de la operation `content`.

    La subclase declara solo `entity`; el payload es `DeleteIn` ({slug}).
    """

    entity: str
    endpoint = '/cv-admin#content'
    service_module = 'services.content_service'
    service_name = 'delete_entity'

    def service_kwargs(self, data: Any) -> dict[str, Any]:
        """Pasa la entidad + el slug a borrar."""
        return {'entity': type(self).entity, 'slug': data.slug}
