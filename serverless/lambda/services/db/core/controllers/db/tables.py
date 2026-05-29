"""Controller db/tables — lista las tablas de la DB con estimado de filas.

Orquestador delgado: delega al service y normaliza el resultado. NO
contiene logica de negocio.
"""

from __future__ import annotations

from models.db import TablesModel
from services.db_service import ServiceError, run_tables
from shared.lambda_kit.base_controller import BaseController


class Tables(BaseController):
    """Controller para la accion 'tables' de la operacion 'db'."""

    event_model = TablesModel

    def execute(self) -> dict:
        """Orquesta db/tables: delega al service y normaliza la salida."""
        try:
            result = run_tables()
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
            'data': {'command': 'tables', 'status': 'ok', **result},
            'code': 0,
        }
