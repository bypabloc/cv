"""Logica de corrida del comando `e2e`: gate de auth + runner por modulo.

`main.py` orquesta; este modulo concentra (a) el gate de auth duro (AC-6:
SSO + clave bypass disponibles para los modulos api/admin) y (b) la corrida
de cada modulo (pytest sobre `tests/<module>/`, en proceso para `api`, en el
container `e2e` para `admin`/`app`).

NUNCA imprime un valor de secreto: el gate solo reporta presencia/ausencia.
"""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


# Modulos que EXIGEN auth (SSO + clave bypass). `app` (no-auth) puede correr
# sin credenciales.
_AUTH_MODULES = ('api', 'admin')

# Raiz del repo: devtools/e2e/runner.py -> e2e -> devtools -> ROOT.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_VENV_PYTHON = _PROJECT_ROOT / 'devtools' / '.venv' / 'bin' / 'python'
_TESTS_DIR = _PROJECT_ROOT / 'tests'


def _tests_path_for(module: str) -> Path:
    """Carpeta de tests del modulo (`tests/api`, `tests/admin`, ...)."""
    return _TESTS_DIR / module


def _has_sso(aws_profile: str | None) -> bool:
    """True si hay credenciales AWS validas (sts get-caller-identity).

    Best-effort: cualquier error de boto3/credenciales -> False. NO imprime
    el ARN ni la cuenta.
    """
    try:
        import boto3
    except ImportError:
        return False
    try:
        session = boto3.Session(profile_name=aws_profile)
        session.client('sts').get_caller_identity()
    except Exception:  # noqa: BLE001 -- cualquier fallo = sin auth
        return False
    return True


def _has_bypass_key(env: str, aws_profile: str | None) -> bool:
    """True si hay clave privada Ed25519 local para firmar el bypass token.

    Usa `tests.shared.environment.Environment.bypass_token()` (None si falta
    la clave). NUNCA imprime el token. Importa el portador agregando `tests/`
    al sys.path.
    """
    tests_dir = str(_TESTS_DIR)
    if tests_dir not in sys.path:
        sys.path.insert(0, tests_dir)
    try:
        from shared.environment import Environment
    except ImportError:
        return False
    try:
        environment = Environment(env, aws_profile=aws_profile)
        return environment.bypass_token() is not None
    except Exception:  # noqa: BLE001 -- cualquier fallo = sin bypass
        return False


def check_auth_gate(
    *,
    modules: list[str],
    env: str,
    aws_profile: str | None,
) -> bool:
    """Gate de auth duro (AC-6) para los modulos que mutan el entorno.

    Si algun modulo pedido esta en `_AUTH_MODULES`, exige SSO valido Y clave
    bypass disponible. Imprime un error claro y devuelve False si falta algo.
    `app` solo NO dispara el gate.
    """
    if not any(m in _AUTH_MODULES for m in modules):
        return True

    if not _has_sso(aws_profile):
        profile_hint = aws_profile or '(perfil del shell)'
        print(
            '[ERROR] auth: sin credenciales AWS validas para '
            f'{profile_hint}. Los modulos api/admin mutan el entorno y '
            'leen SSM/Neon: necesitan SSO activo.\n'
            '  Corre: aws sso login --profile <perfil> '
            'y pasa --aws-profile=<perfil>.',
        )
        return False

    if not _has_bypass_key(env, aws_profile):
        print(
            '[ERROR] auth: clave privada de bypass Ed25519 no disponible '
            f'en docker/env/dev-cli/.{env}. Los modulos api/admin la '
            'necesitan para firmar el token de bypass de Turnstile.\n'
            '  Genera el par con: '
            'python devtools/run.py bypass_token keygen --envs=dev',
        )
        return False

    return True


def _base_pytest_args(
    *,
    module: str,
    env: str,
    samples: int,
    keep_data: bool,
    aws_profile: str | None,
    lambda_filter: str | None,
    verbose: bool,
    quiet: bool,
) -> list[str]:
    """Construye los argumentos de pytest comunes para un modulo."""
    args = [module, f'--env={env}', f'--samples={samples}']
    if aws_profile:
        args.append(f'--aws-profile={aws_profile}')
    if keep_data:
        args.append('--keep-data')
    if module == 'api' and lambda_filter:
        args.append(f'--lambda={lambda_filter}')
    if verbose:
        args.append('-v')
    elif quiet:
        args.append('-q')
    return args


def run_module(
    *,
    module: str,
    env: str,
    samples: int,
    keep_data: bool,
    aws_profile: str | None,
    lambda_filter: str | None,
    headed: bool,
    verbose: bool,
    quiet: bool,
) -> int:
    """Corre los tests de un modulo. Degrada limpio si la carpeta no existe.

    Returns:
        0   PASS (o carpeta aun no implementada -> no rompe).
        1   algun test FAIL.
        2   error de setup (no deberia ocurrir aqui; lo cubre el gate).
    """
    tests_path = _tests_path_for(module)
    if not tests_path.is_dir():
        print(
            f'[INFO] modulo {module}: tests/{module}/ aun no implementado '
            '(otra fase del plan). Se omite.',
        )
        return 0

    pytest_args = _base_pytest_args(
        module=module,
        env=env,
        samples=samples,
        keep_data=keep_data,
        aws_profile=aws_profile,
        lambda_filter=lambda_filter,
        verbose=verbose,
        quiet=quiet,
    )

    if module == 'api':
        return _run_api_local(pytest_args)
    return _run_browser_module(
        env=env,
        pytest_args=pytest_args,
        headed=headed,
        quiet=quiet,
    )


def _run_api_local(pytest_args: list[str]) -> int:
    """Corre pytest del modulo api en proceso (httpx puro, sin browser)."""
    python = str(_VENV_PYTHON) if _VENV_PYTHON.exists() else sys.executable
    cmd = [python, '-m', 'pytest', *pytest_args]
    result = subprocess.run(  # noqa: S603
        cmd,
        cwd=str(_TESTS_DIR),
        check=False,
    )
    return result.returncode


def _run_browser_module(
    *,
    env: str,
    pytest_args: list[str],
    headed: bool,
    quiet: bool,
) -> int:
    """Corre un modulo browser (admin/app).

    Por defecto corre en el HOST con el `devtools/.venv` (que ya trae
    playwright + los browsers instalados via `playwright install`): es el
    camino verificado y el que usa el pre-push. `--headed` solo controla que
    el browser sea visible (debug); headless es el default.

    El container `e2e` (E2E_USE_CONTAINER=1) queda como opcion de aislamiento
    para entornos sin browsers en el host; requiere que su `.venv` este
    sincronizado (uv sync dentro del container).
    """
    if os.environ.get('E2E_USE_CONTAINER') == '1':
        from e2e.container import ensure_e2e_container
        from e2e.container import run_pytest_in_container

        if not ensure_e2e_container(env):
            return 2
        return run_pytest_in_container(
            env=env,
            pytest_args=pytest_args,
            quiet=quiet,
        )

    python = str(_VENV_PYTHON) if _VENV_PYTHON.exists() else sys.executable
    spawn_env = {**os.environ}
    if headed:
        spawn_env['E2E_HEADED'] = '1'
    result = subprocess.run(  # noqa: S603
        [python, '-m', 'pytest', *pytest_args],
        cwd=str(_TESTS_DIR),
        check=False,
        env=spawn_env,
    )
    return result.returncode
