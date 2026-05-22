"""Unit tests for serverless.provisioner - render + provision de Lambdas.

Path mirroring: devtools/serverless/provisioner.py -> this file (sin
prefijo test_, convencion de devtools).

`render` se prueba como funcion pura (sin AWS). `provision` y
`deprovision` se prueban con `aws_cli.aws` mockeado, capturando el orden
de las llamadas AWS CLI. Ningun test toca AWS de verdad.
"""

from pathlib import Path

import pytest


pytestmark = pytest.mark.unit

# Path del artefacto de deploy; en los tests nunca se lee de disco, solo
# se interpola en los strings de los comandos aws.
_ZIP_PATH = Path('build') / 'build.zip'


def _manifest_http():
    """Manifiesto de un Lambda con trigger http y uses (contact-form)."""
    return {
        'name': 'contact-form',
        'runtime': 'python3.13',
        'handler': 'core.handler.lambda_handler',
        'memory': 512,
        'timeout': 30,
        'region': 'us-east-1',
        'trigger': {'type': 'http', 'method': 'POST', 'path': '/contact'},
        'uses': {
            'tables': {
                'contacts': 'read-write',
                'cache': 'read-write',
            },
            'secrets': ['turnstile-secret', 'owner-email'],
            'sends-email': True,
        },
        'env': {
            'default': {'LOG_LEVEL': 'INFO'},
            'dev': {'LOG_LEVEL': 'INFO'},
        },
    }


def _manifest_stream():
    """Manifiesto de un Lambda con trigger on-table-changes."""
    return {
        'name': 'stream-processor',
        'runtime': 'python3.13',
        'handler': 'core.handler.lambda_handler',
        'memory': 512,
        'timeout': 60,
        'region': 'us-east-1',
        'trigger': {
            'type': 'on-table-changes',
            'tables': ['contacts', 'tracking'],
        },
        'uses': {
            'tables': [],
            'secrets': ['neon-url'],
            'sends-email': False,
        },
        'env': {'default': {'LOG_LEVEL': 'INFO'}},
    }


def _manifest_direct():
    """Manifiesto minimo de un Lambda con trigger direct, sin defaults."""
    return {
        'name': 'db',
        'runtime': 'python3.13',
        'handler': 'core.handler.lambda_handler',
        'region': 'us-east-1',
        'trigger': {'type': 'direct'},
        'uses': {'tables': [], 'secrets': [], 'sends-email': False},
        'env': {'default': {'LOG_LEVEL': 'INFO'}},
    }


def _fake_aws(recorder, responses=None):
    """Construye un fake de `aws()` que registra cada llamada.

    `recorder` es una lista que recibe los args de cada invocacion.
    `responses` mapea el primer arg del comando a un dict JSON simulado.
    """
    from serverless.aws_cli import AwsResult

    responses = responses or {}

    def fake(args, **_kwargs):
        recorder.append(args)
        json_payload = None
        # Resuelve la respuesta JSON segun el verbo del comando AWS.
        key = '.'.join(args[:2])
        if key in responses:
            json_payload = responses[key]
        return AwsResult(
            returncode=0,
            stdout='',
            stderr='',
            json=json_payload,
        )

    return fake


def _default_responses():
    """Respuestas JSON simuladas para los comandos aws de un CREATE."""
    return {
        'sts.get-caller-identity': {'Account': '111122223333'},
        'iam.create-role': {
            'Role': {
                'Arn': 'arn:aws:iam::111122223333:role/portfolio-x',
            },
        },
        'lambda.create-function': {
            'FunctionArn': 'arn:aws:lambda:us-east-1:111122223333:function:x',
        },
        'ssm.get-parameter': {'Parameter': {'Value': 'api-abc123'}},
        'apigateway.create-resource': {'id': 'res9'},
        'lambda.create-event-source-mapping': {'UUID': 'uuid-1'},
    }


