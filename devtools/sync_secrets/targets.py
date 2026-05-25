"""Targets de sincronizacion: 1 funcion por categoria.

Cada target retorna `dict[str, int]` con contadores por accion.
Hermetico: ningun valor de secreto en stdout.
"""

from pathlib import Path

from serverless.secrets_catalog import Catalog as ServerCatalog
from serverless.secrets_sync import SyncAction
from serverless.secrets_sync import sync_secrets_to_ssm
from sync_secrets.catalog import CLIENT_SYNCED_KEYS
from sync_secrets.catalog import DEVCLI_EXPECTED_KEYS
from sync_secrets.catalog import DEVCLI_OPTIONAL_KEYS
from sync_secrets.gh_client import GhClientError
from sync_secrets.gh_client import check_auth as gh_check_auth
from sync_secrets.gh_client import ensure_environment
from sync_secrets.gh_client import get_variable
from sync_secrets.gh_client import hash_value
from sync_secrets.gh_client import set_variable
from sync_secrets.parser import EnvParseError
from sync_secrets.parser import filter_catalog
from sync_secrets.parser import parse_env_file


def _zero_counters() -> dict[str, int]:
    return {
        'PUSH': 0,
        'CREATE': 0,
        'SKIP': 0,
        'MISSING': 0,
        'LOCAL-ONLY': 0,
        'ERROR': 0,
    }


def sync_client(
    *,
    env: str,
    env_file: Path,
    dry_run: bool,
    keys_filter: set[str] | None,
    create_env: bool,
) -> dict[str, int]:
    """Sincroniza client secrets -> GitHub Environment Variables."""
    counters = _zero_counters()
    print(f'\n[client] -> GitHub Environment Variables (env={env})')

    if not env_file.is_file():
        print(f'[ERROR] No existe: {env_file}')
        counters['ERROR'] += 1
        return counters

    try:
        gh_check_auth()
    except GhClientError as e:
        print(f'[ERROR] {e}')
        counters['ERROR'] += 1
        return counters

    try:
        parsed = parse_env_file(env_file)
    except EnvParseError as e:
        print(f'[ERROR] {e}')
        counters['ERROR'] += 1
        return counters

    subset = filter_catalog(parsed, CLIENT_SYNCED_KEYS)
    if keys_filter:
        unknown = keys_filter - CLIENT_SYNCED_KEYS
        if unknown:
            print(
                f'[ERROR] --keys con keys fuera del catalogo client: {sorted(unknown)}'
            )
            counters['ERROR'] += 1
            return counters
        subset = {k: v for k, v in subset.items() if k in keys_filter}

    if create_env and not dry_run:
        try:
            ensure_environment(env)
        except GhClientError as e:
            print(f'[ERROR] {e}')
            counters['ERROR'] += 1
            return counters

    targets = sorted(keys_filter) if keys_filter else sorted(CLIENT_SYNCED_KEYS)
    for name in targets:
        rc = _client_sync_one(
            env=env,
            name=name,
            local_value=subset.get(name, ''),
            env_path_name=env_file.name,
            dry_run=dry_run,
            counters=counters,
        )
        if rc != 0:
            break
    return counters


def _client_sync_one(
    *,
    env: str,
    name: str,
    local_value: str,
    env_path_name: str,
    dry_run: bool,
    counters: dict[str, int],
) -> int:
    if not local_value:
        print(f'[MISSING] {name}: ausente o vacio en {env_path_name}')
        counters['MISSING'] += 1
        return 0
    try:
        remote = get_variable(env, name)
    except GhClientError as e:
        print(f'[ERROR] leyendo {name}: {e}')
        counters['ERROR'] += 1
        return 1
    if remote is None:
        action = 'CREATE'
    elif hash_value(local_value) == hash_value(remote):
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
        counters['ERROR'] += 1
        return 1
    print(f'[{action}] {name}: ok')
    counters[action] += 1
    return 0


def sync_server(
    *,
    stage: str,
    env_file: Path,
    catalog_dir: Path,
    aws_profile: str | None,
    dry_run: bool,
    keys_filter: set[str] | None,
) -> dict[str, int]:
    """Sincroniza server secrets -> AWS SSM Parameter Store.

    Reusa `serverless.secrets_sync.sync_secrets_to_ssm` (catalogo YAML).
    """
    counters = _zero_counters()
    print(f'\n[server] -> AWS SSM Parameter Store (stage={stage})')

    if stage == 'local':
        print('[SKIP] stage=local no se sincroniza a SSM (offline-dev)')
        counters['SKIP'] += 1
        return counters

    try:
        catalog = ServerCatalog.load(catalog_dir)
    except Exception as e:
        print(f'[ERROR] cargando catalogo de {catalog_dir}: {e}')
        counters['ERROR'] += 1
        return counters

    try:
        results = sync_secrets_to_ssm(
            stage=stage,
            env_file=env_file,
            catalog=catalog,
            profile=aws_profile,
            only=tuple(keys_filter) if keys_filter else None,
            dry_run=dry_run,
        )
    except Exception as e:
        # SyncError o similar. NUNCA contiene valores (hermeticidad
        # garantizada por sync_secrets_to_ssm).
        print(f'[ERROR] sync server: {e}')
        counters['ERROR'] += 1
        return counters

    for r in results:
        prefix = 'DRY-RUN ' if dry_run and r.action == SyncAction.PUSH else ''
        action = r.action.value
        # Mapear acciones del server a contadores comunes (server no tiene CREATE)
        counter_key = action if action in counters else 'SKIP'
        print(f'[{prefix}{action}] {r.name}: {r.path}')
        counters[counter_key] = counters.get(counter_key, 0) + 1
    return counters


def sync_devcli(
    *,
    env: str,
    env_file: Path,
) -> dict[str, int]:
    """dev-cli: NO sincroniza nada remoto. Solo valida que las keys
    obligatorias esten presentes localmente.
    """
    counters = _zero_counters()
    print(f'\n[dev-cli] -> LOCAL-ONLY (env={env})')

    if not env_file.is_file():
        print(f'[ERROR] No existe: {env_file}')
        counters['ERROR'] += 1
        return counters

    try:
        parsed = parse_env_file(env_file)
    except EnvParseError as e:
        print(f'[ERROR] {e}')
        counters['ERROR'] += 1
        return counters

    for name in sorted(DEVCLI_EXPECTED_KEYS):
        value = parsed.get(name, '')
        if not value:
            print(
                f'[MISSING] {name}: ausente o vacio en {env_file.name} (requerido)'
            )
            counters['MISSING'] += 1
            continue
        print(f'[LOCAL-ONLY] {name}: presente (no se sincroniza remoto)')
        counters['LOCAL-ONLY'] += 1

    # Opcionales: solo reportar si estan
    for name in sorted(DEVCLI_OPTIONAL_KEYS):
        if parsed.get(name):
            print(f'[LOCAL-ONLY] {name}: presente (opcional, no se sincroniza)')
            counters['LOCAL-ONLY'] += 1

    return counters
