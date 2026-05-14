"""
Lambda handler: scheduled cron 03:00 UTC daily.

Triggered por EventBridge Scheduled Rule. Computa daily_metrics para
yesterday + refresca MVs + cleanup processed_stream_events.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from typing import Any

from aws_lambda_powertools.metrics import MetricUnit

from common.logger import logger
from common.metrics import metrics
from common.tracer import tracer
from aggregator.queries import (
    CLEANUP_OLD_EVENTS,
    COMPUTE_DAILY_METRICS,
    REFRESH_MV_CONTACTS,
    REFRESH_MV_JOURNEY,
    REFRESH_MV_LANDING,
)

_conn: Any = None


def _get_connection() -> Any:
    """Lazy connection a Neon."""
    global _conn  # noqa: PLW0603
    if _conn is None or _conn.closed:
        import psycopg  # noqa: PLC0415
        from common.ssm_client import get_secret  # noqa: PLC0415

        path = os.environ.get('SSM_NEON_URL_PATH', '/portfolio/neon-url')
        _conn = psycopg.connect(get_secret(path), autocommit=True)
    return _conn


@logger.inject_lambda_context(log_event=False)
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Entry point del aggregator nightly."""
    # Target: yesterday (UTC)
    yesterday = (datetime.now(UTC) - timedelta(days=1)).date()
    logger.info('aggregator starting', extra={'target_date': str(yesterday)})

    conn = _get_connection()
    results: dict[str, Any] = {'target_date': str(yesterday)}

    # Step 1: compute daily_metrics
    with conn.cursor() as cur:
        cur.execute(COMPUTE_DAILY_METRICS, {'target_date': yesterday})
    results['daily_metrics'] = 'ok'
    metrics.add_metric(name='AggregatorDailyMetrics', unit=MetricUnit.Count, value=1)

    # Step 2: refresh MVs (CONCURRENTLY, individually para que un fail no
    # rompa los otros)
    for mv_query, mv_name in [
        (REFRESH_MV_CONTACTS, 'mv_contacts_by_month_niche'),
        (REFRESH_MV_LANDING, 'mv_top_landing_pages'),
        (REFRESH_MV_JOURNEY, 'mv_session_journey'),
    ]:
        try:
            with conn.cursor() as cur:
                cur.execute(mv_query)
            results[mv_name] = 'refreshed'
        except Exception:  # noqa: BLE001
            logger.exception(
                'failed to refresh materialized view',
                extra={'mv_name': mv_name},
            )
            results[mv_name] = 'failed'

    # Step 3: cleanup processed_stream_events > 30d
    with conn.cursor() as cur:
        cur.execute(CLEANUP_OLD_EVENTS)
        results['cleanup_rows'] = cur.rowcount
    metrics.add_metric(
        name='AggregatorEventsCleaned',
        unit=MetricUnit.Count,
        value=cur.rowcount or 0,
    )

    logger.info('aggregator completed', extra=results)
    return results
