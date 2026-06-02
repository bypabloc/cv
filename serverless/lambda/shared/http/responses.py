"""
HTTP response helpers para API Gateway REST proxy integration.

Convencion shape para API GW REST:
    {
        'statusCode': int,
        'headers': dict[str, str],
        'body': str (JSON serializado),
        'isBase64Encoded': bool (opcional, default False)
    }
"""

from __future__ import annotations

import json
from typing import Any

from shared.core.exceptions import ApplicationError
from shared.core.types import ErrorPayload, JsonResponse
from shared.http.cors import cors_headers

_DEFAULT_HEADERS = {
    'Content-Type': 'application/json; charset=utf-8',
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
}


def json_response(
    status_code: int,
    body: dict[str, Any] | list[Any],
    *,
    origin: str,
    extra_headers: dict[str, str] | None = None,
) -> JsonResponse:
    """
    Build una respuesta JSON 2XX con headers CORS + seguridad estandar.

    Args:
        status_code: HTTP code (200, 201, 204, etc.).
        body: dict/list a serializar como JSON.
        origin: origin a echo en Access-Control-Allow-Origin
                (usar `resolve_origin()` para resolverlo).
        extra_headers: headers adicionales (ej: Retry-After).

    Returns:
        JsonResponse shape para API GW REST proxy.

    Examples:
        >>> r = json_response(200, {'ok': True}, origin='https://the-full-stack.com')
        >>> r['statusCode']
        200
        >>> r['headers']['Access-Control-Allow-Origin']
        'https://the-full-stack.com'
        >>> r['body']
        '{"ok":true}'
    """
    headers = {**_DEFAULT_HEADERS, **cors_headers(origin)}
    if extra_headers:
        headers.update(extra_headers)

    return {
        'statusCode': status_code,
        'headers': headers,
        'body': json.dumps(body, separators=(',', ':'), ensure_ascii=False),
    }


def error_response(
    error: ApplicationError | Exception,
    *,
    origin: str,
    status_code: int | None = None,
    extra_headers: dict[str, str] | None = None,
) -> JsonResponse:
    """
    Build respuesta de error JSON. Mapea ApplicationError -> {error, code, extra}.

    Para excepciones genericas (no ApplicationError) usa status_code 500
    y NO expone el mensaje al cliente (ese va a logs, el cliente recibe
    un mensaje generico).

    Args:
        error: excepcion a mapear.
        origin: origin para CORS echo.
        status_code: override del status_code default de la excepcion.
        extra_headers: headers extra (ej: Retry-After para 429).

    Returns:
        JsonResponse con shape `{statusCode, headers, body: '{error, code, extra}'}`
    """
    if isinstance(error, ApplicationError):
        status = status_code or error.status_code
        payload: ErrorPayload = {
            'error': error.message or error.code,
            'code': error.code,
        }
        if error.extra:
            payload['extra'] = error.extra
    else:
        # Excepcion no-aplicacion: mensaje generico, NO leak detalles
        status = status_code or 500
        payload = {
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR',
        }

    # Si es rate-limit, agregar Retry-After header automaticamente
    headers_extra = dict(extra_headers or {})
    if isinstance(error, ApplicationError):
        retry_after = error.extra.get('retry_after_seconds')
        if retry_after is not None and 'Retry-After' not in headers_extra:
            headers_extra['Retry-After'] = str(retry_after)

    return json_response(
        status,
        dict(payload),
        origin=origin,
        extra_headers=headers_extra,
    )


def no_content_response(
    *,
    origin: str,
    extra_headers: dict[str, str] | None = None,
) -> JsonResponse:
    """Response 204 No Content para endpoints fire-and-forget (tracking pixel)."""
    headers = {**cors_headers(origin)}
    if extra_headers:
        headers.update(extra_headers)
    return {'statusCode': 204, 'headers': headers, 'body': ''}


def redirect_response(
    location: str,
    *,
    origin: str,
    extra_headers: dict[str, str] | None = None,
) -> JsonResponse:
    """
    Build una respuesta 302 que redirige al `location` (header Location).

    La usan los endpoints GET que devuelven un `redirect_url` (ej. el
    callback del magic-link de auth: el browser navega al link del email,
    el Lambda responde 302 Location -> el admin/callback). El body va vacio.

    Incluye los headers CORS por consistencia (inofensivos: una navegacion
    top-level del browser NO valida CORS), pero NO los `_DEFAULT_HEADERS`
    JSON (no hay body JSON). El `Location` puede llevar un fragment hash
    (`#access=...`) que el browser retiene local y NO reenvia al destino.

    Args:
        location: URL destino del redirect (header Location).
        origin: origin a echo en Access-Control-Allow-Origin.
        extra_headers: headers adicionales.

    Returns:
        JsonResponse shape `{statusCode: 302, headers: {...cors, Location},
        body: ''}` para API GW REST proxy.

    Examples:
        >>> r = redirect_response(
        ...     'https://admin.the-full-stack.com/callback#access=x',
        ...     origin='https://admin.the-full-stack.com',
        ... )
        >>> r['statusCode']
        302
        >>> r['headers']['Location']
        'https://admin.the-full-stack.com/callback#access=x'
        >>> r['body']
        ''
    """
    headers = {**cors_headers(origin), 'Location': location}
    if extra_headers:
        headers.update(extra_headers)
    return {'statusCode': 302, 'headers': headers, 'body': ''}
