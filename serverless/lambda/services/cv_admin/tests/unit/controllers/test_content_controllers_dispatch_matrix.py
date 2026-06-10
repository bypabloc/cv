"""Cada controller de cv_admin delega en SU service fn (matriz 22 actions).

Given guards (auth/admin/rate-limit) mockeados y el service fn mockeado,
When se ejecuta el `run()` de cada uno de los 22 controllers,
Then cada uno devuelve {is_valid: True, code: 0} y llama la funcion del
service correcta con los kwargs esperados (entity/slug/etc).

Un solo escenario ("el dispatch de la matriz completa") parametrizado:
cubre el wiring controller -> service de las 22 actions sin duplicar 22
archivos identicos.
"""

from importlib import import_module
from unittest.mock import MagicMock

import pytest

from ._helpers import (
    _experience_payload,
    _make_admin_user,
    _make_authed_event,
    _project_payload,
)

_PROFILE = {
    'name': 'P',
    'handle': 'bypabloc',
    'headline': {'es': 'h'},
    'summary': {'es': 's'},
    'location': 'Lima',
    'contacts': {
        'email': 'user@example.com',
        'linkedin': 'https://linkedin.com/in/x',
        'github': 'https://github.com/x',
    },
    'avatarUrl': 'https://cdn.example.com/a.avif',
}

_SIMPLES = {
    'education': {
        'slug': 'edu-1',
        'institution': 'I',
        'start': '2017',
        'description': {'es': 'd'},
    },
    'certificate': {
        'slug': 'cert-1',
        'title': 'T',
        'issuer': 'I',
        'date': '2023-04-20',
        'url': 'https://x',
    },
    'award': {
        'slug': 'award-1',
        'title': {'es': 't'},
        'issuer': 'I',
        'date': '2024-01',
        'motivation': {'es': 'm'},
    },
    'language': {
        'slug': 'lang-1',
        'name': {'es': 'n'},
        'level': {'es': 'l'},
    },
    'endorsement': {
        'slug': 'endo-1',
        'name': 'N',
        'role': 'R',
        'relation': {'es': 'r'},
        'linkedin': 'https://linkedin.com/in/x',
    },
    'publication': {
        'slug': 'pub-1',
        'title': 'T',
        'platform': 'X',
        'url': 'https://x',
        'date': '2026-01',
        'summary': {'es': 's'},
    },
}

_SKILL_CAT = {
    'slug': 'cat-1',
    'name': {'es': 'n'},
    'kind': 'technical',
    'skills': ['Python'],
}

