"""Unit tests for serverless.infra_provision - render + provision de infra.

Path mirroring: devtools/serverless/infra_provision.py -> este archivo
(sin prefijo test_, convencion de devtools).

`render_resource` se prueba como funcion pura sobre fixtures YAML en
`tmp_path`. `provision_infra` / `deprovision_infra` se prueban con
`aws_cli.aws` y `aws_cli.aws_resource_exists` mockeados, capturando el
orden de las llamadas AWS CLI. Ningun test toca AWS de verdad.

Cubre AC-3.1..AC-3.7 de la Fase 3 (docs/specs/serverless-drop-sam).
"""

from pathlib import Path

import pytest


pytestmark = pytest.mark.unit


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def _write(path: Path, body: str) -> Path:
    """Escribe un fragmento YAML en `path` y devuelve la ruta."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding='utf-8')
    return path


def _dynamodb_fragment(*, with_stream: bool) -> str:
    """Fragmento YAML de una tabla DynamoDB (con o sin stream)."""
    stream = 'NEW_AND_OLD_IMAGES' if with_stream else 'null'
    stream_ssm = (
        '  stream_arn: /portfolio/${stage}/dynamodb/contacts/stream-arn\n'
        if with_stream
        else ''
    )
    return (
        'kind: dynamodb-table\n'
        'name: portfolio-contacts-${stage}\n'
        'billing_mode: PAY_PER_REQUEST\n'
        'hash_key: { name: id, type: S }\n'
        'range_key: null\n'
        f'stream: {stream}\n'
        'point_in_time_recovery: true\n'
        'encryption: true\n'
        'ttl_attribute: null\n'
        'publishes_ssm:\n'
        '  name: /portfolio/${stage}/dynamodb/contacts/name\n'
        '  arn: /portfolio/${stage}/dynamodb/contacts/arn\n'
        f'{stream_ssm}'
        'tags: { Project: portfolio, ManagedBy: devtools }\n'
    )


def _rest_api_fragment() -> str:
    """Fragmento YAML de la API Gateway REST."""
    return (
        'kind: rest-api\n'
        'name: portfolio-api-${stage}\n'
        'endpoint_type: REGIONAL\n'
        'access_log_group: /aws/apigateway/portfolio-api-${stage}\n'
        'access_log_retention_days: 7\n'
        'cloudwatch_role_name: portfolio-api-cwlogs-role-${stage}\n'
        'publishes_ssm:\n'
        '  id: /portfolio/${stage}/api_gateway/portfolio-api/id\n'
        '  root_resource_id: /portfolio/${stage}/api_gateway/'
        'portfolio-api/root-resource-id\n'
        '  access_log_group_arn: /portfolio/${stage}/api_gateway/'
        'portfolio-api/access-log-group-arn\n'
    )


def _sqs_fragment() -> str:
    """Fragmento YAML de la cola SQS."""
    return (
        'kind: sqs-queue\n'
        'name: portfolio-stream-processor-dlq-${stage}\n'
        'message_retention_seconds: 1209600\n'
        'publishes_ssm:\n'
        '  arn: /portfolio/${stage}/sqs/stream-processor-dlq/arn\n'
        '  url: /portfolio/${stage}/sqs/stream-processor-dlq/url\n'
    )


class _FakeAws:
    """Fake de `aws_cli.aws` que registra cada invocacion.

    `responses` mapea el verbo `service.action` (primeros dos args) a un
    dict JSON simulado. Si el valor es una lista, cada invocacion del
    verbo consume el siguiente elemento (respuestas secuenciales).
    """

    def __init__(self, responses=None):
        self.calls: list[list[str]] = []
        self.responses = responses or {}
        self._cursors: dict[str, int] = {}

    def __call__(self, args, **_kwargs):
        from serverless.aws_cli import AwsResult

        self.calls.append(args)
        key = '.'.join(args[:2])
        payload = self.responses.get(key)
        if isinstance(payload, list):
            index = self._cursors.get(key, 0)
            resolved = payload[min(index, len(payload) - 1)]
            self._cursors[key] = index + 1
            payload = resolved
        return AwsResult(
            returncode=0,
            stdout='',
            stderr='',
            json=payload,
        )


# --------------------------------------------------------------------------
# render_resource — funcion pura
# --------------------------------------------------------------------------
class TestRenderResource:
    """render_resource interpola ${stage} y valida el esquema."""

    def test_render_interpolates_stage(self, tmp_path):
        """
        Given un fragmento dynamodb-table con ${stage},
        When render_resource(stage='dev'),
        Then todos los ${stage} quedan interpolados a 'dev'. [AC-3.1]
        """
        from serverless import infra_provision

        path = _write(
            tmp_path / 'contacts.yaml',
            _dynamodb_fragment(with_stream=True),
        )

        rendered = infra_provision.render_resource(path, stage='dev')

        assert rendered.name == 'portfolio-contacts-dev'
        assert (
            rendered.publishes_ssm['name']
            == '/portfolio/dev/dynamodb/contacts/name'
        )
        assert (
            rendered.publishes_ssm['stream_arn']
            == '/portfolio/dev/dynamodb/contacts/stream-arn'
        )

    def test_render_dynamodb_table_with_stream(self, tmp_path):
        """
        Given un fragmento dynamodb-table con stream,
        When render_resource,
        Then el kind es dynamodb-table y el stream queda en el spec.
        """
        from serverless import infra_provision

        path = _write(
            tmp_path / 'contacts.yaml',
            _dynamodb_fragment(with_stream=True),
        )

        rendered = infra_provision.render_resource(path, stage='stage')

        assert rendered.kind == 'dynamodb-table'
        assert rendered.spec['stream'] == 'NEW_AND_OLD_IMAGES'
        assert rendered.spec['hash_key'] == {'name': 'id', 'type': 'S'}

    def test_render_rest_api_fields(self, tmp_path):
        """
        Given un fragmento rest-api,
        When render_resource,
        Then los campos del rol CloudWatch y log group estan presentes.
        """
        from serverless import infra_provision

        path = _write(tmp_path / 'portfolio-api.yaml', _rest_api_fragment())

        rendered = infra_provision.render_resource(path, stage='prod')

        assert rendered.kind == 'rest-api'
        assert rendered.name == 'portfolio-api-prod'
        assert (
            rendered.spec['cloudwatch_role_name']
            == 'portfolio-api-cwlogs-role-prod'
        )
        assert (
            rendered.spec['access_log_group']
            == '/aws/apigateway/portfolio-api-prod'
        )

    def test_render_sqs_queue_fields(self, tmp_path):
        """
        Given un fragmento sqs-queue,
        When render_resource,
        Then el kind es sqs-queue y la retencion queda en el spec.
        """
        from serverless import infra_provision

        path = _write(tmp_path / 'dlq.yaml', _sqs_fragment())

        rendered = infra_provision.render_resource(path, stage='dev')

        assert rendered.kind == 'sqs-queue'
        assert rendered.name == 'portfolio-stream-processor-dlq-dev'
        assert rendered.spec['message_retention_seconds'] == 1209600

    def test_render_rejects_unknown_kind(self, tmp_path):
        """
        Given un fragmento con kind invalido,
        When render_resource,
        Then lanza ValueError.
        """
        from serverless import infra_provision

        path = _write(
            tmp_path / 'bad.yaml',
            'kind: s3-bucket\nname: x-${stage}\n',
        )

        with pytest.raises(ValueError, match='kind invalido'):
            infra_provision.render_resource(path, stage='dev')


# --------------------------------------------------------------------------
# discover_resources
# --------------------------------------------------------------------------
class TestDiscoverResources:
    """discover_resources lista los fragmentos reales de resources/."""

    def test_discover_finds_four_resources(self):
        """
        Given los 4 fragmentos de serverless/lambda/resources/,
        When discover_resources,
        Then devuelve exactamente 4 paths y ninguno empieza con '_'.

        Cantidad post spec direct-neon-writes: 3 tablas DDB (cache +
        rate-limit-rules + rate-limit-buckets) + 1 API GW. Se eliminaron
        las tablas `contacts`/`tracking` y la SQS DLQ del stream_processor.
        """
        from serverless import infra_provision

        paths = infra_provision.discover_resources()

        assert len(paths) == 4
        assert all(not p.stem.startswith('_') for p in paths)


# --------------------------------------------------------------------------
# provision_infra — aws_cli mockeado
# --------------------------------------------------------------------------
class TestProvisionInfra:
    """provision_infra emite las llamadas AWS CLI y publica los SSM."""

    def test_provision_dynamodb_with_stream_publishes_ssm(
        self, tmp_path, monkeypatch
    ):
        """
        Given un kind dynamodb-table con stream,
        When provision_infra,
        Then se llama create-table con --stream-specification y se
        publica el stream_arn en SSM. [AC-3.2]
        """
        from serverless import aws_cli
        from serverless import infra_provision
        from serverless import state

        path = _write(
            tmp_path / 'contacts.yaml',
            _dynamodb_fragment(with_stream=True),
        )
        monkeypatch.setattr(
            infra_provision,
            'discover_resources',
            lambda: [path],
        )
        monkeypatch.setattr(state, 'STATE_DIR', tmp_path / '.state')

        fake = _FakeAws(
            {
                'dynamodb.create-table': {
                    'TableDescription': {
                        'TableArn': 'arn:aws:dynamodb:::table/contacts',
                        'LatestStreamArn': 'arn:aws:dynamodb:::stream/x',
                    },
                },
            },
        )
        monkeypatch.setattr(aws_cli, 'aws', fake)
        monkeypatch.setattr(
            aws_cli,
            'aws_resource_exists',
            lambda *_a, **_k: False,
        )

        infra = infra_provision.provision_infra(
            stage='dev',
            profile=None,
        )

        create_calls = [
            c for c in fake.calls if c[:2] == ['dynamodb', 'create-table']
        ]
        assert len(create_calls) == 1
        assert '--stream-specification' in create_calls[0]
        assert (
            '/portfolio/dev/dynamodb/contacts/stream-arn' in infra.ssm_published
        )

    def test_provision_skips_create_when_table_exists(
        self, tmp_path, monkeypatch
    ):
        """
        Given una tabla que ya existe,
        When provision_infra,
        Then NO se llama create-table, solo se re-publican los SSM.
        [AC-3.3]
        """
        from serverless import aws_cli
        from serverless import infra_provision
        from serverless import state

        path = _write(
            tmp_path / 'contacts.yaml',
            _dynamodb_fragment(with_stream=False),
        )
        monkeypatch.setattr(
            infra_provision,
            'discover_resources',
            lambda: [path],
        )
        monkeypatch.setattr(state, 'STATE_DIR', tmp_path / '.state')

        fake = _FakeAws(
            {
                'dynamodb.describe-table': {
                    'Table': {
                        'TableArn': 'arn:aws:dynamodb:::table/contacts',
                        'LatestStreamArn': None,
                    },
                },
            },
        )
        monkeypatch.setattr(aws_cli, 'aws', fake)
        monkeypatch.setattr(
            aws_cli,
            'aws_resource_exists',
            lambda *_a, **_k: True,
        )

        infra = infra_provision.provision_infra(
            stage='dev',
            profile=None,
        )

        create_calls = [
            c for c in fake.calls if c[:2] == ['dynamodb', 'create-table']
        ]
        assert create_calls == []
        assert '/portfolio/dev/dynamodb/contacts/name' in infra.ssm_published

    def test_provision_rest_api_creates_role_loggroup_api_ssm(
        self, tmp_path, monkeypatch
    ):
        """
        Given un kind rest-api,
        When provision_infra,
        Then se crea el rol CloudWatch, el log group, la REST API y se
        publican los 3 SSM. [AC-3.4]
        """
        from serverless import aws_cli
        from serverless import infra_provision
        from serverless import state

        path = _write(
            tmp_path / 'portfolio-api.yaml',
            _rest_api_fragment(),
        )
        monkeypatch.setattr(
            infra_provision,
            'discover_resources',
            lambda: [path],
        )
        monkeypatch.setattr(state, 'STATE_DIR', tmp_path / '.state')

        fake = _FakeAws(
            {
                'iam.get-role': {
                    'Role': {'Arn': 'arn:aws:iam:::role/cwlogs'},
                },
                'apigateway.create-rest-api': {'id': 'api123'},
                'apigateway.get-rest-apis': {'items': []},
                'apigateway.get-resources': {
                    'items': [{'path': '/', 'id': 'root1'}],
                },
                'logs.describe-log-groups': [
                    # 1a llamada: el log group no existe -> se crea.
                    {'logGroups': []},
                    # 2a llamada: ya creado -> se resuelve su ARN.
                    {
                        'logGroups': [
                            {
                                'logGroupName': (
                                    '/aws/apigateway/portfolio-api-dev'
                                ),
                                'arn': 'arn:aws:logs:::log-group/api',
                            },
                        ],
                    },
                ],
            },
        )
        monkeypatch.setattr(aws_cli, 'aws', fake)
        monkeypatch.setattr(
            aws_cli,
            'aws_resource_exists',
            lambda *_a, **_k: False,
        )

        infra = infra_provision.provision_infra(
            stage='dev',
            profile=None,
        )

        verbs = ['.'.join(c[:2]) for c in fake.calls]
        assert 'iam.create-role' in verbs
        assert 'logs.create-log-group' in verbs
        assert 'apigateway.create-rest-api' in verbs
        assert len(infra.ssm_published) == 3

    def test_provision_is_idempotent(self, tmp_path, monkeypatch):
        """
        Given provision_infra corrida dos veces seguidas,
        When termina la segunda,
        Then no hubo errores y el estado es consistente. [AC-3.6]
        """
        from serverless import aws_cli
        from serverless import infra_provision
        from serverless import state

        path = _write(
            tmp_path / 'dlq.yaml',
            _sqs_fragment(),
        )
        monkeypatch.setattr(
            infra_provision,
            'discover_resources',
            lambda: [path],
        )
        monkeypatch.setattr(state, 'STATE_DIR', tmp_path / '.state')

        fake = _FakeAws(
            {
                'sqs.get-queue-url': {
                    'QueueUrl': 'https://sqs/portfolio-dlq',
                },
                'sqs.get-queue-attributes': {
                    'Attributes': {'QueueArn': 'arn:aws:sqs:::dlq'},
                },
            },
        )
        monkeypatch.setattr(aws_cli, 'aws', fake)
        monkeypatch.setattr(
            aws_cli,
            'aws_resource_exists',
            lambda *_a, **_k: True,
        )

        first = infra_provision.provision_infra(stage='dev', profile=None)
        second = infra_provision.provision_infra(stage='dev', profile=None)

        assert first.resources == second.resources
        assert second.ssm_published == [
            '/portfolio/dev/sqs/stream-processor-dlq/arn',
            '/portfolio/dev/sqs/stream-processor-dlq/url',
        ]

    def test_provision_dry_run_does_not_touch_aws(self, tmp_path, monkeypatch):
        """
        Given dry_run=True,
        When provision_infra,
        Then no se llama a aws() y no se escribe estado.
        """
        from serverless import aws_cli
        from serverless import infra_provision
        from serverless import state

        path = _write(
            tmp_path / 'contacts.yaml',
            _dynamodb_fragment(with_stream=True),
        )
        monkeypatch.setattr(
            infra_provision,
            'discover_resources',
            lambda: [path],
        )
        monkeypatch.setattr(state, 'STATE_DIR', tmp_path / '.state')

        fake = _FakeAws()
        monkeypatch.setattr(aws_cli, 'aws', fake)

        infra_provision.provision_infra(
            stage='dev',
            profile=None,
            dry_run=True,
        )

        assert fake.calls == []
        assert not (tmp_path / '.state' / 'infra-dev.json').exists()


# --------------------------------------------------------------------------
# deprovision_infra
# --------------------------------------------------------------------------
class TestDeprovisionInfra:
    """deprovision_infra borra en orden inverso y limpia el estado."""

    def test_deprovision_reverse_order(self, tmp_path, monkeypatch):
        """
        Given infra desplegada (3 kinds),
        When deprovision_infra,
        Then se borran API, tabla y DLQ en orden inverso y el
        .state/infra-<stage>.json se vacia. [AC-3.5]
        """
        from serverless import aws_cli
        from serverless import infra_provision
        from serverless import state

        sqs = _write(tmp_path / 'sqs' / 'dlq.yaml', _sqs_fragment())
        table = _write(
            tmp_path / 'dynamodb' / 'contacts.yaml',
            _dynamodb_fragment(with_stream=True),
        )
        api = _write(
            tmp_path / 'api_gateway' / 'portfolio-api.yaml',
            _rest_api_fragment(),
        )
        monkeypatch.setattr(
            infra_provision,
            'discover_resources',
            lambda: [sqs, table, api],
        )
        monkeypatch.setattr(state, 'STATE_DIR', tmp_path / '.state')

        # Estado previo de la infra a destruir.
        state.save_state(
            state.LambdaState(
                scope='infra',
                stage='dev',
                config_hash='sha256:x',
                code_hash='sha256:empty',
                resources={},
                updated_at='2026-05-21T10:00:00Z',
            ),
        )

        fake = _FakeAws(
            {
                'sqs.get-queue-url': {'QueueUrl': 'https://sqs/dlq'},
                'apigateway.get-rest-apis': {
                    'items': [
                        {'name': 'portfolio-api-dev', 'id': 'api123'},
                    ],
                },
            },
        )
        monkeypatch.setattr(aws_cli, 'aws', fake)

        infra_provision.deprovision_infra(stage='dev', profile=None)

        delete_verbs = [
            '.'.join(c[:2]) for c in fake.calls if c[1].startswith('delete')
        ]
        assert delete_verbs == [
            'apigateway.delete-rest-api',
            'dynamodb.delete-table',
            'sqs.delete-queue',
        ]
        assert not (tmp_path / '.state' / 'infra-dev.json').exists()
