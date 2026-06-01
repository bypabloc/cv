"""Controller tracking/track — encoder async (invoke) o sync (Neon legacy).

Orquestador con feature flag `AppConfig.async_mode`:

- `ASYNC_MODE=true` (default): encoder ligero. Aplica rate-limit, pre-
  genera `page_id` (UUIDv7) + `created_at`, invoca `tracking_writer`
  async (`InvocationType='Event'`, sin SQS) via `invoke_tracking_writer`
  y responde 202 con `TrackAcceptedOutput`. NO toca Neon, NO parsea UA
  (el writer lo hace, cacheado).
- `ASYNC_MODE=false`: comportamiento legacy. Rate-limit + UA parsing +
  escritura directa a Neon (`process_tracking_event`) + respuesta 204.
  Es el rollback de emergencia mientras dure el flag.

Rate-limit corre en AMBOS modos ANTES del branch (la metrica de bots
y proteccion DoS no depende del modo de persistencia).

Errores de negocio:
  - rate-limit -> `code` 4001 (RATE_LIMITED), `is_valid=False`. La
    `ApplicationError` viaja en `data['application_error']` para que el
    handler la mapee al HTTP correspondiente.
  - invoke failure (`LambdaInvokeError` u otra excepcion) -> propaga al
    handler como UNEXPECTED_ERROR, que la traduce a HTTP 502.

NO contiene logica de negocio: enrichment, persistencia e invoke
viven en `services/tracking_service.py`.
"""

from __future__ import annotations

from datetime import UTC, datetime

from models.tracking import TrackAcceptedOutput, TrackEventModel
from services.tracking_service import (
    invoke_tracking_writer,
    process_tracking_event,
)
from settings.config import AppConfig, ErrorCode
from shared.core.exceptions import ApplicationError
from shared.core.ulid import new_uuidv7
from shared.lambda_kit.base_controller import BaseController
from shared.rate_limit.check import check_or_raise

# Endpoint que el rate-limit usa para resolver las rules.
_TRACK_ENDPOINT = '/track'


class Track(BaseController):
    """Controller para la accion 'track' de la operacion 'tracking'.

    El nombre de la clase es action.capitalize() ('track' -> 'Track').
    """

    event_model = TrackEventModel

    def execute(self) -> dict:
        """Orquesta tracking/track: rate-limit -> branch por ASYNC_MODE."""
        data: TrackEventModel = self.validated_data  # TrackEventModel
        meta = data.meta

        # --- Rate-limit per-IP (IDENTICO en ambos modos) ---
        # check_or_raise lanza ApplicationError si la IP esta blacklisted,
        # el country bloqueado o el sliding window agotado. Corre ANTES
        # del branch: NO se debe encolar ni persistir si el cliente esta
        # rate-limited.
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

        # --- Branch por feature flag ---
        if AppConfig.async_mode:
            return self._execute_async(data=data, meta=meta)
        return self._execute_sync(data=data, meta=meta)

    def _execute_async(self, *, data: TrackEventModel, meta: object) -> dict:
        """Invoca `tracking_writer` async y responde 202 (ASYNC_MODE=true).

        El encoder pre-genera `page_id` (UUIDv7) y `created_at`: ambos
        viajan en el payload del invoke y en la respuesta. Asi el cliente
        recibe el id final sin esperar al writer, y el writer NO los
        regenera. Sin SQS: invoke Lambda->Lambda (InvocationType='Event').
        """
        payload = data.tracking_payload()
        page_id = new_uuidv7()
        created_at = datetime.now(UTC)

        invoke_tracking_writer(
            page_id=page_id,
            created_at=created_at,
            validated_input=payload,
            ip=meta.ip,  # type: ignore[attr-defined]
            user_agent=meta.user_agent,  # type: ignore[attr-defined]
            country=meta.country,  # type: ignore[attr-defined]
        )

        output = TrackAcceptedOutput(
            page_id=page_id,
            session_id=payload['session_id'],
            created_at=created_at,
            accepted=True,
        )
        return {
            'is_valid': True,
            'data': {
                'operation': 'tracking',
                'action': 'track',
                'status': 'accepted',
                **output.model_dump(mode='json'),
            },
            'code': 0,
        }

    def _execute_sync(self, *, data: TrackEventModel, meta: object) -> dict:
        """Persiste sincronamente a Neon y responde 204 (ASYNC_MODE=false).

        Modo legacy / rollback de emergencia. Replica el flujo del
        Lambda previo al refactor a encoder.
        """
        result = process_tracking_event(
            validated_input=data.tracking_payload(),
            ip=meta.ip,  # type: ignore[attr-defined]
            user_agent=meta.user_agent,  # type: ignore[attr-defined]
            country=meta.country,  # type: ignore[attr-defined]
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