# (modulo, clase, data del evento, service_module, service_fn,
#  kwargs esperados que DEBE recibir el service — subset exacto)
_MATRIX = [
    (
        'controllers.content.upsert_profile', 'UpsertProfile', _PROFILE,
        'services.content_service', 'upsert_entity', {'entity': 'profile'},
    ),
    (
        'controllers.content.upsert_experience', 'UpsertExperience',
        _experience_payload(), 'services.content_service', 'upsert_entity',
        {'entity': 'experience'},
    ),
    (
        'controllers.content.upsert_project', 'UpsertProject',
        _project_payload(), 'services.content_service', 'upsert_entity',
        {'entity': 'project'},
    ),
    (
        'controllers.content.upsert_skill_category', 'UpsertSkillCategory',
        _SKILL_CAT, 'services.content_service', 'upsert_entity',
        {'entity': 'skill_category'},
    ),
    (
        'controllers.content.upsert_education', 'UpsertEducation',
        _SIMPLES['education'], 'services.content_service', 'upsert_entity',
        {'entity': 'education'},
    ),
    (
        'controllers.content.upsert_certificate', 'UpsertCertificate',
        _SIMPLES['certificate'], 'services.content_service', 'upsert_entity',
        {'entity': 'certificate'},
    ),
    (
        'controllers.content.upsert_award', 'UpsertAward',
        _SIMPLES['award'], 'services.content_service', 'upsert_entity',
        {'entity': 'award'},
    ),
    (
        'controllers.content.upsert_language', 'UpsertLanguage',
        _SIMPLES['language'], 'services.content_service', 'upsert_entity',
        {'entity': 'language'},
    ),
    (
        'controllers.content.upsert_endorsement', 'UpsertEndorsement',
        _SIMPLES['endorsement'], 'services.content_service', 'upsert_entity',
        {'entity': 'endorsement'},
    ),
    (
        'controllers.content.upsert_publication', 'UpsertPublication',
        _SIMPLES['publication'], 'services.content_service', 'upsert_entity',
        {'entity': 'publication'},
    ),
    (
        'controllers.content.delete_experience', 'DeleteExperience',
        {'slug': 'x-1'}, 'services.content_service', 'delete_entity',
        {'entity': 'experience', 'slug': 'x-1'},
    ),
    (
        'controllers.content.delete_project', 'DeleteProject',
        {'slug': 'x-2'}, 'services.content_service', 'delete_entity',
        {'entity': 'project', 'slug': 'x-2'},
    ),
    (
        'controllers.content.delete_skill_category', 'DeleteSkillCategory',
        {'slug': 'x-3'}, 'services.content_service', 'delete_entity',
        {'entity': 'skill_category', 'slug': 'x-3'},
    ),
    (
        'controllers.content.delete_education', 'DeleteEducation',
        {'slug': 'x-4'}, 'services.content_service', 'delete_entity',
        {'entity': 'education', 'slug': 'x-4'},
    ),
    (
        'controllers.content.delete_certificate', 'DeleteCertificate',
        {'slug': 'x-5'}, 'services.content_service', 'delete_entity',
        {'entity': 'certificate', 'slug': 'x-5'},
    ),
    (
        'controllers.content.delete_award', 'DeleteAward',
        {'slug': 'x-6'}, 'services.content_service', 'delete_entity',
        {'entity': 'award', 'slug': 'x-6'},
    ),
    (
        'controllers.content.delete_language', 'DeleteLanguage',
        {'slug': 'x-7'}, 'services.content_service', 'delete_entity',
        {'entity': 'language', 'slug': 'x-7'},
    ),
    (
        'controllers.content.delete_endorsement', 'DeleteEndorsement',
        {'slug': 'x-8'}, 'services.content_service', 'delete_entity',
        {'entity': 'endorsement', 'slug': 'x-8'},
    ),
    (
        'controllers.content.delete_publication', 'DeletePublication',
        {'slug': 'x-9'}, 'services.content_service', 'delete_entity',
        {'entity': 'publication', 'slug': 'x-9'},
    ),
    (
        'controllers.content.reorder', 'Reorder',
        {
            'entity_type': 'experience',
            'niche': 'generic',
            'ordered_slugs': ['a-1', 'b-2'],
        },
        'services.reorder_service', 'reorder',
        {
            'entity_type': 'experience',
            'niche': 'generic',
            'ordered_slugs': ['a-1', 'b-2'],
        },
    ),
    (
        'controllers.content.catalogs', 'Catalogs', {},
        'services.catalog_service', 'catalogs', {},
    ),
    (
        'controllers.publish.dispatch', 'Dispatch', {},
        'services.publish_service', 'dispatch', {},
    ),
    (
        'controllers.publish.status', 'Status', {},
        'services.publish_service', 'status', {},
    ),
]


@pytest.mark.parametrize(
    ('ctl_module', 'ctl_class', 'data', 'svc_module', 'svc_fn', 'expected'),
    _MATRIX,
    ids=[m[0].rsplit('.', 1)[1] for m in _MATRIX],
)
def test_content_controllers_dispatch_matrix(
    monkeypatch, ctl_module, ctl_class, data, svc_module, svc_fn, expected,
):
    """Cada controller delega en su service fn con los kwargs correctos."""
    from controllers import _base

    monkeypatch.setattr(
        _base, 'require_active_user', lambda *_a, **_k: _make_admin_user(),
    )
    monkeypatch.setattr(
        _base, 'require_admin_user', lambda *_a, **_k: None,
    )
    monkeypatch.setattr(_base, 'RateLimitService', lambda _c: MagicMock())

    service_module = import_module(svc_module)
    service_mock = MagicMock(return_value={'ok': True})
    monkeypatch.setattr(service_module, svc_fn, service_mock)

    controller_cls = getattr(import_module(ctl_module), ctl_class)
    event = _make_authed_event(data=data)

    result = controller_cls(event=event).run()

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['data'] == {'ok': True}
    assert service_mock.call_count == 1
    called_kwargs = service_mock.call_args.kwargs
    for key, value in expected.items():
        assert called_kwargs[key] == value, (
            f'{ctl_class}: kwarg {key!r} esperado {value!r}, '
            f'recibido {called_kwargs.get(key)!r}'
        )
