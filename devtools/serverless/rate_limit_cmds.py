"""Rate-limit management commands.

Gestion de la tabla `rate_limit_rules` (configuracion) y de la tabla
`rate_limit_buckets` (counters). Reemplaza la funcionalidad que en otras
arquitecturas dan AWS WAF rate-based rules — pero a costo $0 (free tier
DynamoDB perpetuo).

Subcomandos (segundo positional despues de `rate-limit`):

    list                       Lista todas las reglas
    show <key>                 Detalle de una regla especifica
    set                        Crear/actualizar regla endpoint o country
    allow                      Agregar IP a whitelist
    block                      Agregar IP a blacklist (con TTL opcional)
    unblock                    Eliminar IP de blacklist
    stats                      Top IPs throttled + auto-blacklists
    clear-buckets              Resetear counters (DESTRUCTIVO, debugging)

API CLI:
    serverless rate-limit list
    serverless rate-limit set --endpoint=/contact --limit=3 --window=300
    serverless rate-limit allow --ip=X.X.X.X
    serverless rate-limit block --ip=X.X.X.X --ttl=86400
    serverless rate-limit unblock --ip=X.X.X.X
    serverless rate-limit stats --since=1h
    serverless rate-limit clear-buckets --confirm
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from typing import Any

from shared.console import CYAN
from shared.console import DIM
from shared.console import GREEN
from shared.console import RED
from shared.console import YELLOW
from shared.console import _c
from shared.console import _err


# Las tablas DynamoDB siguen el patron `portfolio-<recurso>-<stage>` definido
# por devtools al provisionar. El stage default es `dev` (el unico que el
# laptop opera habitualmente). Pasar `--stage=prod` para gestionar produccion.
_DEFAULT_STAGE = 'dev'
_VALID_STAGES = ('dev', 'stage', 'prod')
_REGION = 'us-east-1'

# Tablas resueltas por la cmd_rate_limit() del dispatcher segun --stage.
# Default apunta a dev (caso comun del laptop). Reescrito por el dispatcher
# en cada invocacion antes de llamar al handler.
_RULES_TABLE = f'portfolio-rate-limit-rules-{_DEFAULT_STAGE}'
_BUCKETS_TABLE = f'portfolio-rate-limit-buckets-{_DEFAULT_STAGE}'


def _resolve_stage(flags: dict[str, Any]) -> str:
    """Resuelve el stage del CLI, validando contra el set permitido.

    Si el parser pasa 'local' (default del flag global de serverless), cae
    al default `_DEFAULT_STAGE` porque las tablas de rate-limit no existen
    en local (DynamoDB local no esta provisionado).
    """
    stage = flags.get('stage') or _DEFAULT_STAGE
    if stage == 'local':
        return _DEFAULT_STAGE
    if stage not in _VALID_STAGES:
        _err(
            f'--stage={stage!r} invalido. Validos: {", ".join(_VALID_STAGES)}',
        )
        return _DEFAULT_STAGE
    return stage


def _rules_table(stage: str) -> str:
    return f'portfolio-rate-limit-rules-{stage}'


def _buckets_table(stage: str) -> str:
    return f'portfolio-rate-limit-buckets-{stage}'


_VALID_ACTIONS = [
    'list',
    'show',
    'set',
    'allow',
    'block',
    'unblock',
    'unblock-all',
    'stats',
    'clear-buckets',
]

# Endpoints validos para `rate-limit set`. El Lambda `auth` usa keys
# compuestas `/auth#<operation>.<action>` (el controller las pasa a
# shared.rate_limit.check_or_raise) para tener una regla por accion.
_VALID_ENDPOINTS = [
    '/contact',
    '/track',
    '*',
    '/auth#register.start',
    '/auth#register.verify-magic-link',
    '/auth#register.verify-code',
    '/auth#login.start',
    '/auth#login.verify-magic-link',
    '/auth#login.verify-code',
    '/auth#verify.set-password',
    '/auth#verify.resend-code',
    '/auth#session.refresh',
    '/auth#session.logout',
    # Plan 02 (MFA + WebAuthn + login con password).
    '/auth#mfa.setup-totp',
    '/auth#mfa.confirm-totp',
    '/auth#mfa.recovery-codes-consume',
    '/auth#webauthn.register-options',
    '/auth#webauthn.login-options',
    '/auth#webauthn.login-verify',
    '/auth#login.verify-password',
    '/auth#login.verify-totp',
    # Plan 03 (gestion de usuarios: profile / status / admin). JWT-authed
    # (sin Turnstile). status y admin comparten una key por operation.
    '/users#profile.get',
    '/users#profile.update',
    '/users#profile.change-email',
    '/users#profile.confirm-email-change',
    '/users#profile.delete-account',
    '/users#status',
    '/users#admin',
]


def _ensure_aws_cli() -> bool:
    """Verifica aws CLI disponible."""
    if shutil.which('aws') is None:
        _err('AWS CLI no esta instalado')
        return False
    return True


def _run_aws(args: list[str]) -> tuple[int, str, str]:
    """Ejecuta `aws <args>` capturando stdout/stderr.

    Returns (returncode, stdout, stderr).
    """
    result = subprocess.run(
        ['aws', *args, '--region', _REGION],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode, result.stdout, result.stderr


def cmd_rate_limit(flags: dict[str, Any]) -> int:
    """Dispatcher para `serverless rate-limit <action>`."""
    if not _ensure_aws_cli():
        return 1

    # Resuelve el stage y reescribe las tablas globales para los handlers.
    # No se pasa como arg para no tocar las 8 firmas existentes.
    global _RULES_TABLE, _BUCKETS_TABLE
    stage = _resolve_stage(flags)
    _RULES_TABLE = _rules_table(stage)
    _BUCKETS_TABLE = _buckets_table(stage)

    # Propaga --aws-profile como env var para que los `aws ...` heredados lo
    # usen sin tocar la firma de _run_aws.
    aws_profile = flags.get('aws_profile')
    if aws_profile:
        os.environ['AWS_PROFILE'] = aws_profile

    subcommands = flags.get('subcommands', []) or []
    action = subcommands[1] if len(subcommands) > 1 else 'list'

    if action not in _VALID_ACTIONS:
        _err(f'Sub-accion invalida: {action!r}')
        print(f'{YELLOW}  Validas: {", ".join(_VALID_ACTIONS)}{NC}')
        return 2

    handlers = {
        'list': _rate_limit_list,
        'show': _rate_limit_show,
        'set': _rate_limit_set,
        'allow': _rate_limit_allow,
        'block': _rate_limit_block,
        'unblock': _rate_limit_unblock,
        'unblock-all': _rate_limit_unblock_all,
        'stats': _rate_limit_stats,
        'clear-buckets': _rate_limit_clear_buckets,
    }
    return handlers[action](flags)


def _rate_limit_unblock_all(flags: dict[str, Any]) -> int:
    """Elimina TODAS las entries kind=ip_blacklist (manual + auto).

    Util para limpiar el estado durante testing (cuando una IP del dev
    quedo blacklisteada y dispara 403 en /track o /contact). Requiere
    --confirm para evitar accidentes.
    """
    if not flags.get('confirm'):
        _err('Falta --confirm. Esta accion borra TODAS las IPs blacklisted.')
        print(
            f'{DIM}  Ejemplo: serverless rate-limit unblock-all --confirm{NC}'
        )
        return 2

    # 1. Scan filtrado por kind=ip_blacklist
    code, stdout, stderr = _run_aws(
        [
            'dynamodb',
            'scan',
            '--table-name',
            _RULES_TABLE,
            '--filter-expression',
            'kind = :k',
            '--expression-attribute-values',
            json.dumps({':k': {'S': 'ip_blacklist'}}),
            '--output',
            'json',
        ]
    )
    if code != 0:
        _err(f'Scan fallo: {stderr.strip()}')
        return code

    items = json.loads(stdout).get('Items', [])
    if not items:
        print(_c(GREEN, 'No hay IPs blacklisted. Nada que limpiar.'))
        return 0

    # 2. Delete uno por uno (no hay BatchWriteItem keyed por SK aqui)
    removed = 0
    for item in items:
        rule_key = item.get('rule_key', {}).get('S')
        kind = item.get('kind', {}).get('S')
        if not (rule_key and kind):
            continue
        del_code, _, del_stderr = _run_aws(
            [
                'dynamodb',
                'delete-item',
                '--table-name',
                _RULES_TABLE,
                '--key',
                json.dumps({'rule_key': {'S': rule_key}, 'kind': {'S': kind}}),
            ]
        )
        if del_code != 0:
            _err(f'Fallo borrar {rule_key}: {del_stderr.strip()}')
            continue
        removed += 1
        print(f'  - {_c(GREEN, "removed")} {rule_key}')

    print(_c(GREEN, f'\nOK: {removed} IP(s) blacklisted eliminada(s).'))
    return 0


# ---------------------------------------------------------------------------
# list / show
# ---------------------------------------------------------------------------


def _rate_limit_list(flags: dict[str, Any]) -> int:
    """Lista todas las reglas activas en rate_limit_rules.

    Output text (default) o JSON via --output=json.
    """
    output = flags.get('output', 'text')

    code, stdout, stderr = _run_aws(
        [
            'dynamodb',
            'scan',
            '--table-name',
            _RULES_TABLE,
            '--output',
            'json',
        ]
    )
    if code != 0:
        _err(f'Scan fallo: {stderr.strip()}')
        return code

    data = json.loads(stdout)
    items = data.get('Items', [])

    if output == 'json':
        print(json.dumps(items, indent=2))
        return 0

    if not items:
        print(_c(YELLOW, 'No hay reglas configuradas.'))
        print(
            f'{DIM}  Usa `serverless rate-limit set` para crear la primera regla{NC}',
        )
        return 0

    print(_c(CYAN, f'Reglas activas en {_RULES_TABLE}:'))
    print()
    print(
        f'{"rule_key":<40} {"kind":<15} {"limit":<8} {"window":<10} {"action":<10} reason'
    )
    print('-' * 110)

    for item in items:
        rule_key = item['rule_key']['S']
        kind = item.get('kind', {}).get('S', '-')
        limit = item.get('limit', {}).get('N', '-')
        window = item.get('window_seconds', {}).get('N', '-')
        action = item.get('action', {}).get('S', '-')
        reason = item.get('reason', {}).get('S', '')[:40]
        color = (
            RED
            if kind == 'ip_blacklist'
            else (GREEN if kind == 'ip_whitelist' else '')
        )
        print(
            f'{_c(color, rule_key):<40} {kind:<15} {limit:<8} {window:<10} {action:<10} {reason}'
        )

    print()
    print(_c(DIM, f'Total: {len(items)} reglas'))
    return 0


def _rate_limit_show(flags: dict[str, Any]) -> int:
    """Detalle de una regla por rule_key."""
    subcommands = flags.get('subcommands', []) or []
    rule_key = subcommands[2] if len(subcommands) > 2 else flags.get('name')

    if not rule_key:
        _err('Se requiere rule_key como tercer argumento o --name=<rule_key>')
        return 2

    code, stdout, stderr = _run_aws(
        [
            'dynamodb',
            'get-item',
            '--table-name',
            _RULES_TABLE,
            '--key',
            json.dumps({'rule_key': {'S': rule_key}}),
            '--output',
            'json',
        ]
    )
    if code != 0:
        _err(f'GetItem fallo: {stderr.strip()}')
        return code

    data = json.loads(stdout or '{}')
    item = data.get('Item')
    if not item:
        _err(f'No existe regla con rule_key={rule_key!r}')
        return 1

    print(_c(CYAN, f'Regla: {rule_key}'))
    print()
    for k, v in item.items():
        val = next(
            iter(v.values())
        )  # extract first val of {S/N/SS/...} envelope
        print(f'  {k:<20} {val}')
    return 0


# ---------------------------------------------------------------------------
# set
# ---------------------------------------------------------------------------


def _rate_limit_set(flags: dict[str, Any]) -> int:
    """Crear/actualizar regla de endpoint o country.

    Required: --endpoint=/contact o --country=XX
    Optional: --limit=N, --window=N (seconds), --action=throttle|block
    """
    endpoint = flags.get('endpoint')
    country = flags.get('country')

    if not endpoint and not country:
        _err('Se requiere --endpoint=/contact o --country=XX')
        return 2

    if endpoint and endpoint not in _VALID_ENDPOINTS:
        _err(
            f'Endpoint invalido: {endpoint!r}. Validos: {", ".join(_VALID_ENDPOINTS)}'
        )
        return 2

    if country and (len(country) != 2 or not country.isalpha()):
        _err(
            f'Country invalido: {country!r}. Usar ISO 3166-1 alpha-2 (ej. CL, MX, US)'
        )
        return 2

    if endpoint:
        rule_key = f'endpoint#{endpoint}'
        kind = 'endpoint'
    else:
        rule_key = f'country#{country.upper()}'
        kind = 'country'

    limit = int(flags.get('limit', 10))
    window = int(flags.get('window', 300))
    action = flags.get('action', 'throttle')
    reason = flags.get('reason', f'set via CLI {time.strftime("%Y-%m-%d")}')

    item = {
        'rule_key': {'S': rule_key},
        'kind': {'S': kind},
        'limit': {'N': str(limit)},
        'window_seconds': {'N': str(window)},
        'action': {'S': action},
        'reason': {'S': reason},
        'created_at': {'S': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())},
        'created_by': {'S': 'cli'},
    }

    if flags.get('dry_run'):
        print(_c(YELLOW, '[dry-run] PutItem:'))
        print(json.dumps(item, indent=2))
        return 0

    code, _stdout, stderr = _run_aws(
        [
            'dynamodb',
            'put-item',
            '--table-name',
            _RULES_TABLE,
            '--item',
            json.dumps(item),
        ]
    )
    if code != 0:
        _err(f'PutItem fallo: {stderr.strip()}')
        return code

    print(_c(GREEN, f'OK  Regla guardada: {rule_key}'))
    print(f'  limit={limit} window={window}s action={action}')
    return 0


# ---------------------------------------------------------------------------
# allow / block / unblock
# ---------------------------------------------------------------------------


def _put_ip_rule(
    ip: str, kind: str, ttl_seconds: int | None, reason: str, dry_run: bool
) -> int:
    """Helper compartido para crear items kind=ip_whitelist|ip_blacklist."""
    item = {
        'rule_key': {'S': f'ip#{ip}'},
        'kind': {'S': kind},
        'action': {'S': 'block' if kind == 'ip_blacklist' else 'allow'},
        'reason': {'S': reason},
        'created_at': {'S': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())},
        'created_by': {'S': 'cli'},
    }
    if ttl_seconds:
        item['expires_at'] = {'N': str(int(time.time()) + ttl_seconds)}

    if dry_run:
        print(_c(YELLOW, '[dry-run] PutItem:'))
        print(json.dumps(item, indent=2))
        return 0

    code, _stdout, stderr = _run_aws(
        [
            'dynamodb',
            'put-item',
            '--table-name',
            _RULES_TABLE,
            '--item',
            json.dumps(item),
        ]
    )
    if code != 0:
        _err(f'PutItem fallo: {stderr.strip()}')
        return code

    print(_c(GREEN, f'OK  {kind} aplicado a IP {ip}'))
    if ttl_seconds:
        print(f'  TTL: {ttl_seconds}s ({ttl_seconds // 3600}h)')
    return 0


def _validate_ip(ip: str) -> bool:
    """Validacion basica de IPv4 o IPv6."""
    import ipaddress

    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def _rate_limit_allow(flags: dict[str, Any]) -> int:
    """Agregar IP a whitelist (skip rate-limit)."""
    ip = flags.get('ip')
    if not ip:
        _err('Se requiere --ip=X.X.X.X')
        return 2
    if not _validate_ip(ip):
        _err(f'IP invalida: {ip!r}')
        return 2

    reason = flags.get('reason', 'whitelist via CLI')
    return _put_ip_rule(
        ip, 'ip_whitelist', None, reason, bool(flags.get('dry_run'))
    )


def _rate_limit_block(flags: dict[str, Any]) -> int:
    """Agregar IP a blacklist con TTL opcional."""
    ip = flags.get('ip')
    if not ip:
        _err('Se requiere --ip=X.X.X.X')
        return 2
    if not _validate_ip(ip):
        _err(f'IP invalida: {ip!r}')
        return 2

    ttl = flags.get('ttl')
    ttl_seconds = int(ttl) if ttl else None

    reason = flags.get('reason', 'blacklist via CLI')
    return _put_ip_rule(
        ip, 'ip_blacklist', ttl_seconds, reason, bool(flags.get('dry_run'))
    )


def _rate_limit_unblock(flags: dict[str, Any]) -> int:
    """Eliminar IP de whitelist/blacklist."""
    if not flags.get('confirm'):
        _err('--confirm requerido para eliminar regla de IP')
        return 2

    ip = flags.get('ip')
    if not ip:
        _err('Se requiere --ip=X.X.X.X')
        return 2

    rule_key = f'ip#{ip}'
    if flags.get('dry_run'):
        print(_c(YELLOW, f'[dry-run] DeleteItem rule_key={rule_key}'))
        return 0

    code, _stdout, stderr = _run_aws(
        [
            'dynamodb',
            'delete-item',
            '--table-name',
            _RULES_TABLE,
            '--key',
            json.dumps({'rule_key': {'S': rule_key}}),
        ]
    )
    if code != 0:
        _err(f'DeleteItem fallo: {stderr.strip()}')
        return code

    print(_c(GREEN, f'OK  IP {ip} desbloqueada (regla eliminada)'))
    return 0


# ---------------------------------------------------------------------------
# stats / clear-buckets
# ---------------------------------------------------------------------------


def _rate_limit_stats(flags: dict[str, Any]) -> int:
    """Top IPs throttled + auto-blacklists triggered.

    Lee de CloudWatch metrics custom (RateLimitBlocked, AutoBlacklistTriggered).
    """
    output = flags.get('output', 'text')
    since = flags.get('since', '1h')

    duration = {
        '1h': '-PT1H',
        '6h': '-PT6H',
        '24h': '-PT24H',
        '7d': '-P7D',
    }.get(
        since,
        '-PT1H',
    )

    metrics = [
        ('RateLimitChecks', 'Total de checks ejecutados'),
        ('RateLimitBlocked', 'Requests bloqueados por blacklist/country'),
        ('RateLimitThrottled', 'Requests devueltos con 429'),
        ('AutoBlacklistTriggered', 'IPs auto-blacklisted por patron bot'),
    ]

    print(_c(CYAN, f'Stats ultimos {since} (us-east-1):'))
    print()

    results = {}
    for metric_name, description in metrics:
        code, stdout, _stderr = _run_aws(
            [
                'cloudwatch',
                'get-metric-statistics',
                '--namespace',
                'portfolio',
                '--metric-name',
                metric_name,
                '--start-time',
                duration,
                '--end-time',
                'now',
                '--period',
                '3600',
                '--statistics',
                'Sum',
                '--output',
                'json',
                '--query',
                'Datapoints[*].Sum',
            ]
        )
        if code == 0:
            sums = json.loads(stdout) if stdout.strip() else []
            total = sum(sums) if sums else 0
            results[metric_name] = total
            print(
                f'  {_c(CYAN, metric_name):<35} {int(total):>8}  {DIM}{description}{NC}'
            )

    if output == 'json':
        print()
        print(json.dumps(results, indent=2))

    return 0


def _rate_limit_clear_buckets(flags: dict[str, Any]) -> int:
    """Resetear todos los counters de rate_limit_buckets (DESTRUCTIVO).

    Util solo en debugging local. NUNCA en prod (cada usuario perderia
    su counter y un atacante podria reanudar burst).
    """
    if not flags.get('confirm'):
        _err('--confirm requerido para clear-buckets')
        return 2

    if flags.get('dry_run'):
        print(_c(YELLOW, '[dry-run] Scan + BatchDeleteItem rate_limit_buckets'))
        return 0

    print(_c(RED, 'CUIDADO: vas a eliminar TODOS los counters.'))
    print(
        f'{YELLOW}Esto solo es seguro en local/dev. En prod = reset del rate-limit{NC}'
    )
    print()

    # Scan to get all bucket_keys
    code, stdout, stderr = _run_aws(
        [
            'dynamodb',
            'scan',
            '--table-name',
            _BUCKETS_TABLE,
            '--projection-expression',
            'bucket_key',
            '--output',
            'json',
        ]
    )
    if code != 0:
        _err(f'Scan fallo: {stderr.strip()}')
        return code

    items = json.loads(stdout).get('Items', [])
    if not items:
        print(_c(GREEN, 'OK  Tabla ya vacia'))
        return 0

    # Batch delete in chunks of 25 (DynamoDB max batch size)
    deleted = 0
    for i in range(0, len(items), 25):
        chunk = items[i : i + 25]
        request_items = {
            _BUCKETS_TABLE: [
                {'DeleteRequest': {'Key': {'bucket_key': item['bucket_key']}}}
                for item in chunk
            ],
        }
        code, _stdout, stderr = _run_aws(
            [
                'dynamodb',
                'batch-write-item',
                '--request-items',
                json.dumps(request_items),
            ]
        )
        if code != 0:
            _err(f'BatchWriteItem fallo: {stderr.strip()}')
            return code
        deleted += len(chunk)

    print(_c(GREEN, f'OK  Eliminados {deleted} buckets'))
    return 0


# Re-export NC for the _put_ip_rule helper signature usage
NC = '\033[0m'
