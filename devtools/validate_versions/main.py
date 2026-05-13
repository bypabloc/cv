"""Entry point para validate_versions.

Read-only check del monorepo:
    1. Discover manifests (apps/* + packages/* + root + devtools + server)
    2. Para cada dep, fetch latest stable del registry (PyPI / npm)
    3. Aplica reglas de compatibilidad cross-package
    4. Reporta resultado (humano o JSON)

NO escribe. NO modifica nada. Para upgrade: usar `upgrade_deps`.
"""

from __future__ import annotations

import asyncio

from validate_versions.compat_rules import run_all
from validate_versions.reporter import print_human
from validate_versions.reporter import print_json
from validate_versions.resolver import resolve_all


async def _run(*, as_json: bool, strict: bool) -> int:
    packages = await resolve_all()
    issues = run_all(packages)

    if as_json:
        print_json(packages, issues)
    else:
        print_human(packages, issues)

    if strict:
        # En modo strict: fail si hay outdated o errores de compat.
        outdated_count = sum(1 for p in packages if p.status == 'outdated')
        error_count = sum(1 for i in issues if i.severity == 'error')
        if outdated_count > 0 or error_count > 0:
            return 1

    # Modo default: solo fail si hay errores de compat (outdated es info).
    error_count = sum(1 for i in issues if i.severity == 'error')
    return 1 if error_count > 0 else 0


def main(flags: dict) -> int:
    """Entry point invoked by ``devtools/run.py``."""
    return asyncio.run(
        _run(
            as_json=flags.get('json', False),
            strict=flags.get('strict', False),
        ),
    )
