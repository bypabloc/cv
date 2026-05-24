"""github_sync main: sincroniza docker/env/client/.{env} a GitHub
Environment Variables (dev/stage/prod).

Hermetico: ningun valor de env var aparece en stdout, stderr, ni en
mensajes de error. Solo nombres de KEY + acciones (SKIP/PUSH/CREATE/MISSING).

Flujo:
1. Validar flags (--env requerido y valido).
2. Verificar `gh auth status`.
3. Verificar que docker/env/client/.{env} existe.
4. Parsear el .env -> dict {key: value}.
5. Filtrar por catalogo (SYNCED_KEYS).
6. Para cada key del catalogo:
   - Resolver valor local. Si vacio -> MISSING.
   - Resolver valor remoto via gh api (None si no existe).
   - Comparar via hash. SKIP / PUSH / CREATE.
7. Imprimir resumen.

Exit codes:
  0 -> exito (puede incluir SKIPs y MISSINGs, no es error)
  1 -> error de usuario (auth, env file missing, etc.)
  2 -> error interno (gh fallo, etc.)
"""

from pathlib import Path

from github_sync.catalog import SYNCED_KEYS
from github_sync.gh_client import GhClientError
from github_sync.gh_client import check_auth
from github_sync.gh_client import ensure_environment
from github_sync.gh_client import get_variable
from github_sync.gh_client import hash_value
from github_sync.gh_client import set_variable
from github_sync.parser import EnvParseError
from github_sync.parser import filter_catalog
from github_sync.parser import parse_env_file
from shared.paths import PROJECT_ROOT


def main(flags: dict) -> int:  # noqa: C901
    """Entry point. flags ya validado por flags.py.

    C901 ignorado: este es un orquestador CLI con validaciones
    secuenciales de pre-flight. La logica por-key ya esta extraida
    a _sync_one(). Romper mas degradaria la legibilidad.
    """
    env = flags['env']
    dry_run = flags['dry_run']
    keys_filter = _parse_keys(flags['keys'])
    create_env = flags['create_env']

    print(f'[github_sync] env={env} dry_run={dry_run} create_env={create_env}')
    if keys_filter:
        print(f'[github_sync] keys filter: {sorted(keys_filter)}')

    # 1. gh auth
    try:
        check_auth()
    except GhClientError as e:
        print(f'[ERROR] {e}')
        return 1

    # 2. .env file
    env_path = PROJECT_ROOT / 'docker' / 'env' / 'client' / f'.{env}'
    if not env_path.is_file():
        print(f'[ERROR] No existe: {env_path}')
        return 1

    # 3. parse + filter
    try:
        parsed = parse_env_file(env_path)
    except EnvParseError as e:
        print(f'[ERROR] {e}')
        return 1
    catalog_subset = filter_catalog(parsed, SYNCED_KEYS)

    # Si --keys=A,B se paso, restringir mas
    if keys_filter:
        unknown = keys_filter - SYNCED_KEYS
        if unknown:
            print(
                f'[ERROR] --keys contiene keys fuera del catalogo: {sorted(unknown)}',
            )
            return 1
        catalog_subset = {
            k: v for k, v in catalog_subset.items() if k in keys_filter
        }

    # 4. ensure environment
    if create_env and not dry_run:
        try:
            ensure_environment(env)
        except GhClientError as e:
            print(f'[ERROR] {e}')
            return 2

    # 5. sync each key
    targets = sorted(keys_filter) if keys_filter else sorted(SYNCED_KEYS)
    counters = {'PUSH': 0, 'CREATE': 0, 'SKIP': 0, 'MISSING': 0}
    for name in targets:
        rc = _sync_one(
            env=env,
            name=name,
            local_value=catalog_subset.get(name, ''),
            env_path_name=env_path.name,
            dry_run=dry_run,
            counters=counters,
        )
        if rc != 0:
            return rc

    print()
    print(
        f'[RESUMEN] PUSH={counters["PUSH"]} CREATE={counters["CREATE"]} '
        f'SKIP={counters["SKIP"]} MISSING={counters["MISSING"]}',
    )
    return 0


def _sync_one(
    *,
    env: str,
    name: str,
    local_value: str,
    env_path_name: str,
    dry_run: bool,
    counters: dict[str, int],
) -> int:
    """Sincroniza UNA key. Actualiza counters. Retorna 0 ok, 2 si error."""
    if not local_value:
        print(f'[MISSING] {name}: ausente o vacio en {env_path_name}')
        counters['MISSING'] += 1
        return 0
    try:
        remote_value = get_variable(env, name)
    except GhClientError as e:
        print(f'[ERROR] leyendo {name}: {e}')
        return 2
    if remote_value is None:
        action = 'CREATE'
    elif hash_value(local_value) == hash_value(remote_value):
        action = 'SKIP'
    else:
        action = 'PUSH'
    if action == 'SKIP':
        print(f'[SKIP] {name}: valor remoto coincide')
        counters['SKIP'] += 1
        return 0
    if dry_run:
        print(f'[DRY-RUN {action}] {name}: ejecutaria gh variable set')
        counters[action] += 1
        return 0
    try:
        set_variable(env, name, local_value)
    except GhClientError as e:
        print(f'[ERROR] set {name}: {e}')
        return 2
    print(f'[{action}] {name}: ok')
    counters[action] += 1
    return 0


def _parse_keys(raw: str) -> set[str]:
    """Parse "A,B,C" -> {"A","B","C"}. Strings vacios se filtran."""
    if not raw:
        return set()
    return {k.strip() for k in raw.split(',') if k.strip()}