class TestRender:
    """render() traduce el manifiesto a RenderedLambda. Funcion pura."""

    def test_render_iam_policy_when_uses_tables(self):
        from serverless import provisioner

        rendered = provisioner.render(_manifest_http(), stage='dev')

        statements = rendered.iam_policy['Statement']
        dynamo = [
            s
            for s in statements
            if any(a.startswith('dynamodb:') for a in s['Action'])
        ]
        assert len(dynamo) == 2
        assert dynamo[0]['Resource'] == [
            'arn:aws:dynamodb:us-east-1:${account}:'
            'table/portfolio-contacts-dev',
        ]

    def test_render_iam_policy_when_uses_secrets(self):
        from serverless import provisioner

        rendered = provisioner.render(_manifest_http(), stage='dev')

        statements = rendered.iam_policy['Statement']
        ssm = [s for s in statements if s['Action'] == ['ssm:GetParameter']]
        kms = [s for s in statements if s['Action'] == ['kms:Decrypt']]
        assert len(ssm) == 1
        assert len(kms) == 1
        assert (
            'arn:aws:ssm:us-east-1:${account}:'
            'parameter/portfolio/dev/turnstile-secret' in ssm[0]['Resource']
        )

    def test_render_iam_policy_when_sends_email(self):
        from serverless import provisioner

        rendered = provisioner.render(_manifest_http(), stage='dev')

        statements = rendered.iam_policy['Statement']
        ses = [
            s
            for s in statements
            if s['Action']
            == [
                'ses:SendEmail',
                'ses:SendRawEmail',
            ]
        ]
        assert len(ses) == 1
        assert (
            'arn:aws:ses:us-east-1:${account}:identity/the-full-stack.com'
            in ses[0]['Resource']
        )

    def test_render_iam_policy_when_on_table_changes(self):
        from serverless import provisioner

        rendered = provisioner.render(_manifest_stream(), stage='dev')

        statements = rendered.iam_policy['Statement']
        stream = [s for s in statements if 'dynamodb:GetRecords' in s['Action']]
        sqs = [s for s in statements if s['Action'] == ['sqs:SendMessage']]
        assert len(stream) == 1
        assert len(sqs) == 1
        assert stream[0]['Resource'] == [
            'arn:aws:dynamodb:us-east-1:${account}:'
            'table/portfolio-contacts-dev/stream/*',
            'arn:aws:dynamodb:us-east-1:${account}:'
            'table/portfolio-tracking-dev/stream/*',
        ]
        assert sqs[0]['Resource'] == [
            'arn:aws:sqs:us-east-1:${account}:'
            'portfolio-stream-processor-dlq-dev',
        ]

    def test_render_is_pure_same_input_same_output(self):
        from serverless import provisioner

        first = provisioner.render(_manifest_http(), stage='dev')
        second = provisioner.render(_manifest_http(), stage='dev')

        assert first == second

    def test_render_function_config_applies_defaults(self):
        from serverless import provisioner

        rendered = provisioner.render(_manifest_direct(), stage='dev')

        assert rendered.memory == 256
        assert rendered.timeout == 30
        assert rendered.architecture == 'arm64'
        assert rendered.function_name == 'portfolio-db-dev'
        assert rendered.role_name == 'portfolio-db-dev'

    def test_render_trigger_http_carries_method_and_path(self):
        from serverless import provisioner

        rendered = provisioner.render(_manifest_http(), stage='dev')

        assert rendered.trigger.type == 'http'
        assert rendered.trigger.method == 'POST'
        assert rendered.trigger.path == '/contact'

    def test_render_when_invalid_trigger_raises_manifest_error(self):
        from serverless.resolve import ManifestError

        from serverless import provisioner

        manifest = _manifest_direct()
        manifest['trigger'] = {'type': 'cron'}

        with pytest.raises(ManifestError, match=r'trigger\.type invalido'):
            provisioner.render(manifest, stage='dev')


class TestProvisionCreate:
    """provision() con Action.CREATE corre la secuencia completa."""

    def test_provision_create_call_order(self, monkeypatch):
        from serverless.state import Action

        from serverless import provisioner

        calls = []
        monkeypatch.setattr(
            provisioner,
            'aws',
            _fake_aws(calls, _default_responses()),
        )
        monkeypatch.setattr(provisioner.time, 'sleep', lambda _s: None)

        rendered = provisioner.render(_manifest_http(), stage='dev')
        state = provisioner.provision(
            rendered,
            action=Action.CREATE,
            zip_path=_ZIP_PATH,
            previous=None,
            profile=None,
            region='us-east-1',
        )

        verbs = ['.'.join(c[:2]) for c in calls]
        assert verbs == [
            'sts.get-caller-identity',
            'iam.create-role',
            'iam.put-role-policy',
            'iam.attach-role-policy',
            'logs.create-log-group',
            'logs.put-retention-policy',
            'lambda.create-function',
            'ssm.get-parameter',
            'ssm.get-parameter',
            'apigateway.create-resource',
            'apigateway.put-method',
            'apigateway.put-integration',
            'apigateway.create-deployment',
            'lambda.add-permission',
        ]
        assert state.resources['function_name'] == 'portfolio-contact-form-dev'

    def test_provision_create_records_resources(self, monkeypatch):
        from serverless.state import Action

        from serverless import provisioner

        calls = []
        monkeypatch.setattr(
            provisioner,
            'aws',
            _fake_aws(calls, _default_responses()),
        )
        monkeypatch.setattr(provisioner.time, 'sleep', lambda _s: None)

        rendered = provisioner.render(_manifest_http(), stage='dev')
        state = provisioner.provision(
            rendered,
            action=Action.CREATE,
            zip_path=_ZIP_PATH,
            previous=None,
            profile=None,
            region='us-east-1',
        )

        assert state.resources['role_arn'] == (
            'arn:aws:iam::111122223333:role/portfolio-x'
        )
        assert state.resources['log_group'] == (
            '/aws/lambda/portfolio-contact-form-dev'
        )
        assert state.resources['api_resource_id'] == 'res9'

    def test_provision_create_stream_creates_event_source_mappings(
        self, monkeypatch
    ):
        from serverless.state import Action

        from serverless import provisioner

        calls = []
        monkeypatch.setattr(
            provisioner,
            'aws',
            _fake_aws(calls, _default_responses()),
        )
        monkeypatch.setattr(provisioner.time, 'sleep', lambda _s: None)

        rendered = provisioner.render(_manifest_stream(), stage='dev')
        state = provisioner.provision(
            rendered,
            action=Action.CREATE,
            zip_path=_ZIP_PATH,
            previous=None,
            profile=None,
            region='us-east-1',
        )

        mappings = [
            c
            for c in calls
            if '.'.join(c[:2]) == 'lambda.create-event-source-mapping'
        ]
        assert len(mappings) == 2
        assert state.resources['event_source_uuids'] == 'uuid-1,uuid-1'


