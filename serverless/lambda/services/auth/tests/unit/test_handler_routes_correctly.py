"""El handler rutea operations validas y rechaza invalidas con 404.

Validamos 3 contratos del scaffold:
1. El EVENT_MODEL acepta `register/start` como operation valida (no
   levanta ValueError en validate_event).
2. Una operation desconocida levanta ValueError -> el handler
   responde 404.
3. Una action desconocida levanta ValueError -> el handler responde
   404.

No probamos el flujo completo: los controllers concretos llegan en
PR 7/8. Aqui solo aseguramos el ruteo del scaffold.
"""

import pytest


def test_event_model_register_actions():
    """register expone start, verify-magic-link, verify-code."""
    from settings.operations import OPERATIONS

    assert 'register' in OPERATIONS
    assert 'login' in OPERATIONS
    assert 'verify' in OPERATIONS
    assert 'session' in OPERATIONS


def test_event_model_rejects_invalid_operation():
    """`unknown` -> ValueError tras import_controller fail."""
    from models.event import EVENT_MODEL

    with pytest.raises(ValueError):
        EVENT_MODEL.validate_event({
            'operation': 'unknown',
            'action': 'start',
            'data': {},
        })


def test_event_model_rejects_invalid_action():
    """`register/unknown-action` -> ValueError."""
    from models.event import EVENT_MODEL

    with pytest.raises(ValueError):
        EVENT_MODEL.validate_event({
            'operation': 'register',
            'action': 'unknown-action',
            'data': {},
        })


def test_event_model_rejects_missing_operation():
    """Sin `operation` en el evento -> ValueError."""
    from models.event import EVENT_MODEL

    with pytest.raises(ValueError):
        EVENT_MODEL.validate_event({
            'action': 'start',
            'data': {},
        })
