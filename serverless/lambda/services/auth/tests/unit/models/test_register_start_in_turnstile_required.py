"""RegisterStartIn: cf_turnstile_response es opcional a nivel Pydantic.

Given un payload sin cf_turnstile_response,
When se valida con RegisterStartIn,
Then NO falla — el campo default a '' (cadena vacia).

El '' habilita el bypass de Turnstile para tests E2E (dev/local). La
exigencia del token NO es a nivel Pydantic sino del controller
register.start, que con cf_response vacio + sin bypass valido lanza
TurnstileError 403 (AC-12, cubierto por
test_register_start_turnstile_invalid_403). Mismo contrato que
contact_form (cf_token default='').
"""

import pytest


pytestmark = pytest.mark.unit


def test_register_start_in_turnstile_defaults_empty():
    from models.register import RegisterStartIn

    model = RegisterStartIn(email='valid@example.com')

    assert model.cf_turnstile_response == ''
