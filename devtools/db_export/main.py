"""@module main — orquestador del export CV: Neon -> YAML -> S3.

Flujo:
1. Resuelve la Neon URL desde SSM (`/portfolio/<stage>/neon-url`) con
   `aws ssm get-parameter --with-decryption` (subprocess). HERMETICO:
   el valor vive solo en memoria del proceso; NUNCA se imprime, y los
   mensajes de error se sanitizan antes de salir por stdout/stderr
   (cumple `.claude/rules/env-files.md`).
2. Conecta a Neon con psycopg v3 en modo READ-ONLY y lee todas las
   entidades CV (`queries.collect_snapshot`).
3. Escribe el snapshot YAML seed-compatible en el staging local
   `tmp/db-export/<stage>/` (+ copia opcional en --out).
4. Sube a S3 (`s3_writer.upload_snapshot`) salvo --dry-run/--no-upload.

Exit codes: 0 ok, 1 error de usuario/entorno (SSM, Neon, S3).
"""

from datetime import UTC
from datetime import datetime
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any
import urllib.parse

import psycopg

from db_export import queries
from db_export import s3_writer
from db_export import serializer
from shared.paths import PROJECT_ROOT


AWS_REGION = 'us-east-1'

_STAGING_BASE = PROJECT_ROOT / 'tmp' / 'db-export'


def _ssm_neon_path(stage: str) -> str:
    """SSM path de la connection string de Neon para el stage."""
    return f'/portfolio/{stage}/neon-url'


def _sanitize(text: str, url: str) -> str:
    """Reemplaza la URL de Neon (y sus componentes) por `***` en `text`.

    Defensa para que un error de psycopg/aws nunca filtre la connection
    string ni sus partes (password, host, user) a stdout/stderr.
    """
    parts = urllib.parse.urlsplit(url)
    secrets = [url, parts.password, parts.hostname, parts.username]
    for secret in secrets:
        if secret:
            text = text.replace(secret, '***')
    return text


def _resolve_neon_url(stage: str, aws_profile: str | None) -> str:
    """Lee la Neon URL de SSM sin imprimirla jamas.

    Mismo estandar hermetico que `serverless/secrets_sync.py`: la
    captura de stdout se parsea en memoria y solo el VALOR se retorna
    al caller; los errores reportan returncode, nunca el contenido.
    """
    cmd = [
        'aws',
        'ssm',
        'get-parameter',
        '--name',
        _ssm_neon_path(stage),
        '--with-decryption',
        '--region',
        AWS_REGION,
    ]
    if aws_profile:
        cmd.extend(['--profile', aws_profile])
    result = subprocess.run(  # noqa: S603
        cmd,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        msg = (
            f'aws ssm get-parameter fallo para {_ssm_neon_path(stage)}: '
            f'returncode={result.returncode}. Verifica credenciales AWS '
            '(--aws-profile / OIDC) y que el parametro exista.'
        )
        raise RuntimeError(msg)
    try:
        return json.loads(result.stdout)['Parameter']['Value']
    except json.JSONDecodeError, KeyError:
        msg = (
            'respuesta inesperada de get-parameter para '
            f'{_ssm_neon_path(stage)}'
        )
        raise RuntimeError(msg) from None


def _write_snapshot(snapshot: dict[str, Any], staging: Path) -> dict[str, int]:
    """Escribe el snapshot al staging local. Devuelve conteos por carpeta.

    El staging se RECREA desde cero (rmtree + mkdir) para que el sync a
    `latest/` refleje exactamente este snapshot, sin archivos viejos.
    """
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)

    counts: dict[str, int] = {}
    profile = snapshot['profile']
    if profile is not None:
        path = staging / 'profile.yaml'
        path.write_text(serializer.dump_yaml(profile), encoding='utf-8')
        counts['profile'] = 1
    else:
        counts['profile'] = 0

    for folder, entries in snapshot['entities'].items():
        folder_dir = staging / folder
        if entries:
            folder_dir.mkdir()
        for slug, data in entries:
            path = folder_dir / f'{slug}.yaml'
            path.write_text(serializer.dump_yaml(data), encoding='utf-8')
        counts[folder] = len(entries)
    return counts


def _print_summary(counts: dict[str, int], staging: Path) -> None:
    """Imprime el resumen de archivos exportados por entidad."""
    total = sum(counts.values())
    print(f'[db_export] Snapshot escrito en {staging} ({total} archivos):')
    for folder, count in counts.items():
        print(f'  {folder:<14} {count}')


def _export(conn: psycopg.Connection, staging: Path) -> dict[str, int]:
    """Lee el snapshot (read-only) y lo escribe al staging."""
    conn.read_only = True
    snapshot = queries.collect_snapshot(conn)
    return _write_snapshot(snapshot, staging)


def main(flags: dict[str, Any]) -> int:
    """Entry point de db_export (flags ya validadas por flags.py)."""
    stage: str = flags['stage']
    aws_profile: str | None = flags['aws_profile']
    staging = _STAGING_BASE / stage

    try:
        url = _resolve_neon_url(stage, aws_profile)
    except RuntimeError as exc:
        print(f'[db_export] {exc}', file=sys.stderr)
        return 1

    try:
        with psycopg.connect(url, connect_timeout=30) as conn:
            counts = _export(conn, staging)
    except psycopg.Error as exc:
        message = _sanitize(str(exc), url)
        print(
            f'[db_export] Error de Neon (stage={stage}): {message}',
            file=sys.stderr,
        )
        return 1

    _print_summary(counts, staging)

    if flags['out']:
        out_dir = Path(flags['out'])
        shutil.copytree(staging, out_dir, dirs_exist_ok=True)
        print(f'[db_export] Copia local extra en {out_dir}')

    date_str = datetime.now(UTC).strftime('%Y-%m-%d')
    if flags['dry_run']:
        print('[db_export] DRY-RUN: no se sube a S3. Destinos previstos:')
        print(f'  {s3_writer.history_uri(stage, date_str)}')
        print(f'  {s3_writer.latest_uri(stage)} (con --delete)')
        return 0
    if flags['no_upload']:
        print('[db_export] --no-upload: snapshot solo local.')
        return 0

    try:
        uris = s3_writer.upload_snapshot(
            staging,
            stage=stage,
            date_str=date_str,
            aws_profile=aws_profile,
            region=AWS_REGION,
        )
    except RuntimeError as exc:
        print(f'[db_export] {exc}', file=sys.stderr)
        return 1

    print('[db_export] Snapshot subido a:')
    for uri in uris:
        print(f'  {uri}')
    return 0
