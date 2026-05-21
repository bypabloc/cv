"""Lambda `stream_processor` — DynamoDB Streams -> replica Neon PostgreSQL.

Triggered por el Event Source Mapping de los DynamoDB Streams (contacts +
tracking). Batch size 100, ventana 10s. Devuelve `batchItemFailures` para
que AWS reintente solo los records fallidos (los demas avanzan).

Idempotencia: cada Stream record trae un `eventID` unico. Antes de insertar
se verifica en `processed_stream_events`; el INSERT del dato + su fila de
idempotencia confirman en la MISMA transaccion.

Persistencia: via los modelos ORM de `shared/db/` (una `Session` por record).
"""

from typing import Any

from aws_lambda_powertools.metrics import MetricUnit

from shared.db.session import db_session
from shared.logger import logger
from shared.metrics import metrics
from shared.tracer import tracer
from stream_processor.pg_writer import (
    insert_contact,
    insert_tracking,
    is_event_processed,
    mark_event_processed,
)
from stream_processor.transformers import (
    detect_table,
    parse_contact_record,
    parse_tracking_record,
)


def _process_record(record: dict[str, Any], event_id: str) -> str:
    """Procesa un record del Stream dentro de su propia transaccion.

    Returns:
        `'processed'` si se replico una fila, `'skipped'` si el record no
        aplica (ya procesado, no-INSERT, imagen incompleta o tabla
        desconocida).

    Raises:
        Exception: cualquier fallo de DB; el handler lo cuenta como fallido
        y deja que `db_session()` haga rollback.
    """
    with db_session() as session:
        if is_event_processed(session, event_id):
            logger.debug('event already processed', extra={'event_id': event_id})
            return 'skipped'

        table = detect_table(record)
        if table == 'contacts':
            payload = parse_contact_record(record)
            if payload is None:
                return 'skipped'
            insert_contact(session, payload)
        elif table == 'tracking':
            payload = parse_tracking_record(record)
            if payload is None:
                return 'skipped'
            insert_tracking(session, payload)
        else:
            logger.warning(
                'unknown table in stream record',
                extra={'event_source_arn': record.get('eventSourceARN', '')},
            )
            return 'skipped'

        mark_event_processed(
            session,
            event_id,
            event_type=record.get('eventName', ''),
            table_name=table,
        )
        return 'processed'


@logger.inject_lambda_context(log_event=False)
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Procesa una batch de records del DynamoDB Stream."""
    records = event.get('Records', [])
    processed = 0
    skipped = 0
    failed_record_ids: list[str] = []

    for record in records:
        event_id = record.get('eventID', '')
        if not event_id:
            skipped += 1
            continue

        try:
            result = _process_record(record, event_id)
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

    metrics.add_metric(
        name='StreamRecordsProcessed', unit=MetricUnit.Count, value=processed
    )
    metrics.add_metric(
        name='StreamRecordsSkipped', unit=MetricUnit.Count, value=skipped
    )
    if failed_record_ids:
        metrics.add_metric(
            name='StreamRecordsFailed',
            unit=MetricUnit.Count,
            value=len(failed_record_ids),
        )

    # `ReportBatchItemFailures`: los records de `batchItemFailures` se
    # reintenta; los OK avanzan.
    return {
        'batchItemFailures': [
            {'itemIdentifier': eid} for eid in failed_record_ids
        ],
    }
