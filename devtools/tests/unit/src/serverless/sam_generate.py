"""Unit tests for serverless.sam_generate - lambda.yaml formato dev -> SAM.

Path mirroring: devtools/serverless/sam_generate.py -> this file.

Verifica la traduccion del manifiesto `lambda.yaml` formato dev (que
describe el lambda en terminos de desarrollador) al template SAM:
trigger, uses (tablas / secretos / email), env vars y permisos IAM.
"""

import pytest


pytestmark = pytest.mark.unit


def _manifest_direct() -> dict:
    """Manifiesto minimo de un lambda con trigger directo (tipo db)."""
    return {
        'name': 'db',
        'runtime': 'python3.13',
        'handler': 'core.handler.lambda_handler',
        'memory': 512,
        'timeout': 120,
        'trigger': {'type': 'direct'},
        'uses': {'tables': [], 'secrets': ['neon-url'], 'sends-email': False},
        'env': {'default': {'LOG_LEVEL': 'INFO'}},
    }


def _manifest_http() -> dict:
    """Manifiesto de un lambda con trigger http (tipo contact_form)."""
    return {
        'name': 'contact-form',
        'runtime': 'python3.13',
        'handler': 'core.handler.lambda_handler',
        'memory': 512,
        'timeout': 30,
        'trigger': {'type': 'http', 'method': 'POST', 'path': '/contact'},
        'uses': {
            'tables': {'contacts': 'read-write'},
            'secrets': ['turnstile-secret'],
            'sends-email': True,
        },
        'env': {'default': {'LOG_LEVEL': 'INFO'}},
    }


def _manifest_stream() -> dict:
    """Manifiesto de un lambda con trigger on-table-changes."""
    return {
        'name': 'stream-processor',
        'runtime': 'python3.13',
        'handler': 'core.handler.lambda_handler',
        'memory': 512,
        'timeout': 60,
        'trigger': {
            'type': 'on-table-changes',
            'tables': ['contacts', 'tracking'],
        },
        'uses': {'tables': [], 'secrets': ['neon-url'], 'sends-email': False},
        'env': {'default': {'LOG_LEVEL': 'INFO'}},
    }


class TestBuildTemplateBasics:
    """build_template produce un SAM template valido."""

    def test_template_has_serverless_transform(self):
        from serverless.sam_generate import build_template

        template = build_template(_manifest_direct(), stage='dev')

        assert template['Transform'] == 'AWS::Serverless-2016-10-31'

    def test_function_logical_id_is_pascal_case(self):
        from serverless.sam_generate import build_template

        template = build_template(_manifest_direct(), stage='dev')

        assert 'DbFunction' in template['Resources']

    def test_function_name_includes_portfolio_prefix_and_stage(self):
        from serverless.sam_generate import build_template

        template = build_template(_manifest_direct(), stage='dev')

        props = template['Resources']['DbFunction']['Properties']
        assert props['FunctionName'] == 'portfolio-db-dev'


class TestEnvVars:
    """El bloque de env vars combina env explicito + uses."""

    def test_secret_path_injected_as_env_var(self):
        from serverless.sam_generate import build_template

        template = build_template(_manifest_direct(), stage='dev')

        env = template['Resources']['DbFunction']['Properties']['Environment'][
            'Variables'
        ]
        assert env['SSM_NEON_URL_PATH'] == '/portfolio/dev/neon-url'

    def test_table_name_injected_as_env_var(self):
        from serverless.sam_generate import build_template

        template = build_template(_manifest_http(), stage='dev')

        env = template['Resources']['ContactFormFunction']['Properties'][
            'Environment'
        ]['Variables']
        assert env['CONTACTS_TABLE_NAME'] == 'portfolio-contacts-dev'

    def test_invalid_env_stage_raises(self):
        from serverless.resolve import ManifestError
        from serverless.sam_generate import build_template

        manifest = _manifest_direct()
        manifest['env'] = {'qa': {'LOG_LEVEL': 'DEBUG'}}

        with pytest.raises(ManifestError):
            build_template(manifest, stage='dev')


