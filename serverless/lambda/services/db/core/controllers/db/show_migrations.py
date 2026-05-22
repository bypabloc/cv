"""Controller db/show_migrations — historial de migraciones + actual.

Orquestador delgado: delega al service y normaliza el resultado. NO
contiene logica de negocio.

El command de invocacion es `show-migrations` (con guion); el handler lo
mapea a la action `show_migrations` (con underscore) para que el nombre
del modulo y de la clase sean identificadores Python validos.
"""

from __future__ import annotations

from models.db import ShowMigrationsModel
from services.db_service import ServiceError, run_show_migrations
from utils.base_controller import BaseController


class Show_migrations(BaseController):  # noqa: N801 - action.capitalize()
    """Controller para la accion 'show_migrations' de la operacion 'db'.

    El estandar exige que la clase se llame action.capitalize(); para la
    action 'show_migrations' eso es 'Show_migrations'.
    """

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
