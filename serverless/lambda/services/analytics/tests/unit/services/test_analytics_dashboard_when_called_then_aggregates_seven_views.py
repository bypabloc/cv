"""
Given las 7 funciones agregadas del service mockeadas,
When se invoca analytics_service.dashboard con rango/bucket/limit,
Then las llama una vez cada una (con los kwargs correctos) y devuelve un
solo dict con las 7 vistas bajo su clave.
"""

from datetime import date

import services.analytics_service as analytics_service


def test_analytics_dashboard_when_called_then_aggregates_seven_views(mocker):
    # Arrange: cada sub-funcion devuelve un marcador identificable.
    overview = mocker.patch.object(
        analytics_service, 'overview', return_value={'k': 'overview'}
    )
    timeseries = mocker.patch.object(
        analytics_service, 'timeseries', return_value={'k': 'timeseries'}
    )
    top_pages = mocker.patch.object(
        analytics_service, 'top_pages', return_value={'k': 'top_pages'}
    )
    top_referrers = mocker.patch.object(
        analytics_service, 'top_referrers', return_value={'k': 'top_referrers'}
    )
    top_niches = mocker.patch.object(
        analytics_service, 'top_niches', return_value={'k': 'top_niches'}
    )
    active_now = mocker.patch.object(
        analytics_service, 'active_now', return_value={'k': 'active_now'}
    )
    retention = mocker.patch.object(
        analytics_service, 'retention', return_value={'k': 'retention'}
    )
    date_from = date(2026, 4, 27)
    date_to = date(2026, 5, 28)

    # Act
    result = analytics_service.dashboard(
        date_from=date_from, date_to=date_to, bucket='week', limit=5
    )

    # Assert: shape combinado
    assert result == {
        'overview': {'k': 'overview'},
        'timeseries': {'k': 'timeseries'},
        'top_pages': {'k': 'top_pages'},
        'top_referrers': {'k': 'top_referrers'},
        'top_niches': {'k': 'top_niches'},
        'active_now': {'k': 'active_now'},
        'retention': {'k': 'retention'},
    }

    # Assert: cada sub-funcion llamada una vez con los kwargs correctos
    overview.assert_called_once_with(date_from=date_from, date_to=date_to)
    timeseries.assert_called_once_with(
        date_from=date_from, date_to=date_to, bucket='week'
    )
    top_pages.assert_called_once_with(
        date_from=date_from, date_to=date_to, limit=5
    )
    top_referrers.assert_called_once_with(
        date_from=date_from, date_to=date_to, limit=5
    )
    top_niches.assert_called_once_with(
        date_from=date_from, date_to=date_to, limit=5
    )
    active_now.assert_called_once_with()
    retention.assert_called_once_with(date_from=date_from, date_to=date_to)
