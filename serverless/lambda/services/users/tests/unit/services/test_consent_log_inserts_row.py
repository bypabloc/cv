"""ConsentService.log — inserta un row de consent log (GDPR).

Given un cambio de marketing_consent,
When se invoca log,
Then delega a insert_consent_log con field/old_value/new_value correctos.
"""

from contextlib import contextmanager
from unittest.mock import MagicMock


@contextmanager
def _ctx(session):
    yield session


def test_consent_log_inserts_row(monkeypatch):
    from services import consent_service

    fake_session = MagicMock()
    calls = {}

    def fake_insert(_session, *, user_id, field, old_value, new_value, ip,
                    user_agent):
        calls['user_id'] = user_id
        calls['field'] = field
        calls['old_value'] = old_value
        calls['new_value'] = new_value

    monkeypatch.setattr(
        consent_service, 'db_session', lambda: _ctx(fake_session),
    )
    monkeypatch.setattr(consent_service, 'insert_consent_log', fake_insert)

    svc = consent_service.ConsentService(app_config=object())
    svc.log(
        user_id='user-1',
        field='marketing_consent',
        old_value='false',
        new_value='true',
    )

    assert calls['user_id'] == 'user-1'
    assert calls['field'] == 'marketing_consent'
    assert calls['old_value'] == 'false'
    assert calls['new_value'] == 'true'
