"""Integration — command 'seed' (restore) end-to-end.

Given un evento crudo {command: 'seed'} SIN confirm_overwrite contra una
DB con datos, When se invoca lambda_handler real, Then el guard aborta
con SEED_REQUIRES_CONFIRM (la DB editada via cv_admin es la fuente de
verdad).

Given el mismo evento con args {confirm_overwrite: true} y
S3_DB_BACKUPS_BUCKET apuntando al bucket del stage, When se invoca,
Then baja el snapshot latest/ de S3, lo upsertea y devuelve
{status: 'ok', seeded: True} con los invariantes del CV (1 profile,
5 niches) en los conteos.

Requiere: DATABASE_URL (schema migrado, con datos), credenciales AWS con
lectura del bucket y S3_DB_BACKUPS_BUCKET en el entorno.
"""

import pytest

from tests.integration._fixtures._invocation import (
    invoke_event,
    lambda_context,
)

pytestmark = pytest.mark.integration


def test_seed_command_e2e():
    import handler

    # Act 1: sin confirm sobre una DB poblada -> guard.
    blocked = handler.lambda_handler(invoke_event('seed'), lambda_context())

    # Assert 1
    assert blocked['status'] == 'error'
    assert blocked['error_code'] == 'SEED_REQUIRES_CONFIRM'

    # Act 2: restore real desde el snapshot latest/ del stage.
    result = handler.lambda_handler(
        invoke_event('seed', args={'confirm_overwrite': True}),
        lambda_context(),
    )

    # Assert 2: invariantes del CV (el contenido editable es volatil; los
    # conteos exactos por entidad viven en el snapshot, no en el test).
    assert result['command'] == 'seed'
    assert result['status'] == 'ok'
    assert result['seeded'] is True
    counts = result['counts']
    assert counts['profile'] == 1
    assert counts['niches'] == 5
