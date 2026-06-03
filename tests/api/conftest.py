"""Fixtures de sesion del modulo api (Lambdas HTTP, httpx puro).

Replica el setup del orquestador `devtools/api_e2e/main.py`:

- UN `Environment` (SSM + Neon + bypass firmado) por sesion.
- UN `HttpClient` (httpx + timing) por sesion, contra `api_base(env)`.
- UN `Reporter` + `Runner` por sesion: son la FUENTE del resumen de
  tiempos (cold por Lambda + warm por caso), igual que en api_e2e. Cada
  `test_*.py` registra sus casos contra este Runner compartido.
- `bypass`: token de Turnstile firmado localmente (None si el env no lo
  soporta o falta la clave; en dev/stage el gate de auth ya lo exige).
- `run_id`, `created_emails`, `created_sessions`: estado del run.

Teardown de sesion: imprime el resumen de tiempos + el veredicto del
Reporter y limpia los datos sinteticos creados en Neon (salvo
`--keep-data`), igual que `api_e2e/main._cleanup`. HERMETICO: ningun
valor de secreto (bypass, Neon URL) a stdout.
"""

from __future__ import annotations

from collections.abc import Iterator
import secrets as _secrets

import pytest
from shared.config import api_base
from shared.config import turnstile_bypass_supported
from shared.environment import Environment
from shared.http import HttpClient
from shared.reporter import Reporter
from shared.runner import Runner


# Orden de ejecucion canonico del modulo (el de `api_e2e/main._run_flows`):
# los Lambdas read primero, luego auth (produce el access_token vivo),
# auth_mfa, users (lo consume) y admin AL FINAL. admin promueve la whitelist
# SSM + recicla el contenedor de `users`: corriendolo ultimo, ese Lambda ya
# esta caliente y el sondeo de readiness converge rapido (en api_e2e admin
# era la cola del flujo de users por la misma razon).
_FILE_ORDER = (
    'test_cv.py',
    'test_contact_form.py',
    'test_tracking_pixel.py',
    'test_auth.py',
    'test_auth_mfa.py',
    'test_users.py',
    'test_admin.py',
)


def pytest_collection_modifyitems(
    items: list[pytest.Item],
) -> None:
    """Reordena los tests del modulo api al orden canonico de `_FILE_ORDER`.

    Given los 7 tests del modulo api recolectados (alfabeticamente por
    defecto: admin primero),
    When pytest termina la coleccion,
    Then se reordenan al orden de dependencia real (auth antes que users;
    admin al final) para preservar la cadena de tokens y evitar la carrera
    de la whitelist SSM con un contenedor frio de `users`.
    """
    rank = {name: i for i, name in enumerate(_FILE_ORDER)}
    items.sort(key=lambda item: rank.get(item.path.name, len(rank)))


@pytest.fixture(scope='session')
def run_id() -> str:
    """Identificador corto y unico de la corrida (trazabilidad/cleanup)."""
    return _secrets.token_hex(2)


@pytest.fixture(scope='session')
def environment(
    env: str,
    aws_profile: str | None,
) -> Environment:
    """Acceso al entorno desplegado (SSM secrets + Neon seed/cleanup)."""
    return Environment(env, aws_profile=aws_profile)


@pytest.fixture(scope='session')
def bypass(env: str, environment: Environment) -> str | None:
    """Token de bypass de Turnstile firmado (None si el env no lo soporta).

    Mismo criterio que `api_e2e/main`: solo dev/stage evaluan el header
    `X-Turnstile-Bypass-Token`. El gate de auth de `e2e/runner` ya exige
    la clave privada para los modulos api/admin, asi que en dev/stage el
    valor es no-None.
    """
    if not turnstile_bypass_supported(env):
        return None
    return environment.bypass_token()


@pytest.fixture(scope='session')
def created_emails() -> list[str]:
    """Acumulador de emails sinteticos creados (cleanup en teardown)."""
    return []


