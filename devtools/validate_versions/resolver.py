"""Resolver: discover manifests + parse + fetch latest del registry.

Glue thin entre ``shared.manifest_discovery``, los parsers de
``upgrade_deps`` y el registry async. Devuelve una lista plana de
``ResolvedPackage`` con current + latest + status, lista para que
``compat_rules`` aplique sus reglas cross-package y el reporter imprima.

NO escribe nada. NO modifica manifests. Read-only por diseno.
"""

from __future__ import annotations

import asyncio
from typing import NamedTuple

import httpx

from shared.manifest_discovery import Manifest
from shared.manifest_discovery import discover_npm_manifests
from shared.manifest_discovery import discover_pypi_manifests
from upgrade_deps.parsers import parse_package_json
from upgrade_deps.parsers import parse_pyproject_toml
from upgrade_deps.registry import fetch_npm_versions
from upgrade_deps.registry import fetch_pypi_versions
from upgrade_deps.versions import is_newer
from upgrade_deps.versions import pick_latest_stable


_CONCURRENCY = 10


class ResolvedPackage(NamedTuple):
    """Un paquete resuelto contra el registry.

    Attributes:
        kind: ``'npm'`` o ``'pypi'``.
        workspace: id legible del manifest origen (``'app:fintech'``,
            ``'pkg:content'``, ``'devtools'``, ``'root'``).
        relpath: ruta relativa del manifest origen.
        name: nombre del paquete.
        section: seccion del manifest (``'dependencies'``,
            ``'devDependencies'``, ``'pnpm.overrides'``, etc.).
        current: version pinned localmente.
        latest: ultima version estable en el registry. ``None`` si el
            registry no respondio o no hay estables.
        status: ``'ok'`` (current == latest), ``'outdated'`` (latest > current),
            ``'unknown'`` (no se pudo consultar), ``'ahead'`` (current > latest,
            raro pero posible con canary local).
    """

    kind: str
    workspace: str
    relpath: str
    name: str
    section: str
    current: str
    latest: str | None
    status: str


def _classify(current: str, latest: str | None) -> str:
    if latest is None:
        return 'unknown'
    if current == latest:
        return 'ok'
    if is_newer(current=current, candidate=latest):
        return 'outdated'
    return 'ahead'


async def _resolve_npm(
    client: httpx.AsyncClient, manifest: Manifest
) -> list[ResolvedPackage]:
    """Resuelve TODOS los packages de un manifest npm."""
    parsed = parse_package_json(manifest.path)
    if not parsed:
        return []

    sem = asyncio.Semaphore(_CONCURRENCY)

    async def resolve_one(pkg: dict) -> ResolvedPackage:
        async with sem:
            try:
                versions = await fetch_npm_versions(client, pkg['name'])
                latest = pick_latest_stable(versions)
            except Exception:  # noqa: BLE001
                latest = None
        return ResolvedPackage(
            kind='npm',
            workspace=manifest.workspace,
            relpath=manifest.relpath,
            name=pkg['name'],
            section=pkg['section'],
            current=pkg['version'],
            latest=latest,
            status=_classify(pkg['version'], latest),
        )

    return list(await asyncio.gather(*(resolve_one(p) for p in parsed)))


async def _resolve_pypi(
    client: httpx.AsyncClient, manifest: Manifest
) -> list[ResolvedPackage]:
    """Resuelve TODOS los packages de un manifest pypi."""
    parsed = parse_pyproject_toml(manifest.path)
    if not parsed:
        return []

    sem = asyncio.Semaphore(_CONCURRENCY)

    async def resolve_one(pkg: dict) -> ResolvedPackage:
        async with sem:
            try:
                versions = await fetch_pypi_versions(client, pkg['name'])
                latest = pick_latest_stable(versions)
            except Exception:  # noqa: BLE001
                latest = None
        return ResolvedPackage(
            kind='pypi',
            workspace=manifest.workspace,
            relpath=manifest.relpath,
            name=pkg['name'],
            section=pkg['section'],
            current=pkg['version'],
            latest=latest,
            status=_classify(pkg['version'], latest),
        )

    return list(await asyncio.gather(*(resolve_one(p) for p in parsed)))


async def resolve_all() -> list[ResolvedPackage]:
    """Discover + parse + fetch latest para TODOS los manifests del monorepo."""
    out: list[ResolvedPackage] = []
    async with httpx.AsyncClient() as client:
        for manifest in discover_npm_manifests():
            out.extend(await _resolve_npm(client, manifest))
        for manifest in discover_pypi_manifests():
            out.extend(await _resolve_pypi(client, manifest))
    return out
