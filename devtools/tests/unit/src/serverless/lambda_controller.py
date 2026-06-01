"""Unit tests for serverless.lambda_controller - comandos del CLI sin SAM.

Path mirroring: devtools/serverless/lambda_controller.py -> this file.

Cubre cmd_deploy_lambda (dry-run), cmd_destroy (con / sin --yes) y
cmd_status. `provisioner`, `packaging`, `state` e `infra_provision`
estan mockeados: ningun test toca AWS ni empaqueta de verdad.
"""

import contextlib

import pytest


pytestmark = pytest.mark.unit


@contextlib.contextmanager
def _fake_packaged(_root, *, runtime):
    """Reemplaza packaged_lambda: no empaqueta, devuelve un closure vacio."""
    _ = runtime
    yield (_root, set(), [])


def _patch_common(monkeypatch, tmp_path):
    """Mockea las dependencias compartidas de los comandos.

    Devuelve el modulo lambda_controller con `shutil.which`, `resolve`,
    `packaging` y `state` neutralizados.
    """
    from serverless import lambda_controller as lc

    monkeypatch.setattr(lc.shutil, 'which', lambda _name: '/usr/bin/tool')
    monkeypatch.setattr(lc, 'packaged_lambda', _fake_packaged)
    monkeypatch.setattr(lc, 'zip_build_dir', lambda _root: tmp_path / 'b.zip')
    return lc


def _resolved(tmp_path, name='contact_form'):
    """Construye un ResolvedLambda de prueba."""
    from serverless.resolve import ResolvedLambda

    return ResolvedLambda(
        mode='lambda-controller',
        root=tmp_path,
        manifest={
            'name': name,
            'runtime': 'python3.13',
            'handler': 'core.handler.lambda_handler',
            'region': 'us-east-1',
            'trigger': {'type': 'direct'},
        },
    )


class TestCmdDeployDryRun:
    """cmd_deploy_lambda con --dry-run imprime la accion sin tocar AWS."""

    def test_cmd_deploy_dry_run_prints_action(
        self, monkeypatch, tmp_path, capsys
    ):
        """AC-5.2: deploy --dry-run imprime la accion del diff."""
        lc = _patch_common(monkeypatch, tmp_path)
        from serverless.state import Action

        monkeypatch.setattr(
            lc, 'resolve_lambda', lambda _flags: _resolved(tmp_path)
        )
        monkeypatch.setattr(lc.state_mod, 'load_state', lambda _s, _t: None)
        monkeypatch.setattr(lc.state_mod, 'code_hash', lambda _d: 'sha256:k')
        monkeypatch.setattr(lc.state_mod, 'config_hash', lambda _c: 'sha256:c')
        monkeypatch.setattr(
            lc.state_mod, 'diff', lambda _p, _c, _k: Action.CREATE
        )

        def _no_provision(*_a, **_k):
            raise AssertionError('dry-run no debe provisionar')

        monkeypatch.setattr(lc.provisioner, 'provision', _no_provision)

        rc = lc.cmd_deploy_lambda(
            {'lambda': 'contact_form', 'stage': 'dev', 'dry_run': True}
        )

        assert rc == 0
        assert 'CREATE' in capsys.readouterr().out


class TestCmdDestroy:
    """cmd_destroy exige --yes antes de borrar."""

    def test_cmd_destroy_without_yes_does_not_delete(
        self, monkeypatch, tmp_path
    ):
        """AC-5.3: destroy sin --yes no borra nada."""
        lc = _patch_common(monkeypatch, tmp_path)

        def _no_deprovision(*_a, **_k):
            raise AssertionError('sin --yes no debe borrar')

        monkeypatch.setattr(lc.provisioner, 'deprovision', _no_deprovision)

        rc = lc.cmd_destroy({'stage': 'dev'})

        assert rc == 2

    def test_cmd_destroy_with_yes_calls_deprovision(
        self, monkeypatch, tmp_path
    ):
        """AC-5.4: destroy --yes borra los lambdas + infra y limpia estado."""
        lc = _patch_common(monkeypatch, tmp_path)
        calls = {'deprovision': 0, 'infra': 0, 'cleared': 0}

        def _fake_state(scope, stage):
            from serverless.state import LambdaState

            return LambdaState(
                scope=scope,
                stage=stage,
                config_hash='sha256:c',
                code_hash='sha256:k',
                resources={},
                updated_at='2026-05-21T10:00:00Z',
            )

        monkeypatch.setattr(lc.state_mod, 'load_state', _fake_state)

        def _count_deprovision(*_a, **_k):
            calls['deprovision'] += 1

        monkeypatch.setattr(lc.provisioner, 'deprovision', _count_deprovision)

        def _fake_clear(_stage):
            calls['cleared'] += 1
            return []

        monkeypatch.setattr(lc.state_mod, 'clear_state', _fake_clear)

        import serverless.infra_provision as infra

        def _count_infra(*_a, **_k):
            calls['infra'] += 1

        monkeypatch.setattr(infra, 'deprovision_infra', _count_infra)

        rc = lc.cmd_destroy({'stage': 'dev', 'yes': True})

        assert rc == 0
        # Un deprovision por cada scope de _ALL_LAMBDA_SCOPES (los 8 lambdas).
        assert calls['deprovision'] == len(lc._ALL_LAMBDA_SCOPES)
        assert calls['deprovision'] == 8
        assert calls['infra'] == 1
        assert calls['cleared'] == 1


class TestCmdStatus:
    """cmd_status compara el estado local con AWS."""

    def test_cmd_status_compares_local_vs_aws(
        self, monkeypatch, tmp_path, capsys
    ):
        """AC-5.5: status reporta, por scope, el estado local vs AWS."""
        lc = _patch_common(monkeypatch, tmp_path)
        monkeypatch.setattr(lc.state_mod, 'load_state', lambda _s, _t: None)

        from serverless import aws_cli

        monkeypatch.setattr(
            aws_cli, 'aws_resource_exists', lambda *_a, **_k: False
        )

        rc = lc.cmd_status({'stage': 'dev'})

        out = capsys.readouterr().out
        assert rc == 0
        assert 'contact-form' in out
        assert 'sin deployar' in out
