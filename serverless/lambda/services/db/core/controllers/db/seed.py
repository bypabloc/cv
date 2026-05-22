"""Controller db/seed — carga data de prueba en la DB.

Orquestador delgado: delega al service y normaliza el resultado. NO
contiene logica de negocio.
"""

from __future__ import annotations

from models.db import SeedModel
from services.db_service import ServiceError, run_seed
from utils.base_controller import BaseController


class Seed(BaseController):
    """Controller para la accion 'seed' de la operacion 'db'."""

    event_model = SeedModel

    def execute(self) -> dict:
        """Orquesta db/seed: delega al service y normaliza la salida."""
        try:
            result = run_seed()
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
