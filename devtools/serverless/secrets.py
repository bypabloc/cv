"""Comandos del catalogo de secretos SSM.

setup-ssm, sync-secrets, secrets-status, validate-catalog, rotate-secret
y los comandos de SES DNS. El inventario hardcodeado `_SSM_PARAMETERS`
fue eliminado; la fuente de verdad ahora vive en
`serverless/lambda/resources/secrets/*.yaml`.
"""

from __future__ import annotations

from pathlib import Path
import subprocess
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

# Path al .env del backend serverless (categoria server).
_SERVER_ENV_DIR = _SERVERLESS_DIR.parent / 'docker' / 'env' / 'server'


def _expand_short_name(name: str, stage: str | None) -> tuple[str, Any]:
    """Resuelve `name` a (path SSM, SecretSpec).

    Acepta:
      - Nombre corto del catalogo (ej. 'turnstile-secret') + --stage.
      - Path SSM completo (ej. '/portfolio/dev/turnstile-secret').

    Devuelve (path, SecretSpec | None). Si es path completo y matchea
    algun spec, devuelve el spec; sino None.
    """
    from serverless.secrets_catalog import Catalog
    from serverless.secrets_catalog import CatalogError

    catalog = Catalog.load()

    if name.startswith('/'):
        # Path completo: buscar el spec que matchea
        for spec in catalog.by_name.values():
            for st in spec.stages:
                if spec.path_for(st) == name:
                    return name, spec
        return name, None

    try:
        spec = catalog.get(name)
    except CatalogError as exc:
        raise SystemExit(str(exc)) from exc

    if not stage:
        if len(spec.stages) == 1:
            stage = next(iter(spec.stages))
        else:
            raise SystemExit(
                f'{name!r} se publica en multiples stages '
                f'({sorted(spec.stages)}). Pasar --stage=<env>.',
            )

    return spec.path_for(stage), spec


def cmd_setup_ssm(flags: dict[str, Any]) -> int:
    """Crea o actualiza un SSM Parameter (puntual, valor por stdin).

    Acepta --name como path completo o nombre corto del catalogo
    (con --stage para resolver el path). Lee el valor por stdin
    (sin echo) para evitar leakearlo en el shell history.
    """
    name = flags.get('name')
    if not name:
        _err('--name es requerido')
        print()
        _print_catalog_inventory()
        return 2

    stage = flags.get('stage')
    try:
        path, spec = _expand_short_name(str(name), stage)
    except SystemExit as exc:
        _err(str(exc))
        return 2

    if spec is None:
        print(
            f'{YELLOW}  Aviso:{NC} {path!r} no matchea ningun spec del '
            f'catalogo. Verifica el path o agrega el secreto a '
            f'serverless/lambda/resources/secrets/.',
        )
        kind = 'SecureString'
        kms_alias = 'alias/portfolio-lambdas'
    else:
        kind = spec.ssm_type
        kms_alias = spec.kms_key_alias or 'alias/portfolio-lambdas'

    value = flags.get('value')
    if not value:
        try:
            print(_c(CYAN, f'Valor para {path} (stdin, sin echo):'))
            import getpass

            value = getpass.getpass('  > ')
        except (KeyboardInterrupt, EOFError):
            print()
            _err('Cancelado')
            return 130

    if not value:
        _err('Valor vacio')
        return 1

    return _put_parameter_secure(
        path=path,
        value=value,
        kind=kind,
        kms_alias=kms_alias,
        profile=flags.get('aws_profile'),
    )


def _put_parameter_secure(
    *,
    path: str,
    value: str,
    kind: str,
    kms_alias: str,
    profile: str | None,
) -> int:
    """Llama `aws ssm put-parameter` pasando el valor por tempfile.

    Hermetico: el valor pasa via `--value file://<tmp>` (perms 0600)
    para NO aparecer en `ps aux`.
    """
    import os
    import tempfile

    tmp_fd, tmp_path = tempfile.mkstemp(
        prefix='portfolio-ssm-',
        suffix='.tmp',
        dir='/tmp',
    )
    try:
        os.chmod(tmp_path, 0o600)
        with os.fdopen(tmp_fd, 'w', encoding='utf-8') as f:
            f.write(value)
        cmd = [
            'aws',
            'ssm',
            'put-parameter',
            '--name',
            path,
            '--type',
            kind,
            '--value',
            f'file://{tmp_path}',
            '--overwrite',
            '--region',
            'us-east-1',
        ]
        if kind == 'SecureString':
            cmd.extend(['--key-id', kms_alias])
        if profile:
            cmd.extend(['--profile', str(profile)])

        print(
            _c(CYAN, f'$ aws ssm put-parameter --name {path} --type {kind} ...')
        )

        result = subprocess.run(cmd, check=False)  # noqa: S603
        if result.returncode == 0:
            print(_c(GREEN, f'OK  {path} guardado en SSM'))
        return result.returncode
    finally:
        import contextlib

        with contextlib.suppress(OSError):
            os.unlink(tmp_path)


