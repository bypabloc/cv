"""Unit tests for serverless.email_seed — seed de la tabla email-config.

Path mirroring: devtools/serverless/email_seed.py -> este archivo (sin
prefijo test_, convencion de devtools).

`build_seed_plan` se prueba como funcion pura sobre los templates +
build_rows del Lambda `send_email`. `cmd_seed_email_config` se prueba con
`aws_cli.aws` y `aws_cli.aws_resource_exists` mockeados, capturando el
orden de las llamadas AWS CLI (s3 cp + dynamodb put-item). Ningun test
toca AWS de verdad.
"""

from pathlib import Path
from typing import Any

import pytest


pytestmark = pytest.mark.unit


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
class _AwsCall:
    """Registro de una invocacion a `aws_cli.aws`."""

    def __init__(self, args: list[str]) -> None:
        self.args = args


def _make_fake_aws(calls: list[_AwsCall]) -> Any:
    """Fake de `aws_cli.aws` que registra cada invocacion."""

    def _fake(args: list[str], **_kwargs: Any) -> Any:
        calls.append(_AwsCall(list(args)))

        class _Result:
            returncode = 0
            stdout = ''
            stderr = ''
            json = None

        return _Result()

    return _fake


# --------------------------------------------------------------------------
# build_seed_plan — funcion pura
# --------------------------------------------------------------------------
class TestBuildSeedPlan:
    def test_build_seed_plan_returns_bucket_and_table_for_stage(self):
        """
        Given el stage 'dev',
        When se construye el plan de seed,
        Then bucket y table usan el nombre fisico con el sufijo del stage.
        """
        from serverless.email_seed import build_seed_plan

        plan = build_seed_plan(stage='dev')

        assert plan.bucket == 'portfolio-email-templates-dev'
        assert plan.table == 'portfolio-email-config-dev'

    def test_build_seed_plan_uploads_twenty_templates(self):
        """
        Given los 10 kinds de email (cada uno html + txt),
        When se construye el plan,
        Then hay exactamente 20 uploads de template.
        """
        from serverless.email_seed import build_seed_plan

        plan = build_seed_plan(stage='dev')

        assert len(plan.uploads) == 20

    def test_build_seed_plan_uploads_have_local_path_and_s3_key(self):
        """
        Given el kind 'contact',
        When se construye el plan,
        Then el upload html mapea contact.html (local) -> contact.html (key).
        """
        from serverless.email_seed import build_seed_plan

        plan = build_seed_plan(stage='dev')

        html = next(u for u in plan.uploads if u.s3_key == 'contact.html')
        assert html.local_path.name == 'contact.html'
        assert html.local_path.is_file()

    def test_build_seed_plan_builds_ten_config_rows(self):
        """
        Given los 10 kinds,
        When se construye el plan,
        Then hay 10 filas de email-config.
        """
        from serverless.email_seed import build_seed_plan

        plan = build_seed_plan(stage='dev')

        assert len(plan.rows) == 10

    def test_build_seed_plan_row_has_bucket_and_paths(self):
        """
        Given la fila del kind 'contact',
        When se construye el plan para stage 'prod',
        Then la fila tiene el bucket de prod + paths html/txt + subject.
        """
        from serverless.email_seed import build_seed_plan

        plan = build_seed_plan(stage='prod')

        row = next(r for r in plan.rows if r['kind'] == 'contact')
        assert row['bucket'] == 'portfolio-email-templates-prod'
        assert row['html_path'] == 'contact.html'
        assert row['txt_path'] == 'contact.txt'
        assert row['subject'] == 'Nuevo contacto de {{ name }}'


# --------------------------------------------------------------------------
# cmd_seed_email_config — aws_cli mockeado
# --------------------------------------------------------------------------
class TestCmdSeedEmailConfig:
    def _patch_exists(self, monkeypatch, *, exists: bool) -> None:
        from serverless import aws_cli

        monkeypatch.setattr(
            aws_cli,
            'aws_resource_exists',
            lambda *a, **k: exists,
        )

    def test_seed_uploads_templates_and_puts_items(self, monkeypatch):
        """
        Given el bucket y la tabla existen,
        When se corre seed-email-config para stage dev,
        Then hace 20 `s3 cp` + 10 `dynamodb put-item` (exit 0).
        """
        from serverless import aws_cli
        from serverless.email_seed import cmd_seed_email_config

        calls: list[_AwsCall] = []
        monkeypatch.setattr(aws_cli, 'aws', _make_fake_aws(calls))
        self._patch_exists(monkeypatch, exists=True)

        rc = cmd_seed_email_config({'stage': 'dev'})

        s3_cps = [c for c in calls if c.args[:2] == ['s3', 'cp']]
        put_items = [
            c for c in calls if c.args[:2] == ['dynamodb', 'put-item']
        ]
        assert rc == 0
        assert len(s3_cps) == 20
        assert len(put_items) == 10

    def test_seed_aborts_when_bucket_missing(self, monkeypatch):
        """
        Given el bucket NO existe,
        When se corre seed-email-config,
        Then aborta con exit 1 sin subir nada.
        """
        from serverless import aws_cli
        from serverless.email_seed import cmd_seed_email_config

        calls: list[_AwsCall] = []
        monkeypatch.setattr(aws_cli, 'aws', _make_fake_aws(calls))
        self._patch_exists(monkeypatch, exists=False)

        rc = cmd_seed_email_config({'stage': 'dev'})

        assert rc == 1
        assert calls == []

    def test_seed_rejects_local_stage(self, monkeypatch):
        """
        Given el stage 'local' (no usa AWS),
        When se corre seed-email-config,
        Then aborta con exit 1.
        """
        from serverless import aws_cli
        from serverless.email_seed import cmd_seed_email_config

        calls: list[_AwsCall] = []
        monkeypatch.setattr(aws_cli, 'aws', _make_fake_aws(calls))

        rc = cmd_seed_email_config({'stage': 'local'})

        assert rc == 1
        assert calls == []
