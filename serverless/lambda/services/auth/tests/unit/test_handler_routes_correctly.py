"""El handler rutea operations validas y rechaza invalidas con 404.

Validamos 3 contratos:
1. El dict OPERATIONS expone las operations vigentes (sin `register`, que
   fue eliminada: el alta ocurre dentro del flujo `login` unico).
2. Una operation desconocida (incl. `register`) levanta ValueError -> el
   handler responde 404.
3. Una action desconocida levanta ValueError -> el handler responde 404.
"""

import pytest


def test_operations_dict_exposes_vigent_operations():
    """OPERATIONS tiene login/verify/session/mfa/webauthn/security, NO register."""
    from settings.operations import OPERATIONS

    assert 'register' not in OPERATIONS
    assert 'login' in OPERATIONS
    assert 'verify' in OPERATIONS
    assert 'session' in OPERATIONS
    assert 'mfa' in OPERATIONS
    assert 'webauthn' in OPERATIONS
    assert 'security' in OPERATIONS


def test_event_model_rejects_register_operation():
    """`register` ya NO existe -> ValueError (operation desconocida)."""
    from models.event import EVENT_MODEL

    with pytest.raises(ValueError):
        EVENT_MODEL.validate_event(
            {
                'operation': 'register',
                'action': 'start',
                'data': {},
            }
        )


def test_event_model_rejects_invalid_operation():
    """`unknown` -> ValueError tras import_controller fail."""
    from models.event import EVENT_MODEL

    with pytest.raises(ValueError):
        EVENT_MODEL.validate_event(
            {
                'operation': 'unknown',
                'action': 'start',
                'data': {},
            }
        )


def test_event_model_rejects_invalid_action():
    """`login/unknown-action` -> ValueError."""
    from models.event import EVENT_MODEL

    with pytest.raises(ValueError):
        EVENT_MODEL.validate_event(
            {
                'operation': 'login',
                'action': 'unknown-action',
                'data': {},
            }
        )


def test_event_model_rejects_missing_operation():
    """Sin `operation` en el evento -> ValueError."""
    from models.event import EVENT_MODEL

    with pytest.raises(ValueError):
        EVENT_MODEL.validate_event(
            {
                'action': 'start',
                'data': {},
            }
        )
