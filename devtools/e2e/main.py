"""Entry point del comando `e2e`: orquesta los modulos E2E.

Resuelve los flags, aplica el gate de auth duro para los modulos que mutan
el entorno (api/admin), y corre cada modulo pedido (api -> admin -> app) via
pytest. El modulo `api` corre con httpx puro (sin browser); `admin`/`app`
corren dentro del container Docker `e2e` (o local con `--headed`).

Exit codes: 0 (todos PASS), 1 (algun modulo FALL), 2 (error de setup/auth).
"""

from __future__ import annotations

from typing import Any

from e2e.flags import VALID_MODULES
from e2e.runner import check_auth_gate
from e2e.runner import run_module


def _resolve_modules(module: str | None) -> list[str]:
    """Modulos a correr: el pedido, o los 3 en orden (api -> admin -> app)."""
    if module is None:
        return list(VALID_MODULES)
    return [module]


def main(flags: dict[str, Any]) -> int:
    """Corre el harness E2E segun los flags."""
    env = flags['env']
    samples = flags.get('samples', 5)
    keep_data = flags.get('keep_data', False)
    aws_profile = flags.get('aws_profile')
    lambda_filter = flags.get('lambda')
    headed = flags.get('headed', False)
    verbose = flags.get('verbose', False)
    quiet = flags.get('quiet', False)

    modules = _resolve_modules(flags.get('module'))

    print('=' * 80)
    print(
        f'e2e — tests E2E contra {env.upper()} (modulos: {", ".join(modules)})'
    )
    print('=' * 80)

    if not check_auth_gate(modules=modules, env=env, aws_profile=aws_profile):
        return 2

    exit_code = 0
    for module in modules:
        print(f'\n{"=" * 30} modulo: {module} {"=" * 30}')
        rc = run_module(
            module=module,
            env=env,
            samples=samples,
            keep_data=keep_data,
            aws_profile=aws_profile,
            lambda_filter=lambda_filter,
            headed=headed,
            verbose=verbose,
            quiet=quiet,
        )
        if rc == 2:
            print(f'[ERROR] modulo {module}: error de setup.')
            return 2
        if rc != 0:
            exit_code = 1

    print('\n' + '=' * 80)
    print('e2e: TODOS PASS' if exit_code == 0 else 'e2e: ALGUN MODULO FALLO')
    print('=' * 80)
    return exit_code
