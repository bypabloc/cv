"""Tests del inventario machine-readable (`describe()`) del comando `e2e`."""

from e2e.flags import describe


def test_describe_when_called_then_returns_monocommand_e2e() -> None:
    """
    Given describe(),
    When se invoca,
    Then el payload identifica al script como `e2e` monocommand.
    """
    result = describe()

    assert result['name'] == 'e2e'
    assert result['kind'] == 'monocommand'
    assert result['commands'] == []


def test_describe_when_called_then_flags_include_core_flags() -> None:
    """
    Given describe(),
    When se inspeccionan los flags,
    Then incluye module/env/samples/lambda (los flags clave del comando).
    """
    flags = describe()['flags']

    assert 'module' in flags
    assert 'env' in flags
    assert 'samples' in flags
    assert 'lambda' in flags


def test_describe_when_module_flag_then_choices_are_the_three_modules() -> None:
    """
    Given describe(),
    When se mira el flag module,
    Then sus choices son exactamente api/admin/app.
    """
    module_flag = describe()['flags']['module']

    assert module_flag['type'] == 'choice'
    assert module_flag['choices'] == ['api', 'admin', 'app']


def test_describe_when_env_flag_then_default_dev_and_no_prod() -> None:
    """
    Given describe(),
    When se mira el flag env,
    Then el default es dev y prod NO esta entre los choices.
    """
    env_flag = describe()['flags']['env']

    assert env_flag['default'] == 'dev'
    assert env_flag['choices'] == ['dev']
    assert 'prod' not in env_flag['choices']


def test_describe_when_lambda_flag_then_choices_are_six_lambdas() -> None:
    """
    Given describe(),
    When se mira el flag lambda,
    Then sus choices son los 6 Lambdas HTTP del modulo api.
    """
    lambda_flag = describe()['flags']['lambda']

    assert lambda_flag['choices'] == [
        'cv',
        'contact_form',
        'tracking_pixel',
        'auth',
        'users',
        'cv_admin',
    ]