@pytest.fixture(scope='session')
def created_sessions() -> list[str]:
    """Acumulador de session_ids sinteticos creados (cleanup en teardown)."""
    return []


@pytest.fixture(scope='session')
def reporter(
    env: str,
    environment: Environment,
    bypass: str | None,
    keep_data: bool,
    created_emails: list[str],
    created_sessions: list[str],
) -> Iterator[Reporter]:
    """Reporter compartido por toda la sesion del modulo api.

    Setup: purga blacklists de IPs TEST-NET de corridas previas (mismo
    best-effort que `api_e2e/main`). Teardown: imprime el resumen de
    tiempos + el veredicto y limpia los datos sinteticos (salvo
    `--keep-data`).
    """
    print('=' * 80)
    print(
        f'api e2e — tests reales contra {env.upper()} ({api_base(env)})'
    )
    print('=' * 80)
    _print_bypass_note(env, bypass)

    # Purga blacklists de IPs TEST-NET de corridas previas (auto-blacklist
    # 24h): evita 403 intermitente cuando el round-robin reusa una IP ya
    # bloqueada. Best-effort.
    try:
        purged = environment.cleanup_rate_limit_blacklist()
        if purged:
            print(f'[INFO] blacklists TEST-NET previas purgadas: {purged}')
    except Exception as exc:  # noqa: BLE001 -- best-effort
        print(f'[WARN] purga inicial de blacklist fallo: {exc}')

    rep = Reporter()
    try:
        yield rep
    finally:
        rep.print_timing_summary()
        rep.print_final()
        if keep_data:
            print('\n[INFO] --keep-data: datos sinteticos NO eliminados.')
        else:
            _cleanup(environment, created_emails, created_sessions)


@pytest.fixture(scope='session')
def runner(reporter: Reporter, samples: int) -> Runner:
    """Runner compartido (N samples por caso) sobre el Reporter de sesion."""
    return Runner(reporter, samples=samples)


@pytest.fixture(scope='session')
def http(env: str) -> Iterator[HttpClient]:
    """Cliente httpx (con timing) contra el API Gateway del entorno."""
    client = HttpClient(base_url=api_base(env))
    try:
        yield client
    finally:
        client.close()


@pytest.fixture(scope='session')
def auth_token_box() -> dict[str, str | None]:
    """Caja mutable para la cadena de tokens auth -> users.

    `test_auth` deja aqui el access_token VIVO (access2 del flujo de
    exito); `test_users` lo lee. Si auth no corrio (ej. `--lambda=users`),
    queda None y el flujo de users genera su propio token (igual que
    `api_e2e/main._run_flows` corre auth cuando se pide users).
    """
    return {'access_token': None}


def _print_bypass_note(env_name: str, bypass: str | None) -> None:
    """Avisa si el bypass de Turnstile no esta disponible para el env."""
    if bypass is None and turnstile_bypass_supported(env_name):
        print(
            '[WARN] bypass de Turnstile no disponible: los flujos de '
            'exito de contact/auth se omiten (solo errores).'
        )
    elif not turnstile_bypass_supported(env_name):
        print(
            f'[INFO] {env_name} no soporta bypass de Turnstile: '
            'flujos con Turnstile omitidos (solo errores).'
        )


def _cleanup(
    environment: Environment,
    emails: list[str],
    sessions: list[str],
) -> None:
    """Borra los datos sinteticos creados por la corrida (best-effort)."""
    print('\n--- cleanup (datos sinteticos) ---')
    try:
        users = environment.cleanup_users(emails)
        contacts = environment.cleanup_contacts(emails)
        tracking = environment.cleanup_tracking(sessions)
        blacklist = environment.cleanup_rate_limit_blacklist()
        print(
            f'  borrados: users={users} contacts={contacts} '
            f'tracking={tracking} ip_blacklist={blacklist}'
        )
    except Exception as exc:  # noqa: BLE001 -- best-effort
        print(f'  [WARN] cleanup parcial: {type(exc).__name__}: {exc}')
