"""Controller cv/certificates — certificados filtrados por niche.

`list_certificates` del service no acepta `locale` (no hay campos
bilingues). El controller hace override de `execute()` para llamarlo sin
ese kwarg, manteniendo el patron de normalizacion del base.
"""

from typing import Any

from controllers.cv._base import CvControllerBase
from models.cv import CvQueryModel
from services import cv_service
from services.cv_service import ServiceError


class Certificates(CvControllerBase):
    """Devuelve la lista de certificados (sin locale)."""

    service_name = 'list_certificates'

    def execute(self) -> dict[str, Any]:
        """Igual que el base pero llama al service sin locale."""
        data: CvQueryModel = self.validated_data  # type: ignore[assignment]
        niche = data.normalized_niche()
        try:
            result = cv_service.list_certificates(niche=niche)
        except ServiceError as exc:
            return {
                'is_valid': False,
                'data': {
                    'error_code': exc.error_code,
                    'message': exc.message,
                },
                'code': exc.code,
            }
        return {'is_valid': True, 'data': result, 'code': 0}
