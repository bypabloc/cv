"""Controller db/seed — restaura un snapshot YAML del CV en la DB.

Orquestador delgado: delega al service y normaliza el resultado. NO
contiene logica de negocio (el guard confirm_overwrite es del service).
"""

from __future__ import annotations

from models.db import SeedModel
from services.db_service import ServiceError, run_seed
from shared.lambda_kit.base_controller import BaseController


class Seed(BaseController):
    """Controller para la accion 'seed' de la operacion 'db'."""

    event_model = SeedModel

    def execute(self) -> dict:
        """Orquesta db/seed: delega al service y normaliza la salida."""
        data = self.validated_data  # SeedModel
        try:
            result = run_seed(
                source=data.source,
                confirm_overwrite=data.confirm_overwrite,
            )
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
            'data': {'command': 'seed', 'status': 'ok', **result},
            'code': 0,
        }
