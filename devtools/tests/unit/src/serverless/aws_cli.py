"""Unit tests for serverless.aws_cli - wrapper unico sobre el AWS CLI.

Path mirroring: devtools/serverless/aws_cli.py -> this file.

Verifica que el wrapper inyecte --profile/--region, parsee JSON, lance
AwsError cuando el comando falla y resuelva la existencia de recursos.
`subprocess.run` esta mockeado: ningun test toca AWS de verdad.
"""

import subprocess

import pytest


pytestmark = pytest.mark.unit


def _completed(returncode=0, stdout='', stderr=''):
    """Construye un CompletedProcess de prueba."""
    return subprocess.CompletedProcess(
        args=['aws'],
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


class TestAws:
    """aws() arma el comando, inyecta flags y maneja errores."""

    def test_aws_when_profile_given_includes_profile_flag(self, monkeypatch):
        from serverless import aws_cli

        captured = {}

        def fake_run(cmd, **_kwargs):
            captured['cmd'] = cmd
            return _completed()

        monkeypatch.setattr(subprocess, 'run', fake_run)

        aws_cli.aws(['sts', 'get-caller-identity'], profile='tfs-dev')

        assert '--profile' in captured['cmd']
        assert 'tfs-dev' in captured['cmd']
        assert '--region' in captured['cmd']
        assert 'us-east-1' in captured['cmd']

    def test_aws_when_no_profile_omits_profile_flag(self, monkeypatch):
        from serverless import aws_cli

        captured = {}

        def fake_run(cmd, **_kwargs):
            captured['cmd'] = cmd
            return _completed()

        monkeypatch.setattr(subprocess, 'run', fake_run)

        aws_cli.aws(['sts', 'get-caller-identity'])

        assert '--profile' not in captured['cmd']

    def test_aws_when_command_fails_and_check_raises_awserror(
        self, monkeypatch
    ):
        from serverless import aws_cli

        monkeypatch.setattr(
            subprocess,
            'run',
            lambda *_a, **_k: _completed(returncode=255, stderr='boom'),
        )

        with pytest.raises(aws_cli.AwsError) as exc_info:
            aws_cli.aws(['lambda', 'get-function'], check=True)

        assert exc_info.value.returncode == 255
        assert exc_info.value.stderr == 'boom'

    def test_aws_when_command_fails_and_no_check_returns_result(
        self, monkeypatch
    ):
        from serverless import aws_cli

        monkeypatch.setattr(
            subprocess,
            'run',
            lambda *_a, **_k: _completed(returncode=1, stderr='nope'),
        )

        result = aws_cli.aws(['lambda', 'get-function'], check=False)

        assert result.returncode == 1
        assert result.ok is False

    def test_aws_when_parse_json_returns_parsed_dict(self, monkeypatch):
        from serverless import aws_cli

        monkeypatch.setattr(
            subprocess,
            'run',
            lambda *_a, **_k: _completed(stdout='{"Account": "123"}'),
        )

        result = aws_cli.aws(['sts', 'get-caller-identity'], parse_json=True)

        assert result.json == {'Account': '123'}

    def test_aws_when_parse_json_and_empty_stdout_json_is_none(
        self, monkeypatch
    ):
        from serverless import aws_cli

        monkeypatch.setattr(
            subprocess,
            'run',
            lambda *_a, **_k: _completed(stdout=''),
        )

        result = aws_cli.aws(['logs', 'create-log-group'], parse_json=True)

        assert result.json is None

    def test_aws_when_invalid_json_raises_awserror(self, monkeypatch):
        from serverless import aws_cli

        monkeypatch.setattr(
            subprocess,
            'run',
            lambda *_a, **_k: _completed(stdout='not json'),
        )

        with pytest.raises(aws_cli.AwsError, match='no es JSON valido'):
            aws_cli.aws(['sts', 'get-caller-identity'], parse_json=True)


class TestAwsResourceExists:
    """aws_resource_exists() mapea el exit code de un describe-* a bool."""

    def test_aws_resource_exists_when_describe_returns_zero_true(
        self, monkeypatch
    ):
        from serverless import aws_cli

        monkeypatch.setattr(
            subprocess,
            'run',
            lambda *_a, **_k: _completed(returncode=0),
        )

        exists = aws_cli.aws_resource_exists(
            'dynamodb',
            ['describe-table', '--table-name', 'portfolio-contacts-dev'],
        )

        assert exists is True

    def test_aws_resource_exists_when_describe_returns_nonzero_false(
        self, monkeypatch
    ):
        from serverless import aws_cli

        monkeypatch.setattr(
            subprocess,
            'run',
            lambda *_a, **_k: _completed(returncode=254, stderr='Not Found'),
        )

        exists = aws_cli.aws_resource_exists(
            'dynamodb',
            ['describe-table', '--table-name', 'nope'],
        )

        assert exists is False