class TestPermissions:
    """uses se traduce a Statements IAM."""

    def test_dynamodb_table_produces_policy_statement(self):
        from serverless.sam_generate import build_template

        template = build_template(_manifest_http(), stage='dev')

        policies = template['Resources']['ContactFormFunction']['Properties'][
            'Policies'
        ]
        statements = policies[0]['Statement']
        actions = [a for st in statements for a in st['Action']]
        assert 'dynamodb:PutItem' in actions

    def test_sends_email_produces_ses_statement(self):
        from serverless.sam_generate import build_template

        template = build_template(_manifest_http(), stage='dev')

        policies = template['Resources']['ContactFormFunction']['Properties'][
            'Policies'
        ]
        actions = [a for st in policies[0]['Statement'] for a in st['Action']]
        assert 'ses:SendEmail' in actions

    def test_secret_produces_kms_decrypt_statement(self):
        from serverless.sam_generate import build_template

        template = build_template(_manifest_direct(), stage='dev')

        policies = template['Resources']['DbFunction']['Properties']['Policies']
        actions = [a for st in policies[0]['Statement'] for a in st['Action']]
        assert 'kms:Decrypt' in actions

    def test_direct_lambda_without_tables_has_no_dynamodb_action(self):
        from serverless.sam_generate import build_template

        template = build_template(_manifest_direct(), stage='dev')

        policies = template['Resources']['DbFunction']['Properties']['Policies']
        actions = [a for st in policies[0]['Statement'] for a in st['Action']]
        assert 'dynamodb:PutItem' not in actions


class TestTriggers:
    """trigger se traduce a Events o recursos de API Gateway."""

    def test_direct_trigger_has_no_events(self):
        from serverless.sam_generate import build_template

        template = build_template(_manifest_direct(), stage='dev')

        props = template['Resources']['DbFunction']['Properties']
        assert 'Events' not in props

    def test_http_trigger_creates_apigw_method_resource(self):
        from serverless.sam_generate import build_template

        template = build_template(_manifest_http(), stage='dev')

        assert template['Resources']['ApiMethod']['Type'] == (
            'AWS::ApiGateway::Method'
        )

    def test_http_trigger_creates_lambda_permission(self):
        from serverless.sam_generate import build_template

        template = build_template(_manifest_http(), stage='dev')

        assert template['Resources']['ApiInvokePermission']['Type'] == (
            'AWS::Lambda::Permission'
        )

    def test_on_table_changes_creates_dynamodb_events(self):
        from serverless.sam_generate import build_template

        template = build_template(_manifest_stream(), stage='dev')

        events = template['Resources']['StreamProcessorFunction']['Properties'][
            'Events'
        ]
        assert events['ContactsStream']['Type'] == 'DynamoDB'


class TestValidation:
    """build_template rechaza manifiestos invalidos."""

    def test_rejects_unknown_trigger_type(self):
        from serverless.resolve import ManifestError
        from serverless.sam_generate import build_template

        manifest = _manifest_direct()
        manifest['trigger'] = {'type': 'cron'}

        with pytest.raises(ManifestError):
            build_template(manifest, stage='dev')

    def test_rejects_unknown_table(self):
        from serverless.resolve import ManifestError
        from serverless.sam_generate import build_template

        manifest = _manifest_http()
        manifest['uses']['tables'] = {'nonexistent-table': 'read'}

        with pytest.raises(ManifestError):
            build_template(manifest, stage='dev')

    def test_rejects_unknown_secret(self):
        from serverless.resolve import ManifestError
        from serverless.sam_generate import build_template

        manifest = _manifest_direct()
        manifest['uses']['secrets'] = ['nonexistent-secret']

        with pytest.raises(ManifestError):
            build_template(manifest, stage='dev')


class TestGenerateSamFile:
    """generate_sam_file escribe el template.yaml en el lambda."""

    def test_writes_template_yaml_in_lambda_root(self, tmp_path):
        from serverless.resolve import ResolvedLambda
        from serverless.sam_generate import generate_sam_file

        resolved = ResolvedLambda(
            mode='lambda-controller',
            root=tmp_path,
            manifest=_manifest_direct(),
        )

        out = generate_sam_file(resolved, stage='dev')

        assert out == tmp_path / 'template.yaml'
        assert out.is_file()

    def test_generated_file_has_do_not_edit_header(self, tmp_path):
        from serverless.resolve import ResolvedLambda
        from serverless.sam_generate import generate_sam_file

        resolved = ResolvedLambda(
            mode='lambda-controller',
            root=tmp_path,
            manifest=_manifest_direct(),
        )

        out = generate_sam_file(resolved, stage='dev')

        assert 'NO EDITAR' in out.read_text(encoding='utf-8')
