"""
Given referrers + breakdown utm en el rango,
When se invoca analytics_service.top_referrers (sin cache, via __wrapped__),
Then devuelve {referrers, utm_sources, utm_mediums, utm_campaigns}.
"""

from datetime import date
from unittest.mock import MagicMock

import services.analytics_service as analytics_service


def test_analytics_top_referrers_when_data_then_returns_breakdown(mocker):
    # Arrange: 4 .all() en orden (referrers, utm_sources, utm_mediums,
    # utm_campaigns).
    ref = MagicMock()
    ref.referrer = '(direct)'
    ref.visits = 700
    ref.unique_visitors = 500
    src = MagicMock()
    src.value = 'google'
    src.count = 120
    med = MagicMock()
    med.value = 'cpc'
    med.count = 80
    camp = MagicMock()
    camp.value = 'launch'
    camp.count = 30
    session = MagicMock(name='SQLAlchemySession')
    session.execute.return_value.all.side_effect = [
        [ref],
        [src],
        [med],
        [camp],
    ]
    cm = MagicMock()
    cm.__enter__.return_value = session
    cm.__exit__.return_value = False
    mocker.patch.object(analytics_service, 'db_session', return_value=cm)

    # Act
    result = analytics_service.top_referrers.__wrapped__(
        date_from=date(2026, 4, 27), date_to=date(2026, 5, 28), limit=10
    )

    # Assert
    assert result == {
        'referrers': [
            {
                'referrer': '(direct)',
                'visits': 700,
                'unique_visitors': 500,
            }
        ],
        'utm_sources': [{'value': 'google', 'count': 120}],
        'utm_mediums': [{'value': 'cpc', 'count': 80}],
        'utm_campaigns': [{'value': 'launch', 'count': 30}],
    }
