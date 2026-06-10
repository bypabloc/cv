"""Unit tests de db_export.flags.

Path mirroring: devtools/db_export/flags.py -> este archivo.
"""

import pytest

from db_export.flags import describe
from db_export.flags import flag


pytestmark = pytest.mark.unit


def test_flag_when_stage_missing_then_raises():
    """
    Given un flags_dict sin --stage,
    When flag,
    Then raises ValueError indicando que --stage es obligatorio.
    """
    with pytest.raises(ValueError, match='Falta --stage'):
        flag({})


def test_flag_when_stage_invalid_then_raises():
    """
    Given --stage=qa (no esta en dev|prod),
    When flag,
    Then raises ValueError con el valor invalido y los validos.
    """
    with pytest.raises(ValueError, match="--stage invalido: 'qa'"):
        flag({'stage': 'qa'})


def test_flag_when_stage_local_then_raises():
    """
    Given --stage=local (el export solo aplica a stages desplegados),
    When flag,
    Then raises ValueError.
    """
    with pytest.raises(ValueError, match="--stage invalido: 'local'"):
        flag({'stage': 'local'})


def test_flag_when_stage_dev_then_defaults_applied():
    """
    Given --stage=dev sin mas flags,
    When flag,
    Then devuelve defaults exactos (sin profile, sin dry-run, sin out).
    """
    result = flag({'stage': 'dev'})

    assert result == {
        'stage': 'dev',
        'aws_profile': None,
        'dry_run': False,
        'out': None,
        'no_upload': False,
        'verbose': False,
    }


def test_flag_when_all_flags_set_then_preserved():
    """
    Given --stage=prod --aws-profile=tfs-dev --dry-run --out=tmp/x
      --no-upload,
    When flag,
    Then cada valor se preserva exacto en el dict normalizado.
    """
    result = flag(
        {
            'stage': 'prod',
            'aws_profile': 'tfs-dev',
            'dry_run': True,
            'out': 'tmp/x',
            'no_upload': True,
        }
    )

    assert result == {
        'stage': 'prod',
        'aws_profile': 'tfs-dev',
        'dry_run': True,
        'out': 'tmp/x',
        'no_upload': True,
        'verbose': False,
    }


def test_flag_when_unknown_flag_then_raises():
    """
    Given una flag desconocida (--bucket),
    When flag,
    Then raises ValueError 'Flags no permitidas'.
    """
    with pytest.raises(ValueError, match='Flags no permitidas: bucket'):
        flag({'stage': 'dev', 'bucket': 'x'})


def test_flag_when_out_is_bool_then_raises():
    """
    Given --out sin valor (parseado como bool True),
    When flag,
    Then raises ValueError pidiendo un path.
    """
    with pytest.raises(ValueError, match='--out requiere un path'):
        flag({'stage': 'dev', 'out': True})


def test_describe_returns_monocommand_with_stage_required():
    """
    Given el describe() del script,
    When se consulta,
    Then es monocommand y --stage es la unica flag required.
    """
    payload = describe()

    assert payload['name'] == 'db_export'
    assert payload['kind'] == 'monocommand'
    assert payload['commands'] == []
    required = [
        name for name, spec in payload['flags'].items() if spec['required']
    ]
    assert required == ['stage']
