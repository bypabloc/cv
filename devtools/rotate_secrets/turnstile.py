"""Turnstile service handler: setup/rotate widgets and write env files.

Estrategia:
  - 3 widgets en Cloudflare (uno por env logico: dev, stage, prod).
  - .local y .test reusan el widget dev (su allowlist incluye localhost).
  - Cada widget cubre los hostnames del estandar de subdominios del portfolio.

El bypass de Turnstile para tests E2E ya NO se gestiona aca: es un token
Ed25519 firmado cuyas claves genera `bypass_token keygen` (ver
devtools/bypass_token/). Este script solo gestiona el secret REAL del
widget Cloudflare (TURNSTILE_SECRET_KEY) + el sitekey publico.
"""

from __future__ import annotations

from pathlib import Path

from rotate_secrets.cloudflare_api import CloudflareError
from rotate_secrets.cloudflare_api import TurnstileClient
from rotate_secrets.env_writer import update_env_file
from shared.paths import PROJECT_ROOT


ENV_SERVER_DIR = PROJECT_ROOT / 'docker' / 'env' / 'server'
ENV_CLIENT_DIR = PROJECT_ROOT / 'docker' / 'env' / 'client'

WIDGET_NAME_PREFIX = 'Portfolio Backend'

# Definicion de widgets por env logico (dev, stage, prod). Hostnames alineados
# con el estandar de subdominios `[{component}.]{product}.{env}.{domain}` y el
# apex `the-full-stack.com` para prod.
_WIDGETS = {
    'dev': {
        'name': f'{WIDGET_NAME_PREFIX} (dev)',
        'domains': [
            'localhost',
            '127.0.0.1',
            'the-full-stack.com',
            'dev.the-full-stack.com',
            'hub.portfolio.dev.the-full-stack.com',
            'fintech.portfolio.dev.the-full-stack.com',
            'architect.portfolio.dev.the-full-stack.com',
            'leader.portfolio.dev.the-full-stack.com',
            'vibe.portfolio.dev.the-full-stack.com',
            'generic.portfolio.dev.the-full-stack.com',
            'admin.portfolio.dev.the-full-stack.com',
        ],
    },
    'stage': {
        'name': f'{WIDGET_NAME_PREFIX} (stage)',
        'domains': [
            'stage.the-full-stack.com',
            'hub.portfolio.stage.the-full-stack.com',
            'fintech.portfolio.stage.the-full-stack.com',
            'architect.portfolio.stage.the-full-stack.com',
            'leader.portfolio.stage.the-full-stack.com',
            'vibe.portfolio.stage.the-full-stack.com',
            'generic.portfolio.stage.the-full-stack.com',
            'admin.portfolio.stage.the-full-stack.com',
        ],
    },
    'prod': {
        'name': f'{WIDGET_NAME_PREFIX} (prod)',
        'domains': [
            'the-full-stack.com',
            'www.the-full-stack.com',
            'hub.portfolio.the-full-stack.com',
            'fintech.portfolio.the-full-stack.com',
            'architect.portfolio.the-full-stack.com',
            'leader.portfolio.the-full-stack.com',
            'vibe.portfolio.the-full-stack.com',
            'generic.portfolio.the-full-stack.com',
            'admin.portfolio.the-full-stack.com',
        ],
    },
}

# .local y .test reusan el widget dev (su allowlist incluye localhost).
ENV_TO_WIDGET = {
    'local': 'dev',
    'test': 'dev',
    'dev': 'dev',
    'stage': 'stage',
    'prod': 'prod',
}


