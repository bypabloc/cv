"""Rotate or set up secrets/credentials for external services.

Subcommand-style script:
  python devtools/run.py rotate_secrets <service> [flags...]

Servicios soportados:
  turnstile    Configurar y/o rotar widgets Cloudflare Turnstile por env y
               escribir sitekey + secret en docker/env/{server,client}/.{env}

Cada servicio exige sus credenciales como flags explicitas. NO se leen
archivos .env automaticamente — el usuario extrae solo la key que necesita
(rule: .claude/rules/env-files.md):

  python devtools/run.py rotate_secrets turnstile \\
    --cloudflare-api-token="$(grep -m1 '^CLOUDFLARE_API_TOKEN=' \\
        docker/env/dev-cli/.prod | cut -d= -f2-)" \\
    --cloudflare-account-id="$(grep -m1 '^CLOUDFLARE_ACCOUNT_ID=' \\
        docker/env/dev-cli/.prod | cut -d= -f2-)"

Flags comunes:
  --dry-run     No escribe en disco ni hace cambios en Cloudflare
  --force       Para `turnstile`: crear widget aunque exista uno con el mismo nombre
  --rotate      Para `turnstile`: rotar el secret de widgets existentes
  --envs=local,test,dev,stage,prod
                Subset de envs a escribir (default: todos)
"""

from rotate_secrets import turnstile


def _dispatch_turnstile(flags: dict) -> int:
    return turnstile.run(
        api_token=flags['cloudflare_api_token'],
        account_id=flags['cloudflare_account_id'],
        envs=flags['envs'],
        force=flags.get('force', False),
        rotate=flags.get('rotate', False),
        dry_run=flags.get('dry_run', False),
    )


_DISPATCH = {
    'turnstile': _dispatch_turnstile,
}


def main(flags: dict) -> int:
    """Entry point invoked by ``devtools/run.py``."""
    command = flags['command']
    handler = _DISPATCH.get(command)
    if handler is None:
        # No deberia llegar aqui — flags.py ya valida VALID_SERVICES.
        print(f'Servicio no implementado: {command}')
        return 1
    return handler(flags)