def _print_catalog_inventory() -> None:
    """Lista los secretos del catalogo (sin valores)."""
    from serverless.secrets_catalog import Catalog
    from serverless.secrets_catalog import CatalogError

    try:
        catalog = Catalog.load()
    except CatalogError as exc:
        _err(f'No se puede cargar el catalogo: {exc}')
        return

    print(f'{YELLOW}Catalogo (serverless/lambda/resources/secrets/):{NC}')
    for spec in sorted(catalog.by_name.values(), key=lambda s: s.name):
        kind = spec.ssm_type
        desc = spec.description
        stages = sorted(spec.stages)
        print(
            f'  {_c(CYAN, spec.name):<35} '
            f'{_c(DIM, "[" + kind + "]"):<25} '
            f'stages={stages}  {desc}',
        )


def cmd_validate_catalog(flags: dict[str, Any]) -> int:
    """Valida que el catalogo cargue sin errores."""
    from serverless.secrets_catalog import Catalog
    from serverless.secrets_catalog import CatalogError

    try:
        catalog = Catalog.load()
    except CatalogError as exc:
        _err(f'Catalogo invalido: {exc}')
        return 1

    print(_c(GREEN, f'OK  {len(catalog)} secretos validos'))
    _print_catalog_inventory()
    return 0


def cmd_sync_secrets(flags: dict[str, Any]) -> int:
    """Sincroniza el catalogo del stage desde el .env a SSM."""
    from serverless.secrets_catalog import Catalog
    from serverless.secrets_catalog import CatalogError
    from serverless.secrets_sync import SyncAction
    from serverless.secrets_sync import SyncError
    from serverless.secrets_sync import sync_secrets_to_ssm

    stage = flags.get('stage')
    if not stage:
        _err('--stage=<env> requerido (dev | stage | prod)')
        return 2

    env_file = _SERVER_ENV_DIR / f'.{stage}'
    example_file = _SERVER_ENV_DIR / '.example'
    only_raw = flags.get('only')
    only: tuple[str, ...] | None = None
    if only_raw:
        only = tuple(s.strip() for s in str(only_raw).split(',') if s.strip())

    try:
        # `example_file` habilita el fallback a `os.environ` cuando el
        # `.env` local no existe (modo CI). En local con `.env` presente
        # se usa el archivo y `os.environ` se ignora.
        results = sync_secrets_to_ssm(
            stage=str(stage),
            env_file=env_file,
            catalog=Catalog.load(),
            example_file=example_file,
            profile=flags.get('aws_profile'),
            only=only,
            dry_run=bool(flags.get('dry_run')),
        )
    except (CatalogError, SyncError) as exc:
        _err(str(exc))
        return 1

    push = sum(1 for r in results if r.action == SyncAction.PUSH)
    skip = sum(1 for r in results if r.action == SyncAction.SKIP)
    miss = sum(1 for r in results if r.action == SyncAction.MISSING)

    print(_c(CYAN, f'[secrets-sync] catalogo: {len(results)} entradas'))
    for r in results:
        marker = (
            GREEN
            if r.action == SyncAction.SKIP
            else YELLOW
            if r.action == SyncAction.PUSH
            else CYAN
        )
        print(
            f'  {_c(marker, r.action.value):<6} {r.name:<25} '
            f'{r.path:<45} hash={r.hash_short}',
        )
    print(_c(GREEN, f'-> {push} PUSH, {skip} SKIP, {miss} MISSING'))
    return 0


def _evaluate_status_row(
    spec: Any,
    stage: str,
    env_values: dict[str, str],
    profile: str | None,
) -> tuple[str, str, str, str, str]:
    """Evalua una fila del status: (env_status, ssm_status, match, hash, source_env)."""
    from serverless.secrets_sync import SyncError
    from serverless.secrets_sync import get_ssm_value_hash
    from serverless.secrets_sync import hash_value

    local_value = env_values.get(spec.source_env_var, '')
    local_hash = hash_value(local_value) if local_value else ''
    local_short = local_hash[:4] if local_hash else '----'
    env_status = 'present' if local_value else 'absent'

    try:
        ssm_hash = get_ssm_value_hash(
            spec.path_for(stage),
            profile=profile,
            region='us-east-1',
        )
        ssm_status = 'present' if ssm_hash is not None else 'absent'
    except SyncError:
        ssm_status = 'error'
        ssm_hash = None

    if local_value and ssm_hash is not None:
        match = 'yes' if local_hash == ssm_hash else 'no'
    else:
        match = '-'

    return env_status, ssm_status, match, local_short, local_value


