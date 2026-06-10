"""Resolucion de la fuente del snapshot (seed_service._resolve_data_dir).

Given un source local, un source s3:// y la ausencia de source,
When se resuelve la fuente,
Then el path local se devuelve tal cual, el s3:// dispara la descarga, y
sin source ni S3_DB_BACKUPS_BUCKET se falla con un error explicito;
con la env var presente el default es s3://<bucket>/latest/.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


def test_seed_resolve_data_dir_sources(monkeypatch, tmp_path):
    from services import seed_service
    from services.seed_service import _resolve_data_dir

    # Local path: se devuelve tal cual.
    assert _resolve_data_dir(str(tmp_path)) == Path(str(tmp_path))

    # s3://: delega en la descarga del snapshot.
    with patch.object(
        seed_service, '_download_snapshot', return_value=tmp_path
    ) as download_mock:
        assert _resolve_data_dir('s3://bucket-x/latest/') == tmp_path
    assert download_mock.call_args[0][0] == 's3://bucket-x/latest/'

    # Sin source ni env var: error explicito.
    monkeypatch.delenv('S3_DB_BACKUPS_BUCKET', raising=False)
    with pytest.raises(ValueError, match='S3_DB_BACKUPS_BUCKET'):
        _resolve_data_dir(None)

    # Con env var: el default es latest/ del bucket del stage.
    monkeypatch.setenv('S3_DB_BACKUPS_BUCKET', 'portfolio-db-backups-dev')
    with patch.object(
        seed_service, '_download_snapshot', return_value=tmp_path
    ) as download_mock:
        assert _resolve_data_dir(None) == tmp_path
    assert (
        download_mock.call_args[0][0]
        == 's3://portfolio-db-backups-dev/latest/'
    )
