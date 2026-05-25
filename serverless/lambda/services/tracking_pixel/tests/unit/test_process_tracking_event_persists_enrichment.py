"""Service process_tracking_event — orquesta enrichment + persistencia.

Given un input validado, una IP y un User-Agent de Chrome,
When se invoca process_tracking_event,
Then `ensure_session_and_visit` recibe browser/os/device parseados +
     ip + country (datos del visitante van a sessions/session_visits).

Spec sessions-normalize: el enrichment se pasa al helper, no al ORM
de tracking_events. Los kwargs del helper se capturan via fixture
`session_visit_calls`.
"""

import pytest

from tests.unit._helpers import CHROME_UA, valid_body

pytestmark = pytest.mark.unit


def test_process_tracking_event_persists_enrichment(
    mock_neon_writes: list[dict],
    session_visit_calls: list[dict],
    tracking_aws: None,
) -> None:
    from services.tracking_service import process_tracking_event

    # Act
    process_tracking_event(
        validated_input=valid_body(),
        ip='1.2.3.4',
        user_agent=CHROME_UA,
        country='CL',
    )

    # Assert: una sola escritura tracking_events + una sola invocacion
    # del helper ensure_session_and_visit.
    assert len(mock_neon_writes) == 1
    assert len(session_visit_calls) == 1

    # El enrichment va al HELPER, no al payload de tracking_events.
    helper_args = session_visit_calls[0]
    assert helper_args['browser'] == 'Chrome'
    assert helper_args['os_name'] == 'Linux'
    assert helper_args['device_type'] == 'desktop'
    assert helper_args['ip'] == '1.2.3.4'
    assert helper_args['country'] == 'CL'
    # El helper recibe bump_event_count=True por default del service.
    assert helper_args['bump_event_count'] is True

    # tracking_events ya NO tiene ip/country/browser/os/device_type/utm_*
    payload = mock_neon_writes[0]
    for forbidden in (
        'ip', 'country', 'user_agent', 'browser', 'browser_version',
        'os', 'device_type', 'utm_source', 'utm_medium', 'utm_campaign',
        'utm_content', 'utm_term',
    ):
        assert forbidden not in payload, (
            f'tracking_events no debe persistir {forbidden}: '
            f'movido a sessions/session_visits'
        )
