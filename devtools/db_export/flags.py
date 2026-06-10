"""Validacion de flags del script db_export (mono-comando).

Uso:
  python devtools/run.py db_export --stage=dev [--aws-profile=tfs-dev]
                                   [--dry-run] [--out=tmp/db-export-copy]
                                   [--no-upload]

Flags:
- --stage        (OBLIGATORIO) dev | prod. Resuelve el SSM path de la
                 Neon URL y el bucket S3 destino.
- --aws-profile  perfil AWS CLI para SSM + S3 (default: el del shell).
- --dry-run      exporta a staging local y LISTA lo que subiria, sin
                 tocar S3 (si conecta a Neon, read-only).
- --out          directorio extra donde dejar una copia local del
                 snapshot (debug).
- --no-upload    exporta solo local (staging + --out), sin subir a S3.
"""

from typing import Any

from utils.describe import ScriptDescribe
from utils.flags_to_dict import set_default_values
from utils.flags_to_dict import validate_allowed_flags


VALID_STAGES = ('dev', 'prod')

ALLOWED_FLAGS = [
    'stage',
    'aws_profile',
    'dry_run',
    'out',
    'no_upload',
    'help',
    'verbose',
]

_DEFAULTS: dict[str, Any] = {
    'aws_profile': None,
    'dry_run': False,
    'out': None,
    'no_upload': False,
    'verbose': False,
}


def flag(flags_dict: dict[str, Any]) -> dict[str, Any]:
    """Valida y normaliza las flags de db_export."""
    validate_allowed_flags(flags_dict, ALLOWED_FLAGS)

    stage = flags_dict.get('stage')
    if not stage:
        msg = (
            'Falta --stage (obligatorio). Valores validos: '
            f'{", ".join(VALID_STAGES)}.\n'
            'Ejemplo: python devtools/run.py db_export --stage=dev '
            '--aws-profile=tfs-dev'
        )
        raise ValueError(msg)
    if stage not in VALID_STAGES:
        msg = (
            f'--stage invalido: {stage!r}. Validos: {", ".join(VALID_STAGES)}.'
        )
        raise ValueError(msg)

    flags_dict = set_default_values(flags_dict, _DEFAULTS)

    out = flags_dict.get('out')
    if out is not None and not isinstance(out, str):
        msg = '--out requiere un path (ej. --out=tmp/db-export-copy).'
        raise ValueError(msg)

    return flags_dict


def describe() -> ScriptDescribe:
    """Inventario machine-readable de las flags de db_export."""
    return {
        'name': 'db_export',
        'kind': 'monocommand',
        'summary': (
            'Exporta la data CV de Neon a YAML seed-compatible y la sube '
            'a s3://portfolio-db-backups-<stage>/ (history/<fecha>/ + '
            'latest/). Hermetico: la Neon URL (SSM) nunca se imprime.'
        ),
        'commands': [],
        'flags': {
            'stage': {
                'type': 'string',
                'summary': 'Stage a exportar: dev | prod (OBLIGATORIO)',
                'required': True,
            },
            'aws_profile': {
                'type': 'string',
                'summary': (
                    'Perfil AWS CLI para SSM + S3 (default: el del shell)'
                ),
                'required': False,
            },
            'dry_run': {
                'type': 'bool',
                'summary': (
                    'Exporta local y lista lo que subiria, sin tocar S3'
                ),
                'required': False,
            },
            'out': {
                'type': 'string',
                'summary': 'Directorio extra para copia local del snapshot',
                'required': False,
            },
            'no_upload': {
                'type': 'bool',
                'summary': 'Solo export local (staging + --out), sin S3',
                'required': False,
            },
        },
    }
