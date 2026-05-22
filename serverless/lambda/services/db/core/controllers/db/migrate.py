"""Controller db/migrate — aplica las migraciones pendientes.

Orquestador delgado: toma el payload validado, delega al service y
normaliza el resultado a {is_valid, data, code}. NO contiene logica de
negocio.
"""

from __future__ import annotations

from models.db import MigrateModel
from services.db_service import ServiceError, run_migrate
from utils.base_controller import BaseController


class Migrate(BaseController):
    """Controller para la accion 'migrate' de la operacion 'db'.

    El nombre de la clase es action.capitalize() ('migrate' -> 'Migrate').
    """

    event_model = MigrateModel

    def execute(self) -> dict:
        """Orquesta db/migrate: delega al service y normaliza la salida."""
        data = self.validated_data  # MigrateModel

        try:
            result = run_migrate(target=data.target)
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
            'data': {'command': 'migrate', 'status': 'ok', **result},
            'code': 0,
        }
