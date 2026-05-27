"""Sync de secretos: lee docker/env/server/.{stage} y publica a SSM.

Modulo HERMETICO. El valor del secreto NUNCA aparece en stdout, stderr,
logs, exception traceback ni `ps aux`.

Reglas:

- El `.env` se carga con `dotenv_values` (PyPI `python-dotenv`) o, como
  fallback minimo, un parser custom (sin imprimir).
- En CI (sin `.env` local) el valor de cada key se resuelve desde
  `os.environ`, usando `docker/env/server/.example` como schema canonico
  de keys validas. GitHub Actions inyecta cada key como Environment Secret.
- `aws ssm put-parameter` recibe el valor por tempfile (`--value file://`).
  Tempfile con perms `0600`, borrado en `finally`. NUNCA por argumento
  (visible en `ps`) ni stdin (inflexible bajo `subprocess`).
- `aws ssm get-parameter` captura stdout, calcula SHA256, y descarta el
  valor inmediato. Solo el hash queda en memoria.
- Comparacion por hash: si el local == SSM -> SKIP (idempotencia).
- Exception messages NUNCA contienen el valor.
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass
from enum import StrEnum
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from serverless.secrets_catalog import Catalog
    from serverless.secrets_catalog import SecretSpec


class SyncError(RuntimeError):
    """Error sincronizando un secreto. NUNCA contiene el valor."""


class SyncAction(StrEnum):
    """Accion que el sync ejecuto para un secreto."""

    SKIP = 'SKIP'  # SSM ya tiene el valor (hash match)
    PUSH = 'PUSH'  # publicar a SSM (crear o actualizar)
    MISSING = 'MISSING'  # ausente en .env, no required -> skip silencioso
    ERROR = 'ERROR'  # fallo, ver mensaje


@dataclass(frozen=True)
class SyncResult:
    """Resultado para un secreto puntual."""

    name: str
    path: str
    action: SyncAction
    hash_short: str  # primeros 4 chars del SHA256 (para diff visual)
    detail: str = ''  # mensaje corto, NUNCA contiene el valor


def hash_value(value: str) -> str:
    """SHA256 hex completo del valor. Solo para comparar."""
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def hash_short(value: str) -> str:
    """Primeros 4 chars del SHA256 (entropia 16 bits, no recupera valor)."""
    return hash_value(value)[:4]


def load_env_file(env_file: Path) -> dict[str, str]:
    """Carga un .env en memoria sin imprimir su contenido.

    Usa `python-dotenv` si esta disponible; sino parser minimo.
    """
    if not env_file.exists():
        raise SyncError(f'.env no existe: {env_file}')

    try:
        from dotenv import dotenv_values

        loaded = dotenv_values(env_file)
        return {k: v for k, v in loaded.items() if v is not None}
    except ImportError:
        # Fallback minimo: parser KEY=value, sin substitution.
        result: dict[str, str] = {}
        for line in env_file.read_text(encoding='utf-8').splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
            if '=' not in stripped:
                continue
            key, _, value = stripped.partition('=')
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key:
                result[key] = value
        return result


def load_example_keys(example_file: Path) -> tuple[str, ...]:
    """Devuelve las KEY declaradas en `.example`, en orden de aparicion.

    El `.example` es el SCHEMA canonico: enumera todas las keys que el
    backend serverless reconoce, con o sin valor por defecto. Esta
    funcion solo extrae los NOMBRES (no los valores). El parsing acepta
    keys con digitos (ej. `AWS_S3_REGION_NAME`).
    """
    if not example_file.exists():
        raise SyncError(f'.example no existe: {example_file}')

    keys: list[str] = []
    seen: set[str] = set()
    for line in example_file.read_text(encoding='utf-8').splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        if '=' not in stripped:
            continue
        key, _, _value = stripped.partition('=')
        key = key.strip()
        # Validar identificador: empieza con letra/underscore, resto
        # alfanumerico o underscore (acepta digitos: AWS_S3_REGION_NAME).
        if not key or not (key[0].isalpha() or key[0] == '_'):
            continue
        if not all(c.isalnum() or c == '_' for c in key):
            continue
        if key in seen:
            continue
        seen.add(key)
        keys.append(key)
    return tuple(keys)


def load_env_with_fallback(
    env_file: Path,
    example_file: Path,
) -> dict[str, str]:
    """Carga env vars con prioridad `.env` archivo -> `os.environ` schema.

    - Si `env_file` existe: devuelve `load_env_file(env_file)`.
    - Si NO existe: devuelve `{key: os.environ[key]}` para cada `key` del
      `.example`. Las keys ausentes en `os.environ` se omiten (no se
      defaultean a ''); el caller (`sync_secrets_to_ssm`) decide si la
      ausencia es fatal segun `spec.required`.

    Esto soporta dos modos:
    - Local del dev: lee `docker/env/server/.{stage}` (con valores reales).
    - CI: GitHub Actions inyecta cada key como Environment Secret a
      `os.environ` y este modulo las resuelve usando `.example` como
      schema canonico.
    """
    if env_file.exists():
        return load_env_file(env_file)

    keys = load_example_keys(example_file)
    return {key: os.environ[key] for key in keys if key in os.environ}


def _aws_cmd(profile: str | None, *extra: str) -> list[str]:
    """Construye un comando `aws` con --profile opcional."""
    cmd = ['aws', *extra]
    if profile:
        cmd.extend(['--profile', profile])
    return cmd


def get_ssm_value_hash(
    name: str,
    *,
    profile: str | None,
    region: str,
) -> str | None:
    """Lee SSM y devuelve SOLO el hash del valor. None si no existe.

    El valor raw nunca sale de esta funcion. La captura de stdout se
    descarta inmediatamente despues de calcular el hash.
    """
    cmd = _aws_cmd(
        profile,
        'ssm',
        'get-parameter',
        '--name',
        name,
        '--with-decryption',
        '--region',
        region,
    )
    result = subprocess.run(  # noqa: S603
        cmd,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        if 'ParameterNotFound' in result.stderr:
            return None
        raise SyncError(
            f'aws ssm get-parameter fallo para {name}: '
            f'returncode={result.returncode}',
        )
    try:
        data = json.loads(result.stdout)
        value = data['Parameter']['Value']
    except (json.JSONDecodeError, KeyError):
        raise SyncError(
            f'respuesta inesperada de get-parameter para {name}',
        ) from None
    return hash_value(value)


def put_ssm_value(
    spec: SecretSpec,
    stage: str,
    value: str,
    *,
    profile: str | None,
    region: str,
) -> None:
    """Publica un secreto a SSM via tempfile (no visible en ps).

    El valor pasa del `.env` a un archivo temporal con perms 0600,
    y aws-cli lo lee con `--value file://...`. Cleanup en finally.
    """
    path = spec.path_for(stage)
    tmp_fd, tmp_path = tempfile.mkstemp(
        prefix='portfolio-ssm-',
        suffix='.tmp',
        dir='/tmp',
    )
    try:
        os.chmod(tmp_path, 0o600)
        with os.fdopen(tmp_fd, 'w', encoding='utf-8') as f:
            f.write(value)
        cmd = _aws_cmd(
            profile,
            'ssm',
            'put-parameter',
            '--name',
            path,
            '--type',
            spec.ssm_type,
            '--value',
            f'file://{tmp_path}',
            '--overwrite',
            '--region',
            region,
        )
        if spec.ssm_type == 'SecureString':
            cmd.extend(
                ['--key-id', spec.kms_key_alias or 'alias/portfolio-lambdas']
            )
        result = subprocess.run(  # noqa: S603
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            # NUNCA loggear result.stdout o result.stderr crudos si el
            # aws cli echara back el value (raro pero defensive).
            raise SyncError(
                f'aws ssm put-parameter fallo para {path}: '
                f'returncode={result.returncode}',
            )
    finally:
        with contextlib.suppress(OSError):
            os.unlink(tmp_path)


def _eval_one(
    spec: SecretSpec,
    stage: str,
    env_values: dict[str, str],
    *,
    profile: str | None,
    region: str,
    dry_run: bool,
    env_source: str,
) -> SyncResult:
    """Evalua y sincroniza un secreto."""
    path = spec.path_for(stage)
    local_value = env_values.get(spec.source_env_var, '')
    if not local_value:
        if spec.required:
            raise SyncError(
                f'{spec.source_env_var} ausente o vacio en {env_source} '
                f'(requerido por secreto {spec.name!r})',
            )
        return SyncResult(
            name=spec.name,
            path=path,
            action=SyncAction.MISSING,
            hash_short='----',
            detail=f'{spec.source_env_var} ausente, no required',
        )

    local_hash = hash_value(local_value)
    short = local_hash[:4]

    ssm_hash = get_ssm_value_hash(path, profile=profile, region=region)
    if ssm_hash == local_hash:
        return SyncResult(
            name=spec.name,
            path=path,
            action=SyncAction.SKIP,
            hash_short=short,
        )
    if dry_run:
        return SyncResult(
            name=spec.name,
            path=path,
            action=SyncAction.PUSH,
            hash_short=short,
            detail='(dry-run)',
        )
    put_ssm_value(spec, stage, local_value, profile=profile, region=region)
    return SyncResult(
        name=spec.name,
        path=path,
        action=SyncAction.PUSH,
        hash_short=short,
    )


def sync_secrets_to_ssm(
    *,
    stage: str,
    env_file: Path,
    catalog: Catalog,
    example_file: Path | None = None,
    profile: str | None = None,
    region: str = 'us-east-1',
    only: tuple[str, ...] | None = None,
    dry_run: bool = False,
) -> list[SyncResult]:
    """Sincroniza los secretos del catalogo del stage desde el .env a SSM.

    Devuelve la lista de resultados (un SyncResult por secreto considerado).
    Levanta SyncError si un required falta en el .env.

    Resolucion de valores:
    - Si `env_file` existe, se carga ese archivo (modo dev local).
    - Si NO existe y se paso `example_file`, las keys del `.example` se
      resuelven desde `os.environ` (modo CI con Environment Secrets).
    - Si NO existe y NO se paso `example_file`, se levanta SyncError.

    Hermetico: ningun valor real aparece en stdout/stderr/logs/exception
    messages.
    """
    if stage == 'local':
        raise SyncError(
            'stage `local` no se sincroniza a SSM (modo offline-dev). '
            'Las env vars del .local se inyectan al runtime del lambda directo.',
        )

    if example_file is not None:
        env_values = load_env_with_fallback(env_file, example_file)
        env_source = (
            f'docker/env/server/.{stage}'
            if env_file.exists()
            else 'os.environ (CI: GitHub Environment Secrets)'
        )
    else:
        env_values = load_env_file(env_file)
        env_source = f'docker/env/server/.{stage}'
    specs = catalog.for_stage(stage)
    if only:
        only_set = set(only)
        specs = tuple(s for s in specs if s.name in only_set)

    results: list[SyncResult] = []
    for spec in specs:
        result = _eval_one(
            spec,
            stage,
            env_values,
            profile=profile,
            region=region,
            dry_run=dry_run,
            env_source=env_source,
        )
        results.append(result)
    return results
