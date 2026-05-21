"""Enrichment del evento de tracking: parse UA + extract metadata."""

from __future__ import annotations

import re

from shared.cache import cached

# TTL del cache de UA parsing: 24h. Un mismo User-Agent string repetido en
# invocaciones warm no re-ejecuta el regex (SPEC-204).
_UA_CACHE_TTL_SECONDS = 24 * 60 * 60

# Simple UA parser - regex patterns (sin dependencia externa para evitar bloat)
_BROWSER_PATTERNS = (
    ('Chrome', re.compile(r'Chrome/(\d+)')),
    ('Firefox', re.compile(r'Firefox/(\d+)')),
    ('Safari', re.compile(r'Version/(\d+).*Safari')),
    ('Edge', re.compile(r'Edg/(\d+)')),
)

_OS_PATTERNS = (
    ('iOS', re.compile(r'iPhone|iPad|iPod')),
    ('Android', re.compile(r'Android')),
    ('Windows', re.compile(r'Windows NT (\d+\.\d+)')),
    ('macOS', re.compile(r'Mac OS X (\d+[._]\d+)')),
    ('Linux', re.compile(r'Linux')),
)


@cached(ttl=_UA_CACHE_TTL_SECONDS, namespace='ua', tags=['user-agent'])
def parse_user_agent(user_agent: str | None) -> dict[str, str]:
    """
    Parse User-Agent minimalista: browser + os + device type.

    El resultado se cachea 24h via DynamoDB (`@cached`): la cache key se
    deriva del string User-Agent, asi UA repetidos en invocaciones warm no
    re-ejecutan el regex y UA distintos no colisionan (SPEC-204).

    Returns:
        Dict con `browser`, `browser_version`, `os`, `device_type`.
    """
    if not user_agent:
        return {
            'browser': 'unknown',
            'browser_version': '',
            'os': 'unknown',
            'device_type': 'unknown',
        }

    browser, browser_version = 'unknown', ''
    for name, pattern in _BROWSER_PATTERNS:
        match = pattern.search(user_agent)
        if match:
            browser = name
            browser_version = match.group(1) if match.groups() else ''
            break

    os_name = 'unknown'
    for name, pattern in _OS_PATTERNS:
        if pattern.search(user_agent):
            os_name = name
            break

    # Device type heuristico
    if 'Mobile' in user_agent or 'iPhone' in user_agent:
        device_type = 'mobile'
    elif 'iPad' in user_agent or 'Tablet' in user_agent:
        device_type = 'tablet'
    elif 'bot' in user_agent.lower() or 'crawler' in user_agent.lower():
        device_type = 'bot'
    else:
        device_type = 'desktop'

    return {
        'browser': browser,
        'browser_version': browser_version,
        'os': os_name,
        'device_type': device_type,
    }
