"""
Lambda handler: GET /dashboard/{action} con basic auth.

Actions soportadas (path param):
- summary: stats agregadas (default 30d)
- contacts: lista de contacts recientes
- pages: top landing pages
"""

from __future__ import annotations

import json
from typing import Any

from common.cors import resolve_origin
from common.exceptions import ApplicationError
from common.ip_extractor import extract_ip
from common.logger import logger
from common.metrics import metrics
from common.rate_limit import check_or_raise
from common.responses import error_response, json_response
from common.tracer import tracer
from dashboard_api.auth import unauthorized_response, verify_basic_auth
from dashboard_api.queries import (
    get_recent_contacts,
    get_summary,
    get_top_pages,
)


@logger.inject_lambda_context(log_event=False, correlation_id_path='requestContext.requestId')
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Entry point Lambda dashboard_api."""
    headers = event.get('headers') or {}
    origin = resolve_origin(headers)
    ip = extract_ip(event)
    path_params = event.get('pathParameters') or {}
    action = (path_params.get('action') or 'summary').lower()
    query_params = event.get('queryStringParameters') or {}

    try:
        # Rate-limit (anti-bruteforce: 5/min)
        check_or_raise(
            ip=ip,
            endpoint='/dashboard',
            country=None,
            turnstile_validated=False,
        )

        # Basic auth verify (puede levantar UnauthorizedError)
        try:
            verify_basic_auth(headers)
        except ApplicationError:
            return unauthorized_response(origin)

        # Routing
        if action == 'summary':
            days = int(query_params.get('days', '30'))
            data = get_summary(days=min(days, 365))
        elif action == 'contacts':
            limit = int(query_params.get('limit', '20'))
            data = {'items': get_recent_contacts(limit=min(limit, 100))}
        elif action == 'pages':
            days = int(query_params.get('days', '30'))
            limit = int(query_params.get('limit', '20'))
            data = {
                'items': get_top_pages(days=min(days, 365), limit=min(limit, 100)),
            }
        else:
            return json_response(
                404, {'error': 'unknown action', 'action': action},
                origin=origin,
            )

        return json_response(200, data, origin=origin)

    except ApplicationError as e:
        logger.warning('dashboard rejected', extra={'code': e.code})
        return error_response(e, origin=origin)

    except Exception:  # noqa: BLE001
        logger.exception('unhandled error in dashboard_api')
        return error_response(Exception('internal'), origin=origin)
