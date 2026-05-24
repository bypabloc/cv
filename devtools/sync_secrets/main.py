"""sync_secrets main: orquestador unificado.

Por categoria, llama al target correspondiente:
  client   -> sync_client    -> GitHub Environment Variables
  server   -> sync_server    -> AWS SSM Parameter Store (via serverless.secrets_sync)
  dev-cli  -> sync_devcli    -> LOCAL-ONLY (valida presencia, NO sincroniza)

Exit codes:
  0 -> exito (puede incluir SKIPs y MISSINGs)
  1 -> error de usuario (auth, env file, etc.)
  2 -> error interno (gh/aws fallo)
"""

from pathlib import Path

from shared.paths import PROJECT_ROOT
from sync_secrets.targets import sync_client
from sync_secrets.targets import sync_devcli
from sync_secrets.targets import sync_server


def main(flags: dict) -> int:
    """Entry point. flags ya validado por flags.py.

    C901 ignorado: este es un orquestador CLI con routing por categoria.
    """
    env = flags['env']
    category = flags['category']
    dry_run = flags['dry_run']
    keys_filter = _parse_keys(flags['keys'])
    create_env = flags['create_env']
    aws_profile = flags['aws_profile'] or None

    print(
        f'[sync_secrets] env={env} category={category} dry_run={dry_run}',
    )
    if keys_filter:
        print(f'[sync_secrets] keys filter: {sorted(keys_filter)}')

    client_root = PROJECT_ROOT / 'docker' / 'env' / 'client'
    server_root = PROJECT_ROOT / 'docker' / 'env' / 'server'
    devcli_root = PROJECT_ROOT / 'docker' / 'env' / 'dev-cli'
    catalog_dir = (
        PROJECT_ROOT
        / 'serverless'
        / 'lambda'
        / 'resources'
        / 'secrets'
    )

    totals = {
        'PUSH': 0,
        'CREATE': 0,
        'SKIP': 0,
        'MISSING': 0,
        'LOCAL-ONLY': 0,
        'ERROR': 0,
    }

    if category in ('all', 'client'):
        counters = sync_client(
            env=env,
            env_file=client_root / f'.{env}',
            dry_run=dry_run,
            keys_filter=keys_filter,
            create_env=create_env,
        )
        _accumulate(totals, counters)

    if category in ('all', 'server'):
        counters = sync_server(
            stage=env,
            env_file=server_root / f'.{env}',
            catalog_dir=catalog_dir,
            aws_profile=aws_profile,
            dry_run=dry_run,
            keys_filter=keys_filter,
        )
        _accumulate(totals, counters)

    if category in ('all', 'dev-cli'):
        counters = sync_devcli(
            env=env,
            env_file=devcli_root / f'.{env}',
        )
        _accumulate(totals, counters)

    print(
        f'\n[RESUMEN] PUSH={totals["PUSH"]} CREATE={totals["CREATE"]} '
        f'SKIP={totals["SKIP"]} MISSING={totals["MISSING"]} '
        f'LOCAL-ONLY={totals["LOCAL-ONLY"]} ERROR={totals["ERROR"]}',
    )
    return 2 if totals['ERROR'] > 0 else 0


def _parse_keys(raw: str) -> set[str] | None:
    """Parse "A,B,C" -> {"A","B","C"}. None si vacio."""
    if not raw:
        return None
    return {k.strip() for k in raw.split(',') if k.strip()}


def _accumulate(totals: dict[str, int], counters: dict[str, int]) -> None:
    for k, v in counters.items():
        totals[k] = totals.get(k, 0) + v
