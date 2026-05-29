"""Controller db/downgrade — revierte migraciones (operacion destructiva).

Orquestador delgado: valida la regla de negocio `confirm`, delega al
service y normaliza el resultado. La verificacion de `confirm: true` es
la salvaguarda contra un downgrade accidental en prod.
"""

from __future__ import annotations

from models.db import DowngradeModel
from services.db_service import ServiceError, run_downgrade
from settings.config import ErrorCode
from shared.lambda_kit.base_controller import BaseController


class Downgrade(BaseController):
    """Controller para la accion 'downgrade' de la operacion 'db'."""

    event_model = DowngradeModel

    def execute(self) -> dict:
        """Orquesta db/downgrade: exige `confirm`, delega al service."""
        data = self.validated_data  # DowngradeModel

        if data.confirm is not True:
            return {
                'is_valid': False,
                'data': {
                    'error_code': 'DOWNGRADE_NOT_CONFIRMED',
                    'message': (
                        "downgrade es destructivo — pasa 'confirm': true "
                        'en data para ejecutarlo.'
                    ),
                },
                'code': ErrorCode.DOWNGRADE_NOT_CONFIRMED.value,
            }

        try:
            result = run_downgrade(target=data.target)
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
            'data': {'command': 'downgrade', 'status': 'ok', **result},
            'code': 0,
        }
