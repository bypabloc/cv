"""Tests del runner de api_e2e: clasificacion de status + body helper."""

from pathlib import Path
import sys


_API_E2E_DIR = Path(__file__).resolve().parents[4] / 'api_e2e'
if str(_API_E2E_DIR) not in sys.path:
    sys.path.insert(0, str(_API_E2E_DIR))

from reporter import Reporter
from runner import Runner
from runner import make_body
from support import Response


def _runner() -> tuple[Runner, Reporter]:
    rep = Reporter()
    return Runner(rep, samples=1), rep


def test_case_when_status_matches_exact_int_then_pass() -> None:
    """
    Given un endpoint que devuelve 200 y expected=200,
    When el runner corre el caso,
    Then lo marca passed=True.
    """
    runner, rep = _runner()
    runner.case(
        lambda_name='cv',
        name='x',
        method='GET',
        call=lambda: Response(200, {}, 0.1),
        expected=200,
    )

    assert rep.results[0].passed is True


def test_case_when_status_in_2xx_range_then_pass() -> None:
    """
    Given un 202 y expected='2xx',
    When el runner corre el caso,
    Then passed=True.
    """
    runner, rep = _runner()
    runner.case(
        lambda_name='cf',
        name='x',
        method='POST',
        call=lambda: Response(202, {}, 0.1),
        expected='2xx',
    )

    assert rep.results[0].passed is True


def test_case_when_status_outside_expected_then_fail() -> None:
    """
    Given un 500 y expected='2xx',
    When el runner corre el caso,
    Then passed=False.
    """
    runner, rep = _runner()
    runner.case(
        lambda_name='cf',
        name='x',
        method='POST',
        call=lambda: Response(500, {}, 0.1),
        expected='2xx',
    )

    assert rep.results[0].passed is False


def test_case_when_status_in_list_then_pass() -> None:
    """
    Given un 204 y expected=[200, 204],
    When el runner corre el caso,
    Then passed=True.
    """
    runner, rep = _runner()
    runner.case(
        lambda_name='auth',
        name='logout',
        method='POST',
        call=lambda: Response(204, {}, 0.1),
        expected=[200, 204],
    )

    assert rep.results[0].passed is True


def test_case_records_all_samples() -> None:
    """
    Given samples=3 con tiempos crecientes,
    When el runner corre el caso,
    Then registra los 3 status codes y el cold == primer sample.
    """
    rep = Reporter()
    runner = Runner(rep, samples=3)
    seq = iter(
        [Response(200, {}, 0.5), Response(200, {}, 0.2), Response(200, {}, 0.3)]
    )
    runner.case(
        lambda_name='cv',
        name='x',
        method='GET',
        call=lambda: next(seq),
        expected=200,
    )

    result = rep.results[0]
    assert result.status_codes == [200, 200, 200]
    assert result.cold == 0.5


def test_make_body_puts_operation_action_at_root() -> None:
    """
    Given operation, action y campos extra,
    When make_body,
    Then el dict tiene operation/action al nivel raiz + los campos FLAT.
    """
    result = make_body('contact', 'create', name='X', email='a@b.com')

    assert result == {
        'operation': 'contact',
        'action': 'create',
        'name': 'X',
        'email': 'a@b.com',
    }
