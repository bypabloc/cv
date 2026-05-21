"""Controller tracking/track — registra un evento de tracking.

Orquestador delgado: toma el payload validado (`TrackEventModel`),
aplica el rate-limit per-IP, delega el enrichment + persistencia al
service y normaliza el resultado a `{is_valid, data, code}`. NO contiene
logica de negocio.

Errores de negocio que el controller normaliza:
  - rate-limit (IP blacklist / country block / sliding window agotado):
    el `shared.rate_limit.check_or_raise` lanza una `ApplicationError`;
    el controller la captura y la traduce a `{is_valid: False}` con el
    `code` 4001 (RATE_LIMITED) y la `ApplicationError` original en `data`
    para que el handler la mapee a la respuesta HTTP correspondiente.
"""

from __future__ import annotations

from models.tracking import TrackEventModel
from services.tracking_service import process_tracking_event
from settings.config import ErrorCode
from shared.exceptions import ApplicationError
from shared.rate_limit import check_or_raise
from utils.base_controller import BaseController

# Endpoint que el rate-limit usa para resolver las rules.
_TRACK_ENDPOINT = '/track'


class Track(BaseController):
    """Controller para la accion 'track' de la operacion 'tracking'.

    El nombre de la clase es action.capitalize() ('track' -> 'Track').
    """

    event_model = TrackEventModel

    def execute(self) -> dict:
        """Orquesta tracking/track: rate-limit -> service -> normaliza."""
        data: TrackEventModel = self.validated_data  # TrackEventModel
        meta = data.meta

        # --- Rate-limit per-IP (mas laxo que /contact: 30/min) ---
        # check_or_raise lanza ApplicationError si la IP esta blacklisted,
        # el country bloqueado o el sliding window agotado.
        try:
            check_or_raise(
                ip=meta.ip,
                endpoint=_TRACK_ENDPOINT,
                country=meta.country,
                turnstile_validated=False,
            )
        except ApplicationError as exc:
            return {
                'is_valid': False,
                'data': {
                    'error_code': exc.code,
                    'message': exc.message or exc.code,
                    'application_error': exc,
                },
                'code': ErrorCode.RATE_LIMITED.value,
            }

        # --- Service: enrichment + persistencia ---
        result = process_tracking_event(
            validated_input=data.tracking_payload(),
            ip=meta.ip,
            user_agent=meta.user_agent,
            country=meta.country,
        )

        return {
            'is_valid': True,
            'data': {
                'operation': 'tracking',
                'action': 'track',
                'status': 'ok',
                **result,
            },
            'code': 0,
        }
