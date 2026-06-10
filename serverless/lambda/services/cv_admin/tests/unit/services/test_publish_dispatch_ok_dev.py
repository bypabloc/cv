"""publish.dispatch en stage dev dispara el workflow con ref 'dev'.

Given el stage del Lambda es dev y GitHub acepta el dispatch,
When se invoca publish_service.dispatch,
Then llama dispatch_workflow(token, 'bypabloc/cv', 'deploy-apps.yml',
'dev', {'env': 'dev'}) y devuelve dispatched + ref + actions_url.
"""

from unittest.mock import MagicMock


def test_publish_dispatch_ok_dev(monkeypatch):
    from services import publish_service

    monkeypatch.setattr(
        publish_service.app_config, 'environment', 'dev',
    )
    monkeypatch.setattr(
        publish_service,
        'get_secret_by_name',
        lambda *_a, **_k: 'fake-pat',
    )
    dispatch_mock = MagicMock()
    monkeypatch.setattr(publish_service, 'dispatch_workflow', dispatch_mock)

    result = publish_service.dispatch()

    assert result == {
        'dispatched': True,
        'ref': 'dev',
        'actions_url': (
            'https://github.com/bypabloc/cv/actions/workflows/'
            'deploy-apps.yml'
        ),
    }
    dispatch_mock.assert_called_once_with(
        'fake-pat', 'bypabloc/cv', 'deploy-apps.yml', 'dev', {'env': 'dev'},
    )
