"""
PostgreSQL writer: idempotent INSERT en Neon.

Module-scope connection cached (no pool - reserved_concurrency=2 limita
conexiones concurrentes a Neon).
"""

from __future__ import annotations

import os
from typing import Any

# Singleton de conexion (lazy init para no romper imports en tests)
_conn: Any = None


def _get_connection() -> Any:
    """Lazy connection. Reusable entre invocaciones warm."""
    global _conn
    if _conn is None or _conn.closed:
        import psycopg

        from common.ssm_client import get_secret

        neon_url_path = os.environ.get(
            'SSM_NEON_URL_PATH', '/portfolio/neon-url'
        )
        db_url = get_secret(neon_url_path)
        _conn = psycopg.connect(db_url, autocommit=False)
    return _conn


def is_event_processed(event_id: str) -> bool:
    """Check si el event_id ya esta en processed_stream_events."""
    conn = _get_connection()
    with conn.cursor() as cur:
        cur.execute(
            'SELECT 1 FROM processed_stream_events WHERE event_id = %s',
            (event_id,),
        )
        return cur.fetchone() is not None


def mark_event_processed(
    event_id: str, *, event_type: str, table_name: str
) -> None:
    """Inserta el event_id en processed_stream_events (idempotente)."""
    conn = _get_connection()
    with conn.cursor() as cur:
        cur.execute(
            'INSERT INTO processed_stream_events (event_id, event_type, table_name) '
            'VALUES (%s, %s, %s) ON CONFLICT (event_id) DO NOTHING',
            (event_id, event_type, table_name),
        )


def upsert_contact(payload: dict[str, Any]) -> None:
    """UPSERT en Neon.contacts."""
    conn = _get_connection()
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO contacts (
                id, stream_event_id, created_at, name, email, message,
                company, role, service_type, budget, timeline, niche,
                ip, country, user_agent
            ) VALUES (
                %(id)s, %(stream_event_id)s, %(created_at)s, %(name)s,
                %(email)s, %(message)s, %(company)s, %(role)s,
                %(service_type)s, %(budget)s, %(timeline)s, %(niche)s,
                %(ip)s::inet, %(country)s, %(user_agent)s
            )
            ON CONFLICT (id) DO NOTHING
            """,
            payload,
        )


def upsert_tracking(payload: dict[str, Any]) -> None:
    """UPSERT en Neon.tracking_events."""
    conn = _get_connection()
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO tracking_events (
                session_id, page_id, stream_event_id, created_at, expires_at,
                page_url, page_title, page_path, referrer,
                utm_source, utm_medium, utm_campaign, utm_content, utm_term,
                viewport_width, viewport_height, niche,
                event_id, event_type_id, ip, country,
                user_agent, browser, browser_version, os, device_type
            ) VALUES (
                %(session_id)s, %(page_id)s, %(stream_event_id)s,
                %(created_at)s, to_timestamp(%(expires_at)s),
                %(page_url)s, %(page_title)s, %(page_path)s, %(referrer)s,
                %(utm_source)s, %(utm_medium)s, %(utm_campaign)s,
                %(utm_content)s, %(utm_term)s,
                %(viewport_width)s, %(viewport_height)s, %(niche)s,
                %(event_id)s, %(event_type_id)s,
                %(ip)s::inet, %(country)s, %(user_agent)s,
                %(browser)s, %(browser_version)s, %(os)s, %(device_type)s
            )
            """,
            payload,
        )


def commit() -> None:
    """Commit pending transactions."""
    conn = _get_connection()
    conn.commit()


def rollback() -> None:
    """Rollback pending transactions."""
    conn = _get_connection()
    conn.rollback()
