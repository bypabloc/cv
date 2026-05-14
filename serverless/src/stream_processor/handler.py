"""
Lambda handler: DynamoDB Streams -> Neon PG replica.

Triggered por Event Source Mapping de DynamoDB Streams (contacts + tracking).
Batch size 100, window 10s. Si TODA la batch falla -> DLQ.

Idempotency: cada Stream record tiene eventID unico. Checamos en
processed_stream_events antes de insertar.
"""

from __future__ import annotations

from typing import Any

from aws_lambda_powertools.metrics import MetricUnit

from common.logger import logger
from common.metrics import metrics
from common.tracer import tracer
from stream_processor.pg_writer import (
    commit,
    is_event_processed,
    mark_event_processed,
    rollback,
    upsert_contact,
    upsert_tracking,
)
from stream_processor.transformers import (
    detect_table,
    parse_contact_record,
    parse_tracking_record,
)


@logger.inject_lambda_context(log_event=False)
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Procesa batch de records del DynamoDB Stream."""
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
            # Idempotency check
            if is_event_processed(event_id):
                skipped += 1
                logger.debug('event already processed', extra={'event_id': event_id})
                continue

            table = detect_table(record)
            if table == 'contacts':
                payload = parse_contact_record(record)
                if payload is None:
                    skipped += 1
                    continue
                upsert_contact(payload)
                mark_event_processed(
                    event_id,
                    event_type=record.get('eventName', ''),
                    table_name='contacts',
                )
                commit()
                processed += 1

            elif table == 'tracking':
                payload = parse_tracking_record(record)
                if payload is None:
                    skipped += 1
                    continue
                upsert_tracking(payload)
                mark_event_processed(
                    event_id,
                    event_type=record.get('eventName', ''),
                    table_name='tracking',
                )
                commit()
                processed += 1

            else:
                skipped += 1
                logger.warning(
                    'unknown table in stream record',
                    extra={'event_source_arn': record.get('eventSourceARN', '')},
                )

        except Exception:
            rollback()
            failed_record_ids.append(event_id)
            logger.exception(
                'failed to process stream record',
                extra={'event_id': event_id},
            )

    metrics.add_metric(name='StreamRecordsProcessed', unit=MetricUnit.Count, value=processed)
    metrics.add_metric(name='StreamRecordsSkipped', unit=MetricUnit.Count, value=skipped)
    if failed_record_ids:
        metrics.add_metric(
            name='StreamRecordsFailed',
            unit=MetricUnit.Count,
            value=len(failed_record_ids),
        )

    # AWS Lambda con report batch item failures: si retornamos
    # `batchItemFailures` los records fallidos se reintenten (otros OK
    # avanzan).
    return {
        'batchItemFailures': [
            {'itemIdentifier': eid} for eid in failed_record_ids
        ],
    }
