"""Tests de validacion de flags de api_e2e (logica pura, sin red).

El conftest de devtools (devtools/tests/conftest.py) agrega devtools/ al
sys.path, asi que `api_e2e` resuelve como paquete.
"""

import pytest

from api_e2e.flags import flag


def test_flag_when_no_args_then_applies_defaults() -> None:
    """
    Given flags vacias,
    When flag(),
    Then aplica los defaults (env=dev, samples=5, sin lambda).
    """
    result = flag({})

    assert result['env'] == 'dev'
    assert result['samples'] == 5
    assert result['lambda'] is None
    assert result['keep_data'] is False


def test_flag_when_env_prod_then_raises() -> None:
    """
    Given --env=prod,
    When flag(),
    Then lanza ValueError (api_e2e NUNCA corre contra prod).
    """
    with pytest.raises(ValueError, match='NUNCA prod'):
        flag({'env': 'prod'})


def test_flag_when_env_stage_then_accepted() -> None:
    """
    Given --env=stage,
    When flag(),
    Then se acepta (stage es valido).
    """
    result = flag({'env': 'stage'})

    assert result['env'] == 'stage'


def test_flag_when_lambda_invalid_then_raises() -> None:
    """
    Given --lambda=nope,
    When flag(),
    Then lanza ValueError con los lambdas validos.
    """
    with pytest.raises(ValueError, match='lambda invalido'):
        flag({'lambda': 'nope'})


def test_flag_when_lambda_valid_then_accepted() -> None:
    """
    Given --lambda=users,
    When flag(),
    Then se acepta.
    """
    result = flag({'lambda': 'users'})

    assert result['lambda'] == 'users'


def test_flag_when_samples_string_then_coerced_to_int() -> None:
    """
    Given --samples='3' (string del CLI),
    When flag(),
    Then se convierte a int 3.
    """
    result = flag({'samples': '3'})

    assert result['samples'] == 3


def test_flag_when_samples_zero_then_raises() -> None:
    """
    Given --samples=0,
    When flag(),
    Then lanza ValueError (debe ser >= 1).
    """
    with pytest.raises(ValueError, match='>= 1'):
        flag({'samples': '0'})


def test_flag_when_samples_not_int_then_raises() -> None:
    """
    Given --samples='abc',
    When flag(),
    Then lanza ValueError (no es entero).
    """
    with pytest.raises(ValueError, match='entero'):
        flag({'samples': 'abc'})