def cmd_secrets_status(flags: dict[str, Any]) -> int:
    """Status: muestra .env vs SSM por secreto (sin valores)."""
    from serverless.secrets_catalog import Catalog
    from serverless.secrets_catalog import CatalogError
    from serverless.secrets_sync import SyncError
    from serverless.secrets_sync import load_env_with_fallback

    stage = flags.get('stage')
    if not stage:
        _err('--stage=<env> requerido (dev | stage | prod)')
        return 2

    try:
        catalog = Catalog.load()
    except CatalogError as exc:
        _err(str(exc))
        return 1

    env_file = _SERVER_ENV_DIR / f'.{stage}'
    example_file = _SERVER_ENV_DIR / '.example'
    env_values: dict[str, str] = {}
    if env_file.exists() or example_file.exists():
        try:
            env_values = load_env_with_fallback(env_file, example_file)
        except SyncError:
            env_values = {}

    profile_raw = flags.get('aws_profile')
    profile = str(profile_raw) if profile_raw else None
    specs = catalog.for_stage(str(stage))

    print(_c(CYAN, f'Catalogo: {len(specs)} entradas, stage={stage}'))
    print()
    print(
        f'{"Entrada":<27} {"env":<10} {"SSM":<10} {"Match":<7} Hash(local)',
    )
    print('-' * 72)

    counts = {'sync': 0, 'mismatch': 0, 'missing_local': 0, 'missing_ssm': 0}

    for spec in sorted(specs, key=lambda s: s.name):
        env_status, ssm_status, match, local_short, local_value = (
            _evaluate_status_row(spec, str(stage), env_values, profile)
        )
        if match == 'yes':
            counts['sync'] += 1
        elif match == 'no':
            counts['mismatch'] += 1
        elif not local_value:
            counts['missing_local'] += 1
        elif ssm_status == 'absent':
            counts['missing_ssm'] += 1

        print(
            f'{spec.name:<27} {env_status:<10} {ssm_status:<10} '
            f'{match:<7} {local_short}',
        )

    print()
    print(
        _c(
            GREEN,
            f'Resumen: {counts["sync"]} sync, {counts["mismatch"]} mismatch, '
            f'{counts["missing_ssm"]} missing en SSM, '
            f'{counts["missing_local"]} missing en .env',
        ),
    )
    return 0


def cmd_rotate_secret(flags: dict[str, Any]) -> int:
    """Rotar el valor de un SSM Parameter (destructivo).

    Pide el nuevo valor por stdin, actualiza el parameter. La Lambda
    relee tras 5 min (cache Powertools) o tras un redeploy.
    """
    if not flags.get('confirm'):
        _err('--confirm requerido para rotar un secret')
        return 2

    return cmd_setup_ssm(flags)


def cmd_verify_ses_dns(flags: dict[str, Any]) -> int:
    """dig CNAMEs DKIM + TXT SPF/DMARC contra Cloudflare DNS."""
    import shutil

    if shutil.which('dig') is None:
        _err('dig no esta instalado. Instalar: apt install dnsutils')
        return 1

    domain = 'the-full-stack.com'

    print(_c(CYAN, f'Verificando DNS de {domain}...'))
    print()

    checks = [
        ('SPF (TXT)', ['dig', '+short', 'TXT', domain], 'amazonses.com'),
        ('DMARC (TXT)', ['dig', '+short', 'TXT', f'_dmarc.{domain}'], 'DMARC1'),
    ]

    all_ok = True
    for label, cmd, expected in checks:
        result = subprocess.run(  # noqa: S603
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
                f'  {_c(RED, "FAIL")} {label}: '
                f'esperado {expected!r}, got {output!r}',
            )
            all_ok = False

    print()
    if all_ok:
        print(_c(GREEN, 'OK  Records SPF + DMARC correctos'))
        print(
            f'{YELLOW}  Pendiente:{NC} verificar 3 CNAMEs DKIM '
            f'(leer de aws sesv2 get-email-identity)',
        )
    else:
        _err(
            'Faltan records DNS — ver .claude/rules/serverless-secrets.md '
            '(seccion AWS SES) y el skill aws-ses',
        )

    return 0 if all_ok else 1


def cmd_request_ses_prod(flags: dict[str, Any]) -> int:
    """Imprime la plantilla del ticket de production access SES."""
    template = _SERVERLESS_DIR / 'scripts' / 'request_ses_production.md'

    if template.exists():
        print(template.read_text())
        return 0

    print(
        _c(
            YELLOW,
            'Plantilla por defecto (crear scripts/request_ses_production.md):',
        ),
    )
    print()
    print('---')
    print('Mail type: Transactional')
    print('Website URL: https://the-full-stack.com')
    print('Description:')
    print('  Personal portfolio contact form. Visitors fill a form on')
    print('  the-full-stack.com (and 5 niche subdomains).')
    print('---')
    return 0
