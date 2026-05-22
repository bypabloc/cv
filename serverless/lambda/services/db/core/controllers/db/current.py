"""Controller db/current — revision de Alembic aplicada actualmente.

Orquestador delgado: delega al service y normaliza el resultado. NO
contiene logica de negocio.
"""

from __future__ import annotations

from models.db import CurrentModel
from services.db_service import ServiceError, run_current
from shared.lambda_kit import BaseController


class Current(BaseController):
    """Controller para la accion 'current' de la operacion 'db'."""

    event_model = CurrentModel

    def execute(self) -> dict:
        """Orquesta db/current: delega al service y normaliza la salida."""
        try:
            result = run_current()
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
            'data': {'command': 'current', 'status': 'ok', **result},
            'code': 0,
        }