def _resolve_widget(
    client: TurnstileClient,
    existing_by_name: dict[str, dict],
    *,
    widget_key: str,
    force: bool,
    rotate: bool,
    dry_run: bool,
) -> dict[str, str]:
    """Resuelve sitekey + secret de un widget logico (dev/stage/prod)."""
    conf = _WIDGETS[widget_key]
    name = conf['name']
    domains = conf['domains']

    if name in existing_by_name and not force:
        widget = existing_by_name[name]
        sitekey = widget['sitekey']
        print(f'  [{widget_key}] reusando widget existente "{name}"')
        print(f'        sitekey={sitekey}')

        if rotate:
            print('        rotando secret...')
            if dry_run:
                secret = '<dry-run>'  # noqa: S105
            else:
                result = client.rotate_secret(sitekey)
                secret = result['secret']
        else:
            full = client.get_widget(sitekey)
            secret = full.get('secret', '')
            if not secret:
                print('        WARN: API no retorna secret. Rotando...')
                if dry_run:
                    secret = '<dry-run>'  # noqa: S105
                else:
                    result = client.rotate_secret(sitekey)
                    secret = result['secret']
        return {'sitekey': sitekey, 'secret': secret}

    print(f'  [{widget_key}] creando widget "{name}"')
    print(f'        domains: {domains}')
    if dry_run:
        return {
            'sitekey': f'<dry-run-sitekey-{widget_key}>',
            'secret': f'<dry-run-secret-{widget_key}>',
        }
    created = client.create_widget(name=name, domains=domains)
    print(f'        sitekey={created["sitekey"]}')
    return {'sitekey': created['sitekey'], 'secret': created['secret']}


def _write_env_files(
    widget_data: dict[str, dict[str, str]],
    *,
    envs: list[str],
    dry_run: bool,
) -> None:
    """Escribe sitekey + secret del widget en server/client envs."""
    print('\n=== Escribiendo env files ===')
    for env in envs:
        mapped_to = ENV_TO_WIDGET[env]
        data = widget_data[mapped_to]
        sitekey = data['sitekey']
        secret = data['secret']

        print(f'\n  [.{env}] usa widget de "{mapped_to}"')

        server_path = ENV_SERVER_DIR / f'.{env}'
        update_env_file(
            server_path,
            {
                'TURNSTILE_SECRET_KEY': secret,
            },
            dry_run=dry_run,
        )

        client_path = ENV_CLIENT_DIR / f'.{env}'
        update_env_file(
            client_path,
            {
                'PUBLIC_TURNSTILE_SITEKEY': sitekey,
                'TURNSTILE_SITE_KEY': sitekey,
            },
            dry_run=dry_run,
        )


def _print_summary(widget_data: dict[str, dict[str, str]]) -> None:
    print('\n=== Resumen ===')
    for widget_key, data in widget_data.items():
        sitekey = data['sitekey']
        secret = data['secret']
        if len(secret) > 12:
            sec_preview = f'{secret[:6]}...{secret[-4:]}'
        else:
            sec_preview = secret
        print(f'  {_WIDGETS[widget_key]["name"]}')
        print(f'    sitekey: {sitekey}')
        print(f'    secret:  {sec_preview}')


def run(
    *,
    api_token: str,
    account_id: str,
    envs: list[str],
    force: bool,
    rotate: bool,
    dry_run: bool,
) -> int:
    """Entry point del subcommand `turnstile`."""
    print('=== Cloudflare Turnstile setup ===')
    print(f'  account_id={account_id[:8]}... (longitud={len(account_id)})')
    print(f'  token=*** (longitud={len(api_token)})')
    print(f'  envs={envs}')
    print(f'  force={force} rotate={rotate} dry_run={dry_run}')

    try:
        with TurnstileClient(
            api_token=api_token,
            account_id=account_id,
        ) as client:
            print('\n=== Listando widgets existentes ===')
            existing = client.list_widgets()
            by_name = {w['name']: w for w in existing}
            for widget in existing:
                print(f'  - {widget["name"]} | sitekey={widget["sitekey"]}')

            print('\n=== Resolviendo widgets por env logico ===')
            widget_data: dict[str, dict[str, str]] = {}
            for widget_key in _WIDGETS:
                widget_data[widget_key] = _resolve_widget(
                    client,
                    by_name,
                    widget_key=widget_key,
                    force=force,
                    rotate=rotate,
                    dry_run=dry_run,
                )

        _write_env_files(widget_data, envs=envs, dry_run=dry_run)
        _print_summary(widget_data)

        if dry_run:
            print('\nDRY RUN: nada se escribio en disco ni en Cloudflare.')
        else:
            print(
                '\nLISTO. Siguiente paso: sincronizar SSM con '
                '`serverless setup-ssm --name=/portfolio/<stage>/turnstile-secret`.'
            )
    except CloudflareError as exc:
        print(f'\nERROR Cloudflare API: {exc}')
        if exc.errors:
            print(f'  details: {exc.errors}')
        return 1

    return 0
