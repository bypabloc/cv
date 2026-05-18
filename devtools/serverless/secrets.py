"""Secrets and DNS commands for the SAM backend.

Maneja SSM Parameter Store (con KMS encryption) para secrets como el
Turnstile secret key y la Neon connection string. Tambien verifica los
records DNS de SES (DKIM/SPF/DMARC) en Cloudflare.
"""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
from typing import Any

from shared.console import CYAN
from shared.console import DIM
from shared.console import GREEN
from shared.console import NC
from shared.console import RED
from shared.console import YELLOW
from shared.console import _c
from shared.console import _err


_SERVERLESS_DIR = Path(__file__).resolve().parents[2] / 'serverless'

# Inventario de SSM Parameters que el modulo gestiona.
# Mantener sincronizado con .claude/rules/serverless-secrets.md.
_SSM_PARAMETERS: dict[str, dict[str, str]] = {
    '/portfolio/turnstile-secret': {
        'description': 'Cloudflare Turnstile secret key (siteverify)',
        'kind': 'SecureString',
    },
    '/portfolio/neon-url': {
        'description': 'Neon PostgreSQL connection string (legacy, fallback)',
        'kind': 'SecureString',
    },
    '/portfolio/dev/neon-url': {
        'description': 'Neon connection string del stage dev (psycopg3)',
        'kind': 'SecureString',
    },
    '/portfolio/prod/neon-url': {
        'description': 'Neon connection string del stage prod (psycopg3)',
        'kind': 'SecureString',
    },
    '/portfolio/owner-email': {
        'description': 'Email destino del form de contacto',
        'kind': 'String',
    },
    '/portfolio/ses-from-address': {
        'description': 'From address verificada en SES',
        'kind': 'String',
    },
}


def cmd_setup_ssm(flags: dict[str, Any]) -> int:
    """Crea o actualiza un SSM Parameter con KMS encryption.

    Requiere --name. El --value se lee de stdin (interactive) si no se
    pasa, para evitar leakear el secret en el shell history.
    """
    name = flags.get('name')
    if not name:
        _err('--name es requerido (ej. --name=/portfolio/turnstile-secret)')
        print()
        print(f'{YELLOW}Parameters conocidos:{NC}')
        for path, meta in _SSM_PARAMETERS.items():
            kind = meta['kind']
            desc = meta['description']
            print(f'  {_c(CYAN, path):<40} {_c(DIM, "[" + kind + "]")} {desc}')
        return 2

    if name not in _SSM_PARAMETERS:
        print(
            f'{YELLOW}  Aviso:{NC} {name!r} no esta en el inventario conocido. '
            f'Actualiza _SSM_PARAMETERS y .claude/rules/serverless-secrets.md.'
        )

    kind = _SSM_PARAMETERS.get(name, {}).get('kind', 'SecureString')

    value = flags.get('value')
    if not value:
        try:
            print(_c(CYAN, f'Valor para {name} (stdin, sin echo):'))
            import getpass

            value = getpass.getpass('  > ')
        except (KeyboardInterrupt, EOFError):
            print()
            _err('Cancelado')
            return 130

    if not value:
        _err('Valor vacio')
        return 1

    key_id = flags.get('key_id', 'alias/aws/ssm')

    args = [
        'aws',
        'ssm',
        'put-parameter',
        '--name',
        name,
        '--type',
        kind,
        '--value',
        value,
        '--overwrite',
        '--region',
        'us-east-1',
    ]
    if kind == 'SecureString':
        args.extend(['--key-id', key_id])

    # Imprime sin el value (que es secret)
    print(_c(CYAN, f'$ aws ssm put-parameter --name {name} --type {kind} ...'))

    result = subprocess.run(args, check=False)
    if result.returncode == 0:
        print(_c(GREEN, f'OK  {name} guardado en SSM'))
    return result.returncode


def cmd_rotate_secret(flags: dict[str, Any]) -> int:
    """Rotar el valor de un SSM Parameter (destructivo).

    Pide el nuevo valor por stdin, actualiza el parameter, y opcionalmente
    re-deploya las Lambdas para que tomen el nuevo valor (sin
    redeployar el cache de Powertools parameters expira a los 5min).
    """
    if not flags.get('confirm'):
        _err('--confirm requerido para rotar un secret')
        return 2

    return cmd_setup_ssm(flags)


def cmd_verify_ses_dns(flags: dict[str, Any]) -> int:
    """dig CNAMEs DKIM + TXT SPF/DMARC contra Cloudflare DNS.

    El SES Domain Identity expone 3 CNAMEs DKIM en us-east-1. Esta
    funcion los lee del template.yaml (o el output de sam deploy) y
    verifica con dig que existen en Cloudflare.
    """
    import shutil

    if shutil.which('dig') is None:
        _err('dig no esta instalado. Instalar: apt install dnsutils')
        return 1

    # TODO: leer de outputs de SAM. Por ahora hardcoded como template.
    domain = 'the-full-stack.com'

    print(_c(CYAN, f'Verificando DNS de {domain}...'))
    print()

    checks = [
        ('SPF (TXT)', ['dig', '+short', 'TXT', domain], 'amazonses.com'),
        ('DMARC (TXT)', ['dig', '+short', 'TXT', f'_dmarc.{domain}'], 'DMARC1'),
    ]

    all_ok = True
    for label, cmd, expected in checks:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
        output = result.stdout.strip()
        if expected.lower() in output.lower():
            print(f'  {_c(GREEN, "OK ")} {label}: {output}')
        else:
            print(
                f'  {_c(RED, "FAIL")} {label}: esperado {expected!r}, got {output!r}'
            )
            all_ok = False

    print()
    if all_ok:
        print(_c(GREEN, 'OK  Records SPF + DMARC correctos'))
        print(
            f'{YELLOW}  Pendiente:{NC} verificar 3 CNAMEs DKIM '
            f'(leer de aws sesv2 get-email-identity)'
        )
    else:
        _err(
            'Faltan records DNS — ver .claude/rules/serverless-secrets.md '
            '(seccion AWS SES) y el skill aws-ses'
        )

    return 0 if all_ok else 1


def cmd_request_ses_prod(flags: dict[str, Any]) -> int:
    """Imprime la plantilla del ticket de production access SES."""
    template = _SERVERLESS_DIR / 'scripts' / 'request_ses_production.md'

    if template.exists():
        print(template.read_text())
    else:
        print(
            _c(
                YELLOW,
                'Plantilla por defecto (crear scripts/request_ses_production.md para customizar):',
            )
        )
        print()
        print('---')
        print('Mail type: Transactional')
        print('Website URL: https://the-full-stack.com')
        print('Description:')
        print('  Personal portfolio contact form. Visitors fill a form on')
        print('  the-full-stack.com (and 5 niche subdomains). Each submission')
        print('  triggers ONE email to the site owner (Pablo Contreras).')
        print(
            '  Expected volume: 50-200 emails/month. Domain verified via DKIM.'
        )
        print('Compliance:')
        print('  - One recipient (owner email) per submission')
        print('  - Cloudflare Turnstile CAPTCHA validation server-side')
        print('  - AWS WAF rate-based rule 3 req/5min/IP')
        print('  - No marketing emails, no bulk sends, no lists')
        print('---')

    return 0
