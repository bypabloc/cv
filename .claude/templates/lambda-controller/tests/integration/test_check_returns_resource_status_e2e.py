"""
Test E2E - example/check: invoca lambda_handler end-to-end (sin mocks de
las capas internas) y verifica que devuelve el estado del recurso.

Flujo:
  1. Construir un evento real example/check.
  2. Invocar lambda_handler directamente.
  3. Verificar is_valid True y el status del recurso.

NOTA: este es el escenario mas simple (sin downstream). Para operaciones
que invocan otros Lambdas o tocan recursos AWS, el test debe preparar el
estado real y limpiarlo en el fixture cleanup_resources.

:Authors:
    - <Autor>

:Created:
    - YYYY-MM-DD
"""

from handler import lambda_handler

from tests.integration._fixtures.payloads import build_check_event


def test_check_returns_resource_status_e2e():
    """
    Given un evento real example/check,
    When se invoca lambda_handler end-to-end,
    Then devuelve is_valid True con el status del recurso.
    """
    event = build_check_event(resource_id='INTEGRATION-R-1')

    result = lambda_handler(event, {})

    assert result['is_valid'] is True
    assert result['data']['resource_id'] == 'INTEGRATION-R-1'
    assert result['data']['status'] == 'ok'
