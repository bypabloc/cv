"""@module s3_writer — sube el snapshot YAML a S3 via `aws s3 sync`.

Layout del bucket (`serverless/lambda/resources/s3/db-backups.yaml`):
  s3://portfolio-db-backups-<stage>/history/<YYYY-MM-DD>/<carpeta>/<slug>.yaml
  s3://portfolio-db-backups-<stage>/latest/<carpeta>/<slug>.yaml

`history/` acumula snapshots fechados (lifecycle 84 dias); `latest/` se
sincroniza con `--delete` para reflejar EXACTAMENTE el snapshot actual.
El output de `aws s3 sync` (paths de archivos) es seguro: no contiene
secretos.
"""

from pathlib import Path
import subprocess


BUCKET_PREFIX = 'portfolio-db-backups'


def bucket_name(stage: str) -> str:
    """Nombre del bucket de backups del stage."""
    return f'{BUCKET_PREFIX}-{stage}'


def history_uri(stage: str, date_str: str) -> str:
    """URI S3 del snapshot fechado (inmutable, lifecycle 84 dias)."""
    return f's3://{bucket_name(stage)}/history/{date_str}/'


def latest_uri(stage: str) -> str:
    """URI S3 del snapshot vigente (espejo exacto, sync --delete)."""
    return f's3://{bucket_name(stage)}/latest/'


def _aws_cmd(profile: str | None, *extra: str) -> list[str]:
    """Construye un comando `aws` con --profile opcional."""
    cmd = ['aws', *extra]
    if profile:
        cmd.extend(['--profile', profile])
    return cmd


def _sync(
    staging: Path,
    uri: str,
    *,
    profile: str | None,
    region: str,
    delete: bool,
) -> None:
    """Corre `aws s3 sync <staging> <uri>` y falla con el exit code."""
    cmd = _aws_cmd(
        profile,
        's3',
        'sync',
        str(staging),
        uri,
        '--region',
        region,
    )
    if delete:
        cmd.append('--delete')
    result = subprocess.run(cmd, check=False)  # noqa: S603
    if result.returncode != 0:
        msg = f'aws s3 sync fallo hacia {uri} (exit {result.returncode})'
        raise RuntimeError(msg)


def upload_snapshot(
    staging: Path,
    *,
    stage: str,
    date_str: str,
    aws_profile: str | None,
    region: str,
) -> list[str]:
    """Sube el staging a history/<fecha>/ y replica a latest/ (--delete).

    Returns
    -------
    list[str]
        Las 2 URIs S3 escritas (history fechado + latest).
    """
    history = history_uri(stage, date_str)
    latest = latest_uri(stage)
    _sync(staging, history, profile=aws_profile, region=region, delete=False)
    _sync(staging, latest, profile=aws_profile, region=region, delete=True)
    return [history, latest]
