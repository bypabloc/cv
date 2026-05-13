"""Service URL discovery: parse compose YAML + nginx config and print URLs.

Estos helpers introspectan los archivos compose y nginx del proyecto
portfolio para construir el bloque "Servicios disponibles" que se imprime
después de ``docker up`` y ``docker setup``.
"""

from __future__ import annotations

import re

from shared.console import DIM
from shared.console import GREEN
from shared.console import _c
from shared.console import _header
from shared.paths import DOCKER_DIR


_PORTFOLIO_APPS = ('hub', 'generic', 'fintech', 'architect', 'leader', 'vibe')


_PORT_RE = re.compile(
    r'["\']?'
    r'(?:\$\{[^:}]+:-(\d+)\}|(\d+))'
    r':(\d+)'
    r'["\']?'
)


def _build_container_port_map() -> dict[str, dict[int, str]]:
    """Build the container_port -> config_key mapping per service."""
    container_port_map: dict[str, dict[int, str]] = {
        'nginx': {80: 'proxy_port'},
    }
    for _app in _PORTFOLIO_APPS:
        container_port_map[_app] = {4321: f'{_app}_port'}
    return container_port_map


def _is_service_header(line: str, stripped: str) -> bool:
    """True si la linea es un service header (2-space indent + 'service:')."""
    return (
        line.startswith('  ')
        and not line.startswith('    ')
        and stripped.endswith(':')
        and not stripped.startswith('-')
        and not stripped.startswith('#')
    )


def _extract_port_mapping(stripped: str) -> tuple[int, int] | None:
    """Match 'host:container' o '${VAR:-default}:container' en una linea ports."""
    match = _PORT_RE.search(stripped)
    if not match:
        return None
    host_port = int(match.group(1) or match.group(2))
    container_port = int(match.group(3))
    return host_port, container_port


def parse_compose_ports(env: str) -> dict[str, int | None]:
    """Parse host ports from the docker-compose YAML for a given env.

    Handles both literal ports ("5535:5432") and variable-with-default
    syntax ("${PROXY_PORT:-9970}:80").

    Returns a dict con keys: proxy_port y <app>_port para cada app.
    """
    compose_file = DOCKER_DIR / 'docker-compose' / f'{env}.yml'
    if not compose_file.exists():
        return {}

    container_port_map = _build_container_port_map()
    result: dict[str, int | None] = {'proxy_port': None}
    for _app in _PORTFOLIO_APPS:
        result[f'{_app}_port'] = None

    current_service: str | None = None
    in_ports = False

    for line in compose_file.read_text().splitlines():
        stripped = line.strip()

        if _is_service_header(line, stripped):
            current_service = stripped.rstrip(':')
            in_ports = False
            continue

        if stripped == 'ports:' and current_service:
            in_ports = True
            continue

        if in_ports and stripped and not stripped.startswith('-'):
            in_ports = False

        if not in_ports or not current_service:
            continue

        ports = _extract_port_mapping(stripped)
        if ports is None:
            continue

        host_port, container_port = ports
        config_key = container_port_map.get(current_service, {}).get(
            container_port
        )
        if config_key:
            result[config_key] = host_port

    return result


def parse_nginx_subdomains(env: str) -> list[tuple[str, str]]:
    """Parse server_name entries from the nginx config for a given env.

    Portfolio mapping (local):
        localhost            -> apps/generic (the-full-stack.com en prod)
        hub.localhost        -> apps/hub     (selector multi-niche)
        fintech.localhost    -> apps/fintech
        architect.localhost  -> apps/architect
        leader.localhost     -> apps/leader
        vibe.localhost       -> apps/vibe
        services.localhost   -> indice de servicios estático
    """
    nginx_file = DOCKER_DIR / 'nginx' / f'{env}.conf'
    if not nginx_file.exists():
        return []

    label_map = {
        'localhost': 'Generic (the-full-stack.com)',
        'hub.localhost': 'Hub (selector niches)',
        'fintech.localhost': 'Fintech LATAM',
        'architect.localhost': 'Frontend Architect',
        'leader.localhost': 'Tech Lead / EM',
        'vibe.localhost': 'Vibe Coding',
        'services.localhost': 'Indice de servicios',
    }

    preferred_order = (
        'services.localhost',
        'localhost',
        'hub.localhost',
        'fintech.localhost',
        'architect.localhost',
        'leader.localhost',
        'vibe.localhost',
    )
    order_index = {name: i for i, name in enumerate(preferred_order)}

    results: list[tuple[str, str]] = []
    server_name_re = re.compile(r'server_name\s+([^;]+);')

    seen: set[str] = set()
    for match in server_name_re.finditer(nginx_file.read_text()):
        name = match.group(1).strip()
        if name == '_' or name in seen:
            continue
        seen.add(name)
        label = label_map.get(name, name)
        results.append((name, label))

    results.sort(key=lambda r: order_index.get(r[0], len(preferred_order)))
    return results


def print_service_urls(env: str) -> None:
    """Print URLs for all accessible services in the given environment."""
    compose_ports = parse_compose_ports(env)
    subdomains = parse_nginx_subdomains(env)
    proxy_port = compose_ports.get('proxy_port')

    print()
    _header(f'Servicios - {env}')
    print()

    if proxy_port and subdomains:
        max_label = max(len(label) for _, label in subdomains)
        for name, label in subdomains:
            padding = ' ' * (max_label - len(label) + 1)
            url = f'http://{name}:{proxy_port}'
            print(f'  {_c(GREEN, f"{label}:")}{padding}{url}')
    elif proxy_port:
        print(
            f'  {_c(GREEN, "Server:")}  http://localhost:{proxy_port}',
        )

    # Portfolio no tiene DB ni Redis ni mailpit.
    if not subdomains:
        print(f'  {_c(DIM, "(sin servicios en nginx config)")}')

    print()