class TestProvisionUpdate:
    """provision() con Action.UPDATE_* corre solo lo que cambio."""

    def test_provision_update_code_only_calls_update_function_code(
        self, monkeypatch
    ):
        from serverless.state import Action
        from serverless.state import LambdaState

        from serverless import provisioner

        calls = []
        monkeypatch.setattr(provisioner, 'aws', _fake_aws(calls))

        rendered = provisioner.render(_manifest_http(), stage='dev')
        previous = LambdaState(
            scope='contact-form',
            stage='dev',
            config_hash='sha256:c',
            code_hash='sha256:OLD',
            resources={'function_name': 'portfolio-contact-form-dev'},
            updated_at='2026-05-21T10:00:00Z',
        )
        provisioner.provision(
            rendered,
            action=Action.UPDATE_CODE,
            zip_path=_ZIP_PATH,
            previous=previous,
            profile=None,
            region='us-east-1',
        )

        verbs = ['.'.join(c[:2]) for c in calls]
        assert verbs == ['lambda.update-function-code']

    def test_provision_update_config_calls_config_and_role_policy(
        self, monkeypatch
    ):
        from serverless.state import Action
        from serverless.state import LambdaState

        from serverless import provisioner

        calls = []
        monkeypatch.setattr(
            provisioner,
            'aws',
            _fake_aws(calls, _default_responses()),
        )

        rendered = provisioner.render(_manifest_http(), stage='dev')
        previous = LambdaState(
            scope='contact-form',
            stage='dev',
            config_hash='sha256:OLD',
            code_hash='sha256:k',
            resources={'function_name': 'portfolio-contact-form-dev'},
            updated_at='2026-05-21T10:00:00Z',
        )
        provisioner.provision(
            rendered,
            action=Action.UPDATE_CONFIG,
            zip_path=_ZIP_PATH,
            previous=previous,
            profile=None,
            region='us-east-1',
        )

        verbs = ['.'.join(c[:2]) for c in calls]
        assert verbs == [
            'sts.get-caller-identity',
            'lambda.update-function-configuration',
            'iam.put-role-policy',
        ]
        assert 'lambda.create-function' not in verbs

    def test_provision_update_both_runs_code_and_config(self, monkeypatch):
        from serverless.state import Action
        from serverless.state import LambdaState

        from serverless import provisioner

        calls = []
        monkeypatch.setattr(
            provisioner,
            'aws',
            _fake_aws(calls, _default_responses()),
        )

        rendered = provisioner.render(_manifest_http(), stage='dev')
        previous = LambdaState(
            scope='contact-form',
            stage='dev',
            config_hash='sha256:OLD',
            code_hash='sha256:OLD',
            resources={'function_name': 'portfolio-contact-form-dev'},
            updated_at='2026-05-21T10:00:00Z',
        )
        provisioner.provision(
            rendered,
            action=Action.UPDATE_BOTH,
            zip_path=_ZIP_PATH,
            previous=previous,
            profile=None,
            region='us-east-1',
        )

        verbs = ['.'.join(c[:2]) for c in calls]
        assert verbs == [
            'lambda.update-function-code',
            'sts.get-caller-identity',
            'lambda.update-function-configuration',
            'iam.put-role-policy',
        ]

    def test_provision_noop_makes_no_aws_calls(self, monkeypatch):
        from serverless.state import Action
        from serverless.state import LambdaState

        from serverless import provisioner

        calls = []
        monkeypatch.setattr(provisioner, 'aws', _fake_aws(calls))

        rendered = provisioner.render(_manifest_http(), stage='dev')
        previous = LambdaState(
            scope='contact-form',
            stage='dev',
            config_hash='sha256:c',
            code_hash='sha256:k',
            resources={'function_name': 'portfolio-contact-form-dev'},
            updated_at='2026-05-21T10:00:00Z',
        )
        provisioner.provision(
            rendered,
            action=Action.NOOP,
            zip_path=_ZIP_PATH,
            previous=previous,
            profile=None,
            region='us-east-1',
        )

        assert calls == []


