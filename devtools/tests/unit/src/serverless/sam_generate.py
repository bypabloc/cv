"""Unit tests for serverless.sam_generate - generacion del SAM template.

Path mirroring: devtools/serverless/sam_generate.py -> this file.

Verifica el mapeo lambda.yaml -> AWS::Serverless::Function: runtime,
handler, memoria, timeout, env vars por stage, layers, IAM policies.
"""

import pytest


pytestmark = pytest.mark.unit


def _manifest(**overrides):
    """Manifiesto base con defaults aplicados, sobrescribible."""
    base = {
        'name': 'payment-router',
        'runtime': 'python3.13',
        'handler': 'core.handler.lambda_handler',
        'memory': 256,
        'timeout': 30,
        'region': 'us-east-1',
    }
    base.update(overrides)
    return base


class TestBuildTemplate:
    """build_template mapea el manifiesto al dict del SAM template."""

    def test_function_logical_id_is_pascal_case(self):
        from serverless.sam_generate import build_template

        template = build_template(_manifest())

        assert 'PaymentRouterFunction' in template['Resources']

    def test_function_props_mapped_from_manifest(self):
        from serverless.sam_generate import build_template

        template = build_template(_manifest(memory=512, timeout=60))
        props = template['Resources']['PaymentRouterFunction']['Properties']

        assert props['Runtime'] == 'python3.13'
        assert props['Handler'] == 'core.handler.lambda_handler'
        assert props['MemorySize'] == 512
        assert props['Timeout'] == 60

    def test_function_name_includes_stage(self):
        from serverless.sam_generate import build_template

        template = build_template(_manifest(), stage='prod')
        props = template['Resources']['PaymentRouterFunction']['Properties']

        assert props['FunctionName'] == 'payment-router-prod'

    def test_resource_type_is_serverless_function(self):
        from serverless.sam_generate import build_template

        template = build_template(_manifest())

        assert (
            template['Resources']['PaymentRouterFunction']['Type']
            == 'AWS::Serverless::Function'
        )


class TestEnvironmentResolution:
    """_resolve_env combina environment.default + environment.<stage>."""

    def test_stage_env_overrides_default(self):
        from serverless.sam_generate import build_template

        manifest = _manifest(
            environment={
                'default': {'LOG_LEVEL': 'INFO'},
                'prod': {'LOG_LEVEL': 'WARNING'},
            },
        )

        template = build_template(manifest, stage='prod')
        props = template['Resources']['PaymentRouterFunction']['Properties']

        assert props['Environment']['Variables']['LOG_LEVEL'] == 'WARNING'

    def test_default_env_applies_when_stage_absent(self):
        from serverless.sam_generate import build_template

        manifest = _manifest(
            environment={'default': {'REGION': 'us-east-1'}},
        )

        template = build_template(manifest, stage='dev')
        props = template['Resources']['PaymentRouterFunction']['Properties']

        assert props['Environment']['Variables']['REGION'] == 'us-east-1'

    def test_env_values_coerced_to_string(self):
        from serverless.sam_generate import build_template

        manifest = _manifest(environment={'default': {'TIMEOUT': 30}})

        template = build_template(manifest)
        props = template['Resources']['PaymentRouterFunction']['Properties']

        assert props['Environment']['Variables']['TIMEOUT'] == '30'

    def test_invalid_env_stage_raises(self):
        from serverless.resolve import ManifestError
        from serverless.sam_generate import build_template

        manifest = _manifest(environment={'qa': {'X': 'y'}})

        with pytest.raises(ManifestError, match='qa'):
            build_template(manifest)


class TestLayersAndPolicies:
    """layers e iam_policies son opcionales y se pasan tal cual."""

    def test_layers_included_when_present(self):
        from serverless.sam_generate import build_template

        manifest = _manifest(layers=['arn:aws:lambda:us-east-1:1:layer:x:1'])

        template = build_template(manifest)
        props = template['Resources']['PaymentRouterFunction']['Properties']

        assert props['Layers'] == ['arn:aws:lambda:us-east-1:1:layer:x:1']

    def test_policies_included_when_present(self):
        from serverless.sam_generate import build_template

        manifest = _manifest(iam_policies=['AWSLambdaBasicExecutionRole'])

        template = build_template(manifest)
        props = template['Resources']['PaymentRouterFunction']['Properties']

        assert props['Policies'] == ['AWSLambdaBasicExecutionRole']

    def test_no_layers_key_when_absent(self):
        from serverless.sam_generate import build_template

        template = build_template(_manifest())
        props = template['Resources']['PaymentRouterFunction']['Properties']

        assert 'Layers' not in props


class TestGenerateSamFile:
    """generate_sam_file escribe el template.yaml efimero."""

    def test_legacy_lambda_cannot_generate(self):
        from serverless.resolve import ManifestError
        from serverless.resolve import ResolvedLambda
        from serverless.sam_generate import generate_sam_file

        legacy = ResolvedLambda(mode='legacy', root=None)

        with pytest.raises(ManifestError, match=r'lambda\.yaml'):
            generate_sam_file(legacy)

    def test_writes_template_yaml_in_lambda_root(self, tmp_path):
        from serverless.resolve import ResolvedLambda
        from serverless.sam_generate import generate_sam_file

        resolved = ResolvedLambda(
            mode='lambda-controller',
            root=tmp_path,
            manifest=_manifest(),
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
            manifest=_manifest(),
        )

        out = generate_sam_file(resolved)

        assert 'NO EDITAR' in out.read_text(encoding='utf-8')
