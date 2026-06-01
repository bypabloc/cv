"""Controller db/stamp — marca una revision como aplicada sin ejecutar SQL.

Orquestador delgado: delega al service y normaliza el resultado. NO
contiene logica de negocio.
"""

from __future__ import annotations

from models.db import StampModel
from services.db_service import ServiceError, run_stamp
from shared.lambda_kit.base_controller import BaseController


class Stamp(BaseController):
    """Controller para la accion 'stamp' de la operacion 'db'."""

    event_model = StampModel

    def execute(self) -> dict:
        """Orquesta db/stamp: delega al service y normaliza la salida."""
        data = self.validated_data  # StampModel

        try:
            result = run_stamp(target=data.target)
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
            'data': {'command': 'stamp', 'status': 'ok', **result},
            'code': 0,
        }