class TestProvisionPartialFailure:
    """provision() que falla a mitad deja el estado parcial en la excepcion."""

    def test_provision_partial_failure_records_created_resources(
        self, monkeypatch
    ):
        from serverless.aws_cli import AwsError
        from serverless.aws_cli import AwsResult
        from serverless.state import Action

        from serverless import provisioner

        calls = []
        responses = _default_responses()

        def fake(args, **_kwargs):
            calls.append(args)
            key = '.'.join(args[:2])
            if key == 'lambda.create-function':
                raise AwsError(
                    'boom',
                    returncode=1,
                    stderr='no role',
                    args_used=args,
                )
            return AwsResult(
                returncode=0,
                stdout='',
                stderr='',
                json=responses.get(key),
            )

        monkeypatch.setattr(provisioner, 'aws', fake)
        monkeypatch.setattr(provisioner.time, 'sleep', lambda _s: None)

        rendered = provisioner.render(_manifest_http(), stage='dev')

        with pytest.raises(AwsError) as exc_info:
            provisioner.provision(
                rendered,
                action=Action.CREATE,
                zip_path=_ZIP_PATH,
                previous=None,
                profile=None,
                region='us-east-1',
            )

        partial = exc_info.value.partial_state
        assert partial.resources['role_arn'] == (
            'arn:aws:iam::111122223333:role/portfolio-x'
        )
        assert partial.resources['log_group'] == (
            '/aws/lambda/portfolio-contact-form-dev'
        )
        assert 'function_name' not in partial.resources


class TestDeprovision:
    """deprovision() borra los recursos en orden inverso al de creacion."""

    def test_deprovision_reverse_order(self, monkeypatch):
        from serverless.aws_cli import AwsResult
        from serverless.state import LambdaState

        from serverless import provisioner

        calls = []

        def fake(args, **_kwargs):
            calls.append(args)
            key = '.'.join(args[:2])
            if key == 'ssm.get-parameter':
                return AwsResult(
                    returncode=0,
                    stdout='',
                    stderr='',
                    json={'Parameter': {'Value': 'api-abc123'}},
                )
            return AwsResult(returncode=0, stdout='', stderr='', json=None)

        monkeypatch.setattr(provisioner, 'aws', fake)

        state = LambdaState(
            scope='contact-form',
            stage='dev',
            config_hash='sha256:c',
            code_hash='',
            resources={
                'role_name': 'portfolio-contact-form-dev',
                'function_name': 'portfolio-contact-form-dev',
                'log_group': '/aws/lambda/portfolio-contact-form-dev',
                'api_resource_id': 'res9',
            },
            updated_at='2026-05-21T10:00:00Z',
        )
        provisioner.deprovision(state, profile=None, region='us-east-1')

        verbs = ['.'.join(c[:2]) for c in calls]
        assert verbs == [
            'lambda.remove-permission',
            'ssm.get-parameter',
            'apigateway.delete-resource',
            'lambda.delete-function',
            'iam.delete-role-policy',
            'iam.detach-role-policy',
            'iam.delete-role',
            'logs.delete-log-group',
        ]

    def test_deprovision_stream_deletes_event_source_mappings(
        self, monkeypatch
    ):
        from serverless.aws_cli import AwsResult
        from serverless.state import LambdaState

        from serverless import provisioner

        calls = []
        monkeypatch.setattr(
            provisioner,
            'aws',
            lambda args, **_k: (
                calls.append(args)
                or AwsResult(returncode=0, stdout='', stderr='', json=None)
            ),
        )

        state = LambdaState(
            scope='stream-processor',
            stage='dev',
            config_hash='sha256:c',
            code_hash='',
            resources={
                'role_name': 'portfolio-stream-processor-dev',
                'function_name': 'portfolio-stream-processor-dev',
                'log_group': '/aws/lambda/portfolio-stream-processor-dev',
                'event_source_uuids': 'uuid-1,uuid-2',
            },
            updated_at='2026-05-21T10:00:00Z',
        )
        provisioner.deprovision(state, profile=None, region='us-east-1')

        verbs = ['.'.join(c[:2]) for c in calls]
        assert verbs == [
            'lambda.delete-event-source-mapping',
            'lambda.delete-event-source-mapping',
            'lambda.delete-function',
            'iam.delete-role-policy',
            'iam.detach-role-policy',
            'iam.delete-role',
            'logs.delete-log-group',
        ]
