"""Base comun de los controllers ADMIN del Lambda `cv` (content/publish).

El auth (access JWT + whitelist admin) ya NO vive aqui: lo declara
`required_permission = 'admin'` y lo resuelve la fase Authorize de
`BaseController.run()` (lambda_kit) ANTES de preload/validate, con el
checker que `handler.py` registra en cold start
(`services.permission_checker`). Un caller sin permiso recibe su
401/403/404 sin consumir slot de rate-limit ni filtrar detalles de
validacion.

Cada controller `<operation>/<action>` sigue este ciclo en `execute()`:

1. **rate-limit** — `RateLimitService.check_or_raise` con el `endpoint`
   declarado por la subclase (`turnstile_validated=False`, JWT-authed).
2. **service** — resuelve la funcion del service POR NOMBRE en cada
   `execute()` (no por referencia capturada en clase) y la llama con los
   kwargs que extrae `self.service_kwargs(data)`. Resolver por nombre hace
   que `monkeypatch` del modulo del service intercepte de verdad.
3. **shape** — normaliza a `{is_valid, data, code}`; traduce `ServiceError`
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
from services.cv_service import ServiceError as CvServiceError
from services.rate_limit_service import RateLimitService
from settings.config import app_config
from shared.lambda_kit.base_controller import BaseController

# Mapeo del code interno del ServiceError al HTTP status que el controller
# le pide a http_handler (via el campo `status` del resultado).
_CODE_TO_STATUS: dict[int, int] = {
    1100: 400,  # UNKNOWN_NICHE (validacion contra el catalogo)
    1101: 400,  # REORDER_SLUGS_MISMATCH
    1102: 400,  # INVALID_FIELD_VALUE (coercion fallida, ej. fecha YYYY-13)
    4404: 404,  # SLUG_NOT_FOUND / NICHE_NOT_FOUND
    5200: 502,  # GITHUB_API_ERROR
}


class CvAdminControllerBase(BaseController):
    """Base de los controllers admin del Lambda `cv` (content/publish)."""

    # Auth declarativa: la resuelve la fase Authorize del kit con el
    # checker registrado por handler.py (JWT access + whitelist admin).
    required_permission = 'admin'

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
        """Orquesta rate-limit -> service -> shape (auth ya corrio)."""
        data = self.validated_data
        meta = data.meta  # type: ignore[union-attr]

        # 1. Rate-limit (el auth ya paso en la fase Authorize, sin
        #    Turnstile: un 401 nunca llega aqui ni consume slot).
        RateLimitService(app_config).check_or_raise(
            ip=meta.ip or '',
            endpoint=type(self).endpoint,
            country=meta.country,
        )

        # 2. Service (resuelto por nombre para testeabilidad). Atrapa
        #    AMBOS ServiceError del Lambda: el del dominio admin
        #    (services._errors, con detail) y el de cv_service (get-all
        #    delega en la lectura cacheada del CV).
        service_fn = self._resolve_service()
        try:
            result = service_fn(**self.service_kwargs(data))
        except (ServiceError, CvServiceError) as exc:
            # `status` HTTP explicito para que http_handler NO colapse el
            # error a INVALID_REQUEST/400 generico.
            error_data: dict[str, Any] = {
                'error_code': exc.error_code,
                'message': exc.message,
            }
            detail = getattr(exc, 'detail', None)
            if detail:
                error_data['detail'] = detail
            return {
                'is_valid': False,
                'status': _CODE_TO_STATUS.get(exc.code, 400),
                'data': error_data,
                'code': exc.code,
            }

        # 3. Shape.
        return {'is_valid': True, 'data': result, 'code': 0}


class ContentUpsertBase(CvAdminControllerBase):
    """Base de los upsert-<entidad> de la operation `content`.

    La subclase declara `event_model` (el modelo de la entidad) y
    `entity` (la clave del upsert en `content_service`).
    """

    entity: str
    endpoint = '/cv#content'
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
    endpoint = '/cv#content'
    service_module = 'services.content_service'
    service_name = 'delete_entity'

    def service_kwargs(self, data: Any) -> dict[str, Any]:
        """Pasa la entidad + el slug a borrar."""
        return {'entity': type(self).entity, 'slug': data.slug}
