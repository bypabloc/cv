"""
Extraccion de IP del cliente desde un Lambda event (API GW REST proxy).

Orden de prioridad (CF upstream esta SIEMPRE delante del API GW):
1. `CF-Connecting-IP` header (Cloudflare official, IP real del cliente)
2. `True-Client-IP` header (Cloudflare Enterprise variant)
3. `X-Forwarded-For` first hop (estandar pre-Cloudflare, fallback)
4. `requestContext.identity.sourceIp` (IP del edge AWS, ya no es del cliente
    cuando hay CF upstream; fallback final)

Reglas anti-spoofing:
- En produccion CF reescribe (no concatena) estos headers, asi que confiar
  en ellos es safe cuando el API GW solo recibe trafico de CF.
- Si el API GW se expone directamente al mundo (sin CF upstream), un atacante
  puede forjar CF-Connecting-IP. Mitigacion: WAF que rechaza requests sin
  el secret header de CF.

Header lookup es case-insensitive (API GW REST proxy preserva el case del
cliente pero nosotros normalizamos a lower antes de buscar).
"""

from __future__ import annotations

from typing import Any


def _get_header(headers: dict[str, str] | None, name: str) -> str | None:
    """Lookup case-insensitive en dict de headers."""
    if not headers:
        return None
    target = name.lower()
    for key, value in headers.items():
        if key.lower() == target:
            return value
    return None


def _first_hop(xff: str) -> str:
    """X-Forwarded-For first hop (IP mas a la izquierda, el cliente real)."""
    return xff.split(',')[0].strip()


def extract_ip(event: dict[str, Any]) -> str:
    """
    Resuelve la IP del cliente con prioridad CF > XFF > requestContext.

    Args:
        event: Lambda event de API GW REST proxy.

    Returns:
        IP string o cadena vacia si no se puede determinar.

    Examples:
        >>> extract_ip({'headers': {'CF-Connecting-IP': '1.2.3.4'}})
        '1.2.3.4'
        >>> extract_ip({'headers': {'X-Forwarded-For': '5.6.7.8, 9.10.11.12'}})
        '5.6.7.8'
        >>> extract_ip({'requestContext': {'identity': {'sourceIp': '13.14.15.16'}}})
        '13.14.15.16'
        >>> extract_ip({})
        ''
    """
    headers = event.get('headers') or {}

    # 1. CF-Connecting-IP (priority highest, CF official)
    cf_ip = _get_header(headers, 'CF-Connecting-IP')
    if cf_ip:
        return cf_ip.strip()

    # 2. True-Client-IP (CF Enterprise variant)
    true_client = _get_header(headers, 'True-Client-IP')
    if true_client:
        return true_client.strip()

    # 3. X-Forwarded-For first hop
    xff = _get_header(headers, 'X-Forwarded-For')
    if xff:
        return _first_hop(xff)

    # 4. requestContext.identity.sourceIp (fallback final)
    rc = event.get('requestContext') or {}
    identity = rc.get('identity') or {}
    return (identity.get('sourceIp') or '').strip()


def extract_country(event: dict[str, Any]) -> str | None:
    """
    Resuelve el country code (ISO 3166-1 alpha-2) desde headers Edge.

    Prioridad:
    1. `CloudFront-Viewer-Country` (AWS Edge-Optimized API GW custom domain
       lo inyecta automaticamente con la geoloc de CloudFront).
    2. `CF-IPCountry` (header de Cloudflare; fallback para entornos que
       todavia pasen por CF, o para tests).

    Both son ISO 3166-1 alpha-2 (2 chars uppercase).

    Returns:
        Country code 2 chars upper, o None si no esta presente.
    """
    headers = event.get('headers')
    # 1. CloudFront-Viewer-Country (AWS Edge-Optimized)
    cf_viewer = _get_header(headers, 'CloudFront-Viewer-Country')
    if cf_viewer and len(cf_viewer) == 2:
        return cf_viewer.upper()
    # 2. CF-IPCountry (Cloudflare)
    cf_country = _get_header(headers, 'CF-IPCountry')
    if cf_country and len(cf_country) == 2:
        return cf_country.upper()
    return None


def extract_cloudfront_meta(event: dict[str, Any]) -> dict[str, str]:
    """
    Captura TODOS los headers cloudfront-* del request en un dict.

    Edge-Optimized API Gateway expone ~22 headers `CloudFront-*` con
    geo/device/network/tls metadata: viewer-country / country-region /
    city / postal-code / latitude / longitude / metro-code / time-zone /
    address / asn / ja3-fingerprint / tls / http-version + device flags
    (is-desktop/mobile/tablet/smarttv/ios/android-viewer) +
    forwarded-proto.

    Las keys del dict resultante son lowercase canonicas
    (`cloudfront-viewer-city`, `cloudfront-is-mobile-viewer`, etc.)
    para queries JSONB consistentes en Neon.

    Returns:
        Dict con todos los headers cloudfront-* (vacio si no hay).
    """
    headers = event.get('headers') or {}
    result: dict[str, str] = {}
    for key, value in headers.items():
        if not isinstance(key, str):
            continue
        lower = key.lower()
        if lower.startswith('cloudfront-') and value is not None:
            result[lower] = str(value)
    return result
