"""Controller db/show_migrations — historial de migraciones + actual.

Orquestador delgado: delega al service y normaliza el resultado. NO
contiene logica de negocio.

El command de invocacion es `show-migrations` (con guion). El kit
`import_controller` normaliza la action a snake_case para el modulo
(`show_migrations.py`) y a PascalCase para la clase (`ShowMigrations`),
siguiendo el estandar lambda-controller.
"""

from __future__ import annotations

from models.db import ShowMigrationsModel
from services.db_service import ServiceError, run_show_migrations
from shared.lambda_kit.base_controller import BaseController


class ShowMigrations(BaseController):
    """Controller para la accion 'show-migrations' de la operacion 'db'."""

    event_model = ShowMigrationsModel

    def execute(self) -> dict:
        """Orquesta db/show_migrations: delega al service y normaliza."""
        try:
            result = run_show_migrations()
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
            'data': {
                'command': 'show-migrations',
                'status': 'ok',
                **result,
            },
            'code': 0,
        }
