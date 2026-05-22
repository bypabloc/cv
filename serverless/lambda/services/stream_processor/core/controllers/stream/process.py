"""Controller stream/process — replica un batch de Stream Records a Neon.

Orquestador delgado: toma el batch validado, delega cada record al
service y recolecta los `event_id` fallidos. NO contiene logica de
negocio (transformacion y escritura ORM viven en el service).
"""

from __future__ import annotations

from models.stream import StreamModel
from services.stream_service import process_record
from settings.config import logger
from shared.lambda_kit import BaseController


class Process(BaseController):
    """Controller para la accion 'process' de la operacion 'stream'.

    El nombre de la clase es action.capitalize()
    ('process' -> 'Process').
    """

    event_model = StreamModel

    def execute(self) -> dict:
        """Orquesta stream/process: itera el batch y delega al service.

        Returns
        -------
        dict
            `{is_valid: True, code: 0, data}` con el resumen del batch:
            `processed`, `skipped` y `failed_record_ids`. El controller
            NUNCA devuelve `is_valid: False` por un record fallido —
            un record que falla se reporta en `failed_record_ids` y el
            handler lo traduce a `batchItemFailures` para que AWS lo
            reintente.
        """
        data = self.validated_data  # StreamModel
        records = data.records

        processed = 0
        skipped = 0
        failed_record_ids: list[str] = []

        for record in records:
            event_id = record.get('eventID', '')
            if not event_id:
                skipped += 1
                continue

            try:
                result = process_record(record, event_id)
            except Exception:
                failed_record_ids.append(event_id)
                logger.exception(
                    'failed to process stream record',
                    extra={'event_id': event_id},
                )
                continue

            if result == 'processed':
                processed += 1
            else:
                skipped += 1

        return {
            'is_valid': True,
            'data': {
                'processed': processed,
                'skipped': skipped,
                'failed_record_ids': failed_record_ids,
            },
            'code': 0,
        }
