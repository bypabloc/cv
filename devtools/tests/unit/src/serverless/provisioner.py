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
    """Manifiesto de un Lambda con trigger http y uses (contact-form).

    Tablas: solo infra (cache + rate-limit-buckets). Spec
    direct-neon-writes elimino `contacts` y `tracking` del catalogo
    `_TABLES` del provisioner — los Lambdas escriben directo a Neon.
    """
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
                'rate-limit-buckets': 'read-write',
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
        # El Statement scope a la tabla + a sus indices (index/*) para
        # soportar Query sobre GSI (ej. jwt-blacklist#by_family_id).
        assert dynamo[0]['Resource'] == [
            'arn:aws:dynamodb:us-east-1:${account}:'
            'table/portfolio-rate-limit-buckets-dev',
            'arn:aws:dynamodb:us-east-1:${account}:'
            'table/portfolio-rate-limit-buckets-dev/index/*',
        ]

    def test_render_email_config_table_path_and_arn(self):
        """La tabla `email-config` (la usa send_email) se resuelve a su
        nombre fisico + env var SSM_EMAIL_CONFIG_TABLE_PATH + IAM read.
        """
        from serverless import provisioner

        manifest = _manifest_http()
        manifest['name'] = 'send-email'
        manifest['uses']['tables'] = {'email-config': 'read'}

        rendered = provisioner.render(manifest, stage='dev')

        assert (
            rendered.env_vars['SSM_EMAIL_CONFIG_TABLE_PATH']
            == '/portfolio/dev/dynamodb/email-config/name'
        )
        statements = rendered.iam_policy['Statement']
        dynamo = [
            s
            for s in statements
            if any(a.startswith('dynamodb:') for a in s['Action'])
        ]
        assert dynamo[0]['Resource'] == [
            'arn:aws:dynamodb:us-east-1:${account}:'
            'table/portfolio-email-config-dev',
            'arn:aws:dynamodb:us-east-1:${account}:'
            'table/portfolio-email-config-dev/index/*',
        ]

    def test_render_table_read_grants_scan_for_tag_invalidation(self):
        """
        Given un manifest con una tabla `uses.tables` en modo read,
        When se renderiza la policy IAM,
        Then el Statement read incluye dynamodb:Scan (lo usa la
        invalidacion por tag del cache: invalidate_by_tag hace
        table.scan; sin Scan, cv_admin revienta con AccessDenied al
        invalidar el tag 'cv' tras cada escritura).
        """
        from serverless import provisioner

        manifest = _manifest_http()
        manifest['uses']['tables'] = {'cache': 'read'}

        rendered = provisioner.render(manifest, stage='dev')

        statements = rendered.iam_policy['Statement']
        dynamo = [
            s
            for s in statements
            if any(a.startswith('dynamodb:') for a in s['Action'])
        ]
        assert dynamo[0]['Action'] == [
            'dynamodb:GetItem',
            'dynamodb:Query',
            'dynamodb:BatchGetItem',
            'dynamodb:Scan',
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

    def test_secret_out_of_stage_omitted_from_env_and_iam(self):
        """Un secreto que el catalogo NO declara en el stage no se inyecta.

        `turnstile-bypass-public-key` solo existe en dev/stage (stages:
        [dev, stage]). Un deploy a prod NO debe inyectar su path SSM ni
        conceder IAM sobre el ARN inexistente.
        """
        from serverless import provisioner

        manifest = _manifest_http()
        manifest['uses']['secrets'] = [
            'turnstile-secret',  # dev,stage,prod
            'turnstile-bypass-public-key',  # solo dev,stage
        ]

        # En dev: el bypass public key SI esta presente (env + IAM).
        dev = provisioner.render(manifest, stage='dev')
        assert 'SSM_TURNSTILE_BYPASS_PUBLIC_KEY_PATH' in dev.env_vars
        dev_ssm = next(
            s['Resource']
            for s in dev.iam_policy['Statement']
            if s['Action'] == ['ssm:GetParameter']
        )
        assert any('turnstile-bypass-public-key' in arn for arn in dev_ssm)

        # En prod: el bypass public key NO esta (no declarado para prod);
        # turnstile-secret (dev,stage,prod) SI sigue.
        prod = provisioner.render(manifest, stage='prod')
        assert 'SSM_TURNSTILE_BYPASS_PUBLIC_KEY_PATH' not in prod.env_vars
        assert 'SSM_TURNSTILE_SECRET_PATH' in prod.env_vars
        prod_ssm = next(
            s['Resource']
            for s in prod.iam_policy['Statement']
            if s['Action'] == ['ssm:GetParameter']
        )
        assert not any('turnstile-bypass-public-key' in arn for arn in prod_ssm)

    def test_render_iam_policy_when_uses_kms(self):
        from serverless import provisioner

        manifest = _manifest_http()
        manifest['uses']['kms'] = [
            {'alias': 'portfolio-lambdas', 'actions': ['Encrypt', 'Decrypt']},
        ]

        rendered = provisioner.render(manifest, stage='dev')

        statements = rendered.iam_policy['Statement']
        kms_direct = [
            s
            for s in statements
            if s['Action'] == ['kms:Encrypt', 'kms:Decrypt']
        ]
        assert len(kms_direct) == 1
        assert kms_direct[0]['Resource'] == (
            'arn:aws:kms:us-east-1:${account}:key/*'
        )
        # No lleva Condition kms:ViaService (es CMK directa, no via SSM).
        assert 'Condition' not in kms_direct[0]

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
        assert rendered.trigger.methods == ('POST',)
        assert rendered.trigger.path == '/contact'

    def test_render_when_invalid_trigger_raises_manifest_error(self):
        from serverless import provisioner
        from serverless.resolve import ManifestError

        manifest = _manifest_direct()
        manifest['trigger'] = {'type': 'cron'}

        with pytest.raises(ManifestError, match=r'trigger\.type invalido'):
            provisioner.render(manifest, stage='dev')

    def test_render_trigger_http_methods_list_normalized(self):
        from serverless import provisioner

        manifest = _manifest_http()
        manifest['trigger'] = {
            'type': 'http',
            'methods': ['get', 'post'],
            'path': '/auth',
        }

        rendered = provisioner.render(manifest, stage='dev')

        assert rendered.trigger.methods == ('GET', 'POST')
        assert rendered.trigger.path == '/auth'

    def test_render_trigger_http_methods_dedup_preserves_order(self):
        from serverless import provisioner

        manifest = _manifest_http()
        manifest['trigger'] = {
            'type': 'http',
            'methods': ['POST', 'GET', 'POST'],
            'path': '/auth',
        }

        rendered = provisioner.render(manifest, stage='dev')

        assert rendered.trigger.methods == ('POST', 'GET')

    def test_render_trigger_http_method_and_methods_both_raises(self):
        from serverless import provisioner
        from serverless.resolve import ManifestError

        manifest = _manifest_http()
        manifest['trigger'] = {
            'type': 'http',
            'method': 'POST',
            'methods': ['GET'],
            'path': '/auth',
        }

        with pytest.raises(ManifestError, match=r"'method'.*O.*'methods'"):
            provisioner.render(manifest, stage='dev')

    def test_render_trigger_http_no_method_raises(self):
        from serverless import provisioner
        from serverless.resolve import ManifestError

        manifest = _manifest_http()
        manifest['trigger'] = {'type': 'http', 'path': '/auth'}

        with pytest.raises(ManifestError, match=r"'method'.*'methods'"):
            provisioner.render(manifest, stage='dev')

    def test_render_trigger_http_invalid_method_raises(self):
        from serverless import provisioner
        from serverless.resolve import ManifestError

        manifest = _manifest_http()
        manifest['trigger'] = {
            'type': 'http',
            'methods': ['GET', 'TRACE'],
            'path': '/auth',
        }

        with pytest.raises(ManifestError, match=r'metodo invalido'):
            provisioner.render(manifest, stage='dev')


class TestProvisionCreate:
    """provision() con Action.CREATE corre la secuencia completa."""

    def test_provision_create_call_order(self, monkeypatch):
        from serverless import provisioner
        from serverless.state import Action

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
        # Orden post fix CORS preflight (PR #107): el _wire_http_trigger
        # crea POST + OPTIONS con sus put-method-response/put-integration-
        # response antes de la deployment. La 2a `apigateway.put-method`
        # corresponde a OPTIONS y las 2 put-*-response son su respuesta
        # mockeada para devolver headers CORS al preflight.
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
            # Idempotencia: get-resources verifica si /path ya existe
            # antes de create-resource (evita BadRequest en re-corrida).
            'apigateway.get-resources',
            'apigateway.create-resource',
            'apigateway.put-method',
            'apigateway.put-integration',
            'apigateway.put-method',
            'apigateway.put-integration',
            'apigateway.put-method-response',
            'apigateway.put-integration-response',
            'apigateway.create-deployment',
            # get-policy: inspecciona statements obsoletos
            # (legacy SAM o devtools previo con qualifier distinto)
            # antes de add-permission. En CREATE el policy esta vacio
            # asi que el cleanup no llama remove-permission, pero el
            # wiring SI hace un remove-permission del target_sid (noop si
            # no existe) antes del add-permission, para garantizar que el
            # statement se recree con el source_arn wildcard correcto.
            'lambda.get-policy',
            'lambda.remove-permission',
            'lambda.add-permission',
            # Tras el wiring, `_disable_snap_start` corre tambien en CREATE
            # (el manifest test tiene snap_start=False): cubre el caso de
            # una funcion preexistente con SnapStart re-creada por state
            # perdido. Aqui es no-op (get-function-configuration None +
            # delete-alias + list-aliases + list-versions sin borrados).
            'lambda.get-function-configuration',
            'lambda.delete-alias',
            'lambda.list-aliases',
            'lambda.list-versions-by-function',
        ]
        assert state.resources['function_name'] == 'portfolio-contact-form-dev'

    def test_provision_create_multi_method_wires_each_method(self, monkeypatch):
        from serverless import provisioner
        from serverless.state import Action

        calls = []
        monkeypatch.setattr(
            provisioner,
            'aws',
            _fake_aws(calls, _default_responses()),
        )
        monkeypatch.setattr(provisioner.time, 'sleep', lambda _s: None)

        manifest = _manifest_http()
        manifest['trigger'] = {
            'type': 'http',
            'methods': ['GET', 'POST'],
            'path': '/auth',
        }
        rendered = provisioner.render(manifest, stage='dev')
        provisioner.provision(
            rendered,
            action=Action.CREATE,
            zip_path=_ZIP_PATH,
            previous=None,
            profile=None,
            region='us-east-1',
        )

        verbs = ['.'.join(c[:2]) for c in calls]
        # GET y POST: cada uno con put-method + put-integration (2 pares),
        # luego OPTIONS (put-method + put-integration + sus 2 responses).
        api_seq = [v for v in verbs if v.startswith('apigateway.')]
        assert api_seq == [
            'apigateway.get-resources',
            'apigateway.create-resource',
            'apigateway.put-method',  # GET
            'apigateway.put-integration',  # GET
            'apigateway.put-method',  # POST
            'apigateway.put-integration',  # POST
            'apigateway.put-method',  # OPTIONS
            'apigateway.put-integration',  # OPTIONS
            'apigateway.put-method-response',
            'apigateway.put-integration-response',
            'apigateway.create-deployment',
        ]
        # source_arn del add-permission usa wildcard de metodo `*`.
        add_call = next(
            c for c in calls if c[:2] == ['lambda', 'add-permission']
        )
        arn = add_call[add_call.index('--source-arn') + 1]
        assert arn.endswith('/dev/*/auth')
        # Access-Control-Allow-Methods lista GET,POST,OPTIONS.
        intgr_resp = next(
            c
            for c in calls
            if c[:2] == ['apigateway', 'put-integration-response']
        )
        params = intgr_resp[intgr_resp.index('--response-parameters') + 1]
        assert "'GET,POST,OPTIONS'" in params
        # Access-Control-Allow-Headers del preflight incluye Authorization
        # (los endpoints autenticados mandan el Bearer JWT). Sin el, el
        # browser bloquea el request con CORS.
        assert 'Authorization' in params

    def test_provision_create_snap_start_remove_add_use_qualifier(
        self, monkeypatch
    ):
        """Con snap_start, remove-permission Y add-permission van al alias.

        Regresion real (dev): el remove-permission SIN --qualifier borraba
        el statement del $LATEST (vacio) y dejaba el del alias `live`
        intacto; add-permission --qualifier live no lo sobrescribia (Sid
        ya existe) -> quedaba el SourceArn viejo y el GET sin permiso.
        """
        from serverless import provisioner
        from serverless.aws_cli import AwsResult
        from serverless.state import Action

        calls = []
        responses = _default_responses()

        def fake(args, **_kwargs):
            calls.append(args)
            key = '.'.join(args[:2])
            # SnapStart: publish-version retorna Version; get-alias falla
            # (ResourceNotFound) para forzar create-alias.
            if key == 'lambda.publish-version':
                return AwsResult(
                    returncode=0, stdout='', stderr='', json={'Version': '7'}
                )
            if key == 'lambda.get-alias':
                return AwsResult(
                    returncode=1, stdout='', stderr='not found', json=None
                )
            return AwsResult(
                returncode=0, stdout='', stderr='', json=responses.get(key)
            )

        monkeypatch.setattr(provisioner, 'aws', fake)
        monkeypatch.setattr(provisioner.time, 'sleep', lambda _s: None)

        manifest = _manifest_http()
        manifest['snap_start'] = True
        rendered = provisioner.render(manifest, stage='dev')
        provisioner.provision(
            rendered,
            action=Action.CREATE,
            zip_path=_ZIP_PATH,
            previous=None,
            profile=None,
            region='us-east-1',
        )

        remove_call = next(
            c for c in calls if c[:2] == ['lambda', 'remove-permission']
        )
        add_call = next(
            c for c in calls if c[:2] == ['lambda', 'add-permission']
        )
        # Ambos llevan --qualifier live y el mismo statement-id -live.
        assert '--qualifier' in remove_call
        assert remove_call[remove_call.index('--qualifier') + 1] == 'live'
        assert remove_call[remove_call.index('--statement-id') + 1] == (
            'apigw-dev-live'
        )
        assert '--qualifier' in add_call
        assert add_call[add_call.index('--qualifier') + 1] == 'live'

    def test_provision_update_config_disables_snap_start_and_purges(
        self, monkeypatch
    ):
        """snap_start=False en UPDATE_CONFIG apaga SnapStart y libera snapshots.

        Tras re-apuntar el trigger a $LATEST, `_disable_snap_start`:
        1. update-function-configuration --snap-start ApplyOn=None (porque
           la funcion AUN tiene PublishedVersions activo).
        2. delete-alias del alias `live`.
        3. delete-function --qualifier de cada version publicada que NINGUN
           alias referencie (aqui: 1, 2 y 3; ninguna aliased tras el
           delete-alias).
        """
        from serverless import provisioner
        from serverless.aws_cli import AwsResult
        from serverless.state import Action
        from serverless.state import LambdaState

        calls = []
        responses = _default_responses()

        def fake(args, **_kwargs):
            calls.append(args)
            key = '.'.join(args[:2])
            if key == 'lambda.get-function-configuration':
                # SnapStart sigue activo -> el update a None NO es no-op.
                return AwsResult(
                    returncode=0,
                    stdout='',
                    stderr='',
                    json={'SnapStart': {'ApplyOn': 'PublishedVersions'}},
                )
            if key == 'lambda.list-aliases':
                # Ningun alias queda (el live ya se borro).
                return AwsResult(returncode=0, stdout='', stderr='', json=[])
            if key == 'lambda.list-versions-by-function':
                # $LATEST + 3 versiones publicadas con snapshot.
                return AwsResult(
                    returncode=0,
                    stdout='',
                    stderr='',
                    json=['$LATEST', '1', '2', '3'],
                )
            return AwsResult(
                returncode=0, stdout='', stderr='', json=responses.get(key)
            )

        monkeypatch.setattr(provisioner, 'aws', fake)
        monkeypatch.setattr(provisioner.time, 'sleep', lambda _s: None)

        # _manifest_http NO define snap_start -> render lo deja en False.
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

        # 1. SnapStart apagado: update-function-configuration con ApplyOn=None.
        snap_update = next(
            c
            for c in calls
            if c[:2] == ['lambda', 'update-function-configuration']
            and '--snap-start' in c
        )
        assert snap_update[snap_update.index('--snap-start') + 1] == (
            'ApplyOn=None'
        )
        # 2. Alias `live` borrado.
        delete_alias = next(
            c for c in calls if c[:2] == ['lambda', 'delete-alias']
        )
        assert delete_alias[delete_alias.index('--name') + 1] == 'live'
        # 3. Las 3 versiones publicadas se borran ($LATEST NO).
        deleted_versions = sorted(
            c[c.index('--qualifier') + 1]
            for c in calls
            if c[:2] == ['lambda', 'delete-function'] and '--qualifier' in c
        )
        assert deleted_versions == ['1', '2', '3']

    def test_provision_create_records_resources(self, monkeypatch):
        from serverless import provisioner
        from serverless.state import Action

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

    def test_provision_create_reuses_existing_api_resource(self, monkeypatch):
        """Si /path ya existe en el API GW (re-corrida tras deploy parcial),
        reutilizar su id y NO llamar create-resource."""
        from serverless import provisioner
        from serverless.aws_cli import AwsResult
        from serverless.state import Action

        calls = []
        responses = _default_responses()
        # get-resources devuelve el id existente via stdout (text output).
        existing_resource_id = 'existing-res-id-42'

        def fake(args, **_kwargs):
            calls.append(args)
            key = '.'.join(args[:2])
            if key == 'apigateway.get-resources':
                return AwsResult(
                    returncode=0,
                    stdout=existing_resource_id,
                    stderr='',
                    json=None,
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
        state = provisioner.provision(
            rendered,
            action=Action.CREATE,
            zip_path=_ZIP_PATH,
            previous=None,
            profile=None,
            region='us-east-1',
        )

        verbs = ['.'.join(c[:2]) for c in calls]
        assert 'apigateway.get-resources' in verbs
        assert 'apigateway.create-resource' not in verbs
        assert state.resources['api_resource_id'] == existing_resource_id


class TestProvisionUpdate:
    """provision() con Action.UPDATE_* corre solo lo que cambio."""

    def test_provision_update_code_only_calls_update_function_code(
        self, monkeypatch
    ):
        from serverless import provisioner
        from serverless.state import Action
        from serverless.state import LambdaState

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
        assert verbs == [
            'lambda.wait',
            'lambda.update-function-code',
        ]

    def test_provision_update_config_calls_config_and_role_policy(
        self, monkeypatch
    ):
        from serverless import provisioner
        from serverless.state import Action
        from serverless.state import LambdaState

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
        # Post-fix: tras `_provision_update_config` ahora `provision()`
        # re-aplica el wiring del trigger (`_rewire_trigger_on_update`)
        # para que cambios de `trigger.*` o `snap_start` en el manifest
        # se materialicen en API GW (URI :live, statement-id correcto).
        # La secuencia del wiring es la misma que en CREATE (post `_create_function`).
        # Como el manifest test NO tiene snap_start (=False), tras el
        # rewire `provision()` llama `_disable_snap_start`: verifica la
        # config SnapStart (get-function-configuration; no-op porque ya
        # esta en None), borra el alias `live` (delete-alias) y purga las
        # versiones publicadas (list-aliases + list-versions-by-function;
        # 0 a borrar en el fake).
        assert verbs == [
            'sts.get-caller-identity',
            'iam.create-role',
            'iam.put-role-policy',
            'iam.attach-role-policy',
            'lambda.wait',
            'lambda.update-function-configuration',
            'sts.get-caller-identity',
            'ssm.get-parameter',
            'ssm.get-parameter',
            'apigateway.get-resources',
            'apigateway.create-resource',
            'apigateway.put-method',
            'apigateway.put-integration',
            'apigateway.put-method',
            'apigateway.put-integration',
            'apigateway.put-method-response',
            'apigateway.put-integration-response',
            'apigateway.create-deployment',
            'lambda.get-policy',
            'lambda.remove-permission',
            'lambda.add-permission',
            'lambda.get-function-configuration',
            'lambda.delete-alias',
            'lambda.list-aliases',
            'lambda.list-versions-by-function',
        ]
        assert 'lambda.create-function' not in verbs

        update_call = next(
            c
            for c in calls
            if c[:2] == ['lambda', 'update-function-configuration']
        )
        assert '--role' in update_call
        role_arn = update_call[update_call.index('--role') + 1]
        # _default_responses devuelve este ARN fijo para iam.create-role.
        assert role_arn == 'arn:aws:iam::111122223333:role/portfolio-x'

    def test_provision_update_both_runs_code_and_config(self, monkeypatch):
        from serverless import provisioner
        from serverless.state import Action
        from serverless.state import LambdaState

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
        # Post-fix: el wiring del trigger se re-aplica tambien en
        # UPDATE_BOTH para alinear API GW con el manifest actual. Como el
        # manifest test NO tiene snap_start (=False), tras el rewire se
        # llama `_disable_snap_start` (get-function-configuration no-op +
        # delete-alias + list-aliases + list-versions-by-function).
        assert verbs == [
            'lambda.wait',
            'lambda.update-function-code',
            'sts.get-caller-identity',
            'iam.create-role',
            'iam.put-role-policy',
            'iam.attach-role-policy',
            'lambda.wait',
            'lambda.update-function-configuration',
            'sts.get-caller-identity',
            'ssm.get-parameter',
            'ssm.get-parameter',
            'apigateway.get-resources',
            'apigateway.create-resource',
            'apigateway.put-method',
            'apigateway.put-integration',
            'apigateway.put-method',
            'apigateway.put-integration',
            'apigateway.put-method-response',
            'apigateway.put-integration-response',
            'apigateway.create-deployment',
            'lambda.get-policy',
            'lambda.remove-permission',
            'lambda.add-permission',
            'lambda.get-function-configuration',
            'lambda.delete-alias',
            'lambda.list-aliases',
            'lambda.list-versions-by-function',
        ]

    def test_provision_update_config_cleans_sam_legacy_permission(
        self, monkeypatch
    ):
        """
        Given un Lambda con statement-id legacy de SAM en su policy
            (Sid `portfolio-backend-dev-...PermissionDev-XYZ`, mismo
            source_arn que el target),
        When provision() corre con Action.UPDATE_CONFIG (re-aplica el
            wiring del trigger via `_rewire_trigger_on_update`),
        Then remove-permission borra el statement legacy ANTES del
            add-permission del statement canonico (`apigw-dev`).
        """
        import json as _json

        from serverless import provisioner
        from serverless.aws_cli import AwsResult
        from serverless.state import Action
        from serverless.state import LambdaState

        # Arrange: policy con UN solo statement legacy de SAM, scoped al
        # mismo source_arn que devtools ensamblara para `POST /contact`.
        api_id = 'api-abc123'
        source_arn = (
            f'arn:aws:execute-api:us-east-1:111122223333:{api_id}'
            '/dev/POST/contact'
        )
        legacy_sid = (
            'portfolio-backend-dev-ContactFormFunctionPostContactPermission'
            'Dev-GyamVaKP4q9J'
        )
        legacy_policy = _json.dumps(
            {
                'Statement': [
                    {
                        'Sid': legacy_sid,
                        'Effect': 'Allow',
                        'Principal': {'Service': 'apigateway.amazonaws.com'},
                        'Action': 'lambda:InvokeFunction',
                        'Resource': (
                            'arn:aws:lambda:us-east-1:111122223333:function:'
                            'portfolio-contact-form-dev'
                        ),
                        'Condition': {'ArnLike': {'AWS:SourceArn': source_arn}},
                    }
                ],
            }
        )

        calls = []
        responses = _default_responses()

        def fake(args, **_kwargs):
            calls.append(args)
            key = '.'.join(args[:2])
            if key == 'lambda.get-policy':
                # stdout (text output con --query/--output text)
                return AwsResult(
                    returncode=0,
                    stdout=legacy_policy,
                    stderr='',
                    json=None,
                )
            return AwsResult(
                returncode=0,
                stdout='',
                stderr='',
                json=responses.get(key),
            )

        monkeypatch.setattr(provisioner, 'aws', fake)

        rendered = provisioner.render(_manifest_http(), stage='dev')
        previous = LambdaState(
            scope='contact-form',
            stage='dev',
            config_hash='sha256:OLD',
            code_hash='sha256:k',
            resources={'function_name': 'portfolio-contact-form-dev'},
            updated_at='2026-05-21T10:00:00Z',
        )

        # Act
        provisioner.provision(
            rendered,
            action=Action.UPDATE_CONFIG,
            zip_path=_ZIP_PATH,
            previous=previous,
            profile=None,
            region='us-east-1',
        )

        # Assert: remove-permission del Sid legacy ocurre ANTES del add-permission canonico.
        verbs = ['.'.join(c[:2]) for c in calls]
        assert 'lambda.remove-permission' in verbs
        assert verbs.index('lambda.remove-permission') < verbs.index(
            'lambda.add-permission'
        )

        remove_call = next(
            c for c in calls if c[:2] == ['lambda', 'remove-permission']
        )
        assert '--statement-id' in remove_call
        sid_idx = remove_call.index('--statement-id') + 1
        assert remove_call[sid_idx] == legacy_sid

        add_call = next(
            c for c in calls if c[:2] == ['lambda', 'add-permission']
        )
        add_sid_idx = add_call.index('--statement-id') + 1
        # El manifest test NO tiene snap_start, asi que el target Sid es
        # `apigw-{stage}` sin sufijo `-live`.
        assert add_call[add_sid_idx] == 'apigw-dev'

    def test_provision_noop_makes_no_aws_calls(self, monkeypatch):
        from serverless import provisioner
        from serverless.state import Action
        from serverless.state import LambdaState

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
        from serverless import provisioner
        from serverless.aws_cli import AwsError
        from serverless.aws_cli import AwsResult
        from serverless.state import Action

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
        from serverless import provisioner
        from serverless.aws_cli import AwsResult
        from serverless.state import LambdaState

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


class TestBucketStatements:
    def test_bucket_statements_grant_get_object_and_list_bucket(self):
        """
        Given un uses.buckets con access read,
        When se traducen a Statements IAM,
        Then otorga s3:GetObject sobre las keys Y s3:ListBucket sobre el
        bucket (el restore del Lambda db lista el prefijo del snapshot).
        """
        from serverless.provisioner import _bucket_statements

        statements = _bucket_statements(
            [{'name': 'portfolio-db-backups-${stage}', 'access': 'read'}],
            'dev',
        )

        assert statements == [
            {
                'Effect': 'Allow',
                'Action': ['s3:GetObject'],
                'Resource': 'arn:aws:s3:::portfolio-db-backups-dev/*',
            },
            {
                'Effect': 'Allow',
                'Action': ['s3:ListBucket'],
                'Resource': 'arn:aws:s3:::portfolio-db-backups-dev',
            },
        ]
