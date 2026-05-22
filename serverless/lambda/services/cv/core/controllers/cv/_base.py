"""Base comun de los controllers de la operacion `cv`.

Todos los controllers `cv/<action>` siguen el mismo patron:
1. extraer niche/locale del payload validado (`CvQueryModel`);
2. invocar la funcion correspondiente del `cv_service`;
3. normalizar la salida a `{is_valid, data, code}`.

`CvControllerBase` concentra el (2)+(3); cada subclase solo declara que
funcion invocar via `service_call`. Asi cada controller es < 10 lineas.

Prefijo `_` para que no se descubra como action — solo es un helper.
"""

from __future__ import annotations

from typing import Any

from models.cv import CvQueryModel
from services import cv_service
from services.cv_service import ServiceError
from shared.lambda_kit import BaseController


class CvControllerBase(BaseController):
    """Base de todos los controllers de `cv`.

    Las subclases declaran `service_name` (el nombre del attr de
    `services.cv_service` a invocar, p.ej. 'list_experiences') y
    opcionalmente `requires_niche` (default True; profile usa False).

    Importante: resolvemos el service POR NOMBRE en cada `execute()`, no
    por referencia capturada en clase. Asi `patch('services.cv_service.X')`
    en los tests intercepta de verdad — un `staticmethod(X)` capturaria
    la referencia original al cargar el modulo.
    """

    event_model = CvQueryModel
    service_name: str
    requires_niche: bool = True

    def execute(self) -> dict:
        """Orquesta la action: llama al service y normaliza la salida."""
        data: CvQueryModel = self.validated_data  # type: ignore[assignment]
        niche = data.normalized_niche()
        locale = data.locale

        service_fn = getattr(cv_service, self.__class__.service_name)
        try:
            kwargs: dict[str, Any] = {'locale': locale}
            if self.requires_niche:
                kwargs['niche'] = niche
            result = service_fn(**kwargs)
        except ServiceError as exc:
            return {
                'is_valid': False,
                'data': {
                    'error_code': exc.error_code,
                    'message': exc.message,
                },
                'code': exc.code,
            }

        return {
            'is_valid': True,
            'data': result,
            'code': 0,
        }
