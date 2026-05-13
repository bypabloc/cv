"""Clientes asincronos para PyPI y npm registry.

Cada funcion recibe un ``httpx.AsyncClient`` ya creado y devuelve la lista de
versiones publicadas. Errores HTTP (404, timeout) retornan lista vacia para
que el caller pueda continuar con otros paquetes sin abortar el batch.
"""

import httpx


PYPI_BASE = 'https://pypi.org/pypi'
NPM_BASE = 'https://registry.npmjs.org'

DEFAULT_TIMEOUT = 30.0


async def fetch_pypi_versions(
    client: httpx.AsyncClient, name: str
) -> list[str]:
    """Consulta la JSON API de PyPI y devuelve versiones publicadas.

    Args:
        client: instancia httpx.AsyncClient (mockeable en tests).
        name: nombre del paquete (sin extras).

    Returns:
        Lista de versiones que tienen al menos un archivo publicado y no
        fueron yanked. Lista vacia si 404 o respuesta sin ``releases``.
    """
    url = f'{PYPI_BASE}/{name}/json'
    response = await client.get(url, timeout=DEFAULT_TIMEOUT)

    if response.status_code != 200:
        return []

    data = response.json()
    releases = data.get('releases') or {}

    versions: list[str] = []
    for ver, files in releases.items():
        if not files:
            continue
        # Si CUALQUIER archivo de la version esta yanked, descartamos la
        # version completa (PyPI yank es global a la release).
        if any(f.get('yanked', False) for f in files):
            continue
        versions.append(ver)

    return versions


async def fetch_npm_versions(client: httpx.AsyncClient, name: str) -> list[str]:
    """Consulta el registry de npm y devuelve versiones publicadas.

    Args:
        client: instancia httpx.AsyncClient (mockeable en tests).
        name: nombre del paquete (puede ser ``@scope/pkg``).

    Returns:
        Lista de versiones del paquete (todas, sin filtrar pre-releases —
        ese filtrado vive en versions.pick_latest_stable).
    """
    url = f'{NPM_BASE}/{name}'
    response = await client.get(url, timeout=DEFAULT_TIMEOUT)

    if response.status_code != 200:
        return []

    data = response.json()
    versions = data.get('versions') or {}

    return list(versions.keys())
