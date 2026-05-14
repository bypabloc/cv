"""Queries del dashboard contra Neon PostgreSQL."""

from __future__ import annotations

import os
from typing import Any

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


def get_summary(days: int = 30) -> dict[str, Any]:
    """
    Retorna stats agregadas de los ultimos N dias.

    Returns:
        Dict con totals + breakdown por niche/device/country.
    """
    conn = _get_connection()
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                COUNT(*) AS total_contacts,
                COUNT(*) FILTER (WHERE status = 'converted') AS converted_contacts,
                COUNT(*) FILTER (WHERE status = 'new') AS new_contacts
            FROM contacts
            WHERE created_at >= NOW() - (%s || ' days')::interval
            """,
            (str(days),),
        )
        contacts_row = cur.fetchone()

        cur.execute(
            """
            SELECT
                COUNT(*) AS total_events,
                COUNT(DISTINCT session_id) AS unique_sessions
            FROM tracking_events
            WHERE created_at >= NOW() - (%s || ' days')::interval
            """,
            (str(days),),
        )
        tracking_row = cur.fetchone()

    return {
        'period_days': days,
        'contacts': {
            'total': contacts_row[0] if contacts_row else 0,
            'converted': contacts_row[1] if contacts_row else 0,
            'new': contacts_row[2] if contacts_row else 0,
        },
        'tracking': {
            'total_events': tracking_row[0] if tracking_row else 0,
            'unique_sessions': tracking_row[1] if tracking_row else 0,
        },
    }


def get_recent_contacts(limit: int = 20) -> list[dict[str, Any]]:
    """Lista contacts recientes."""
    conn = _get_connection()
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, created_at, name, email, niche, service_type, status
            FROM contacts
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (limit,),
        )
        rows = cur.fetchall()
    return [
        {
            'id': str(r[0]),
            'created_at': r[1].isoformat() if r[1] else None,
            'name': r[2],
            'email': r[3],
            'niche': r[4],
            'service_type': r[5],
            'status': r[6],
        }
        for r in rows
    ]


def get_top_pages(days: int = 30, limit: int = 20) -> list[dict[str, Any]]:
    """Top landing pages de los ultimos N dias."""
    conn = _get_connection()
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                page_path,
                COUNT(*) AS visits,
                COUNT(DISTINCT session_id) AS unique_sessions
            FROM tracking_events
            WHERE created_at >= NOW() - (%s || ' days')::interval
                AND page_path IS NOT NULL
            GROUP BY page_path
            ORDER BY visits DESC
            LIMIT %s
            """,
            (str(days), limit),
        )
        rows = cur.fetchall()
    return [
        {'page_path': r[0], 'visits': r[1], 'unique_sessions': r[2]}
        for r in rows
    ]
