"""Tests de validacion de flags del comando `e2e` (logica pura, sin red).

El conftest de devtools (devtools/tests/conftest.py) agrega devtools/ al
sys.path, asi que `e2e` resuelve como paquete.
"""

from e2e.flags import flag
import pytest


def test_flag_when_no_args_then_applies_defaults() -> None:
    """
    Given flags vacias,
    When flag(),
    Then aplica los defaults (module=None, env=dev, samples=5, sin lambda).
    """
    result = flag({})

    assert result['module'] is None
    assert result['env'] == 'dev'
    assert result['samples'] == 5
    assert result['lambda'] is None
    assert result['keep_data'] is False
    assert result['headed'] is False


def test_flag_when_module_invalid_then_raises_with_valid_modules() -> None:
    """
    Given --module=foo,
    When flag(),
    Then lanza ValueError que lista los modulos validos (api/admin/app).
    """
    with pytest.raises(ValueError, match='api, admin, app') as exc:
        flag({'module': 'foo'})

    assert "--module invalido: 'foo'" in str(exc.value)


def test_flag_when_module_api_then_accepted() -> None:
    """
    Given --module=api,
    When flag(),
    Then se acepta.
    """
    result = flag({'module': 'api'})

    assert result['module'] == 'api'


def test_flag_when_module_admin_then_accepted() -> None:
    """
    Given --module=admin,
    When flag(),
    Then se acepta.
    """
    result = flag({'module': 'admin'})

    assert result['module'] == 'admin'


def test_flag_when_module_app_then_accepted() -> None:
    """
    Given --module=app,
    When flag(),
    Then se acepta.
    """
    result = flag({'module': 'app'})

    assert result['module'] == 'app'


def test_flag_when_env_prod_then_raises() -> None:
    """
    Given --env=prod,
    When flag(),
    Then lanza ValueError (e2e NUNCA corre contra prod).
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
    Given --lambda=auth,
    When flag(),
    Then se acepta.
    """
    result = flag({'lambda': 'auth'})

    assert result['lambda'] == 'auth'


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


def test_flag_when_unknown_flag_then_raises() -> None:
    """
    Given un flag fuera del catalogo permitido,
    When flag(),
    Then lanza ValueError (validate_allowed_flags).
    """
    with pytest.raises(ValueError, match='no permitidas'):
        flag({'nope': True})


def test_flag_when_headed_set_then_preserved() -> None:
    """
    Given --headed,
    When flag(),
    Then queda en True (browser visible local).
    """
    result = flag({'headed': True})

    assert result['headed'] is True
