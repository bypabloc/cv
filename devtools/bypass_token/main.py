"""Keygen + mint del token de bypass de Turnstile (Ed25519).

  python devtools/run.py bypass_token keygen [--envs=dev] [--dry-run]
  python devtools/run.py bypass_token mint --env=dev [--private-key=...]

keygen: genera un par Ed25519 por env. La PRIVADA va a
        docker/env/dev-cli/.{env} (local-only, gitignored); la PUBLICA va a
        docker/env/server/.{env} para que `sync_secrets`/`setup-ssm` la
        publique a SSM. La privada NUNCA se imprime en stdout (hermetico).

mint:   firma un token efimero (TTL 300s default) para usar en curl:
          curl -H "X-Turnstile-Bypass-Token: <token>" ...
        La privada se pasa con --private-key o se resuelve de
        docker/env/dev-cli/.{env} (extraida con grep, NO se lee el .env
        completo — ver .claude/rules/env-files.md).

NUNCA prod: el bypass de Turnstile no existe en produccion.
"""

from __future__ import annotations

import time

from rotate_secrets.env_writer import update_env_file
from shared.bypass_token import generate_keypair
from shared.bypass_token import sign_bypass_token
from shared.paths import PROJECT_ROOT


_ENV_DEV_CLI_DIR = PROJECT_ROOT / 'docker' / 'env' / 'dev-cli'
_ENV_SERVER_DIR = PROJECT_ROOT / 'docker' / 'env' / 'server'

_PRIVATE_KEY = 'TURNSTILE_BYPASS_PRIVATE_KEY'
_PUBLIC_KEY = 'TURNSTILE_BYPASS_PUBLIC_KEY'


def _cmd_keygen(*, envs: list[str], dry_run: bool) -> int:
    """Genera un par Ed25519 por env y lo escribe a los env files."""
    print('=== bypass_token keygen (Ed25519) ===')
    print(f'  envs={envs} dry_run={dry_run}')
    for env in envs:
        private_b64, public_b64 = generate_keypair()
        print(f'\n  [.{env}] par Ed25519 generado')
        # PRIVADA -> dev-cli (local-only). NUNCA se imprime el valor.
        update_env_file(
            _ENV_DEV_CLI_DIR / f'.{env}',
            {_PRIVATE_KEY: private_b64},
            dry_run=dry_run,
        )
        # PUBLICA -> server (se sincroniza a SSM con sync_secrets/setup-ssm).
        # La publica NO es secreta; mostrar un preview ayuda a verificar.
        preview = f'{public_b64[:8]}...{public_b64[-6:]}'
        print(f'        public={preview}')
        update_env_file(
            _ENV_SERVER_DIR / f'.{env}',
            {_PUBLIC_KEY: public_b64},
            dry_run=dry_run,
        )

    if dry_run:
        print('\nDRY RUN: nada se escribio en disco.')
    else:
        print(
            '\nLISTO. Siguiente paso: publicar la clave PUBLICA a SSM con\n'
            '  python devtools/run.py serverless setup-ssm '
            '--name=/portfolio/<env>/turnstile-bypass-public-key '
            '--env=<env> --aws-profile=tfs-dev\n'
            'o `sync_secrets --category=server`.',
        )
    return 0


def _resolve_private_key(env: str, private_key: str | None) -> str:
    """Resuelve la privada: flag explicita o extraccion puntual del .env.

    NO lee el .env completo: extrae SOLO la key con el patron anclado
    (.claude/rules/env-files.md). El valor viaja en proceso, nunca a stdout.
    """
    if private_key:
        return private_key
    path = _ENV_DEV_CLI_DIR / f'.{env}'
    if not path.exists():
        msg = (
            f'No existe {path} y no se paso --private-key. Corre primero '
            f'`bypass_token keygen --envs={env}`.'
        )
        raise SystemExit(msg)
    prefix = f'{_PRIVATE_KEY}='
    for line in path.read_text().splitlines():
        if line.startswith(prefix):
            return line[len(prefix) :].strip()
    msg = (
        f'{_PRIVATE_KEY} no esta en {path}. Corre '
        f'`bypass_token keygen --envs={env}` para generarla.'
    )
    raise SystemExit(msg)


def _cmd_mint(*, env: str, private_key: str | None, ttl: int) -> int:
    """Firma un token efimero y lo imprime (solo el token, para curl)."""
    resolved = _resolve_private_key(env, private_key)
    if not resolved:
        msg = (
            f'La clave privada de {env} esta vacia. Corre '
            f'`bypass_token keygen --envs={env}`.'
        )
        raise SystemExit(msg)
    token = sign_bypass_token(
        stage=env,
        private_key_b64=resolved,
        now=int(time.time()),
        ttl=ttl,
    )
    # SOLO el token a stdout (para `curl -H "X-Turnstile-Bypass-Token: $(...)"`).
    print(token)
    return 0


def main(flags: dict) -> int:
    """Entry point del script bypass_token."""
    command = flags['command']
    if command == 'keygen':
        return _cmd_keygen(
            envs=flags['envs'],
            dry_run=flags.get('dry_run', False),
        )
    if command == 'mint':
        return _cmd_mint(
            env=flags['env'],
            private_key=flags.get('private_key'),
            ttl=flags.get('ttl', 300),
        )
    raise SystemExit(f'Comando no soportado: {command!r}')
