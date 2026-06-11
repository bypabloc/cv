"""publish.dispatch en stage prod usa ref 'main'.

Given el stage del Lambda es prod,
When se invoca publish_service.dispatch,
Then el workflow se dispara con ref='main' e inputs={'env': 'main'}.
"""

from unittest.mock import MagicMock


def test_publish_dispatch_prod_ref_main(monkeypatch):
    from services import publish_service

    monkeypatch.setattr(
        publish_service.app_config, 'environment', 'prod',
    )
    monkeypatch.setattr(
        publish_service,
        'get_secret_by_name',
        lambda *_a, **_k: 'fake-pat',
    )
    dispatch_mock = MagicMock()
    monkeypatch.setattr(publish_service, 'dispatch_workflow', dispatch_mock)

    result = publish_service.dispatch()

    assert result['ref'] == 'main'
    dispatch_mock.assert_called_once_with(
        'fake-pat', 'bypabloc/cv', 'deploy-apps.yml', 'main',
        {'env': 'main'},
    )
