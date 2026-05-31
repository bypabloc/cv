"""Provision de los recursos compartidos del backend serverless (sin SAM).

Reemplaza `infra_deploy.py`. Antes la infra compartida (tablas DynamoDB,
API Gateway REST, DLQ SQS) se deployaba como stacks CloudFormation
autonomos. Tras la migracion sin SAM, devtools lee cada fragmento de
`serverless/lambda/resources/` — ahora en un esquema plano propio, sin
`Transform`/`Fn::Sub`/`Ref` — y emite las llamadas AWS CLI directas para
crear cada recurso, mas `aws ssm put-parameter` para publicar sus
identificadores (los Lambdas los leen en runtime).

Tres `kind` soportados:

  - `dynamodb-table` -> `aws dynamodb create-table` (+ `update-time-to-live`).
  - `rest-api`       -> rol CloudWatch + log group + `create-rest-api`.
  - `sqs-queue`      -> `aws sqs create-queue`.
  - `s3-bucket`      -> `aws s3api create-bucket` (+ public-access-block + SSE).

La idempotencia se reconcilia consultando AWS (`describe-*` / `get-*`):
si el recurso existe NO se recrea, solo se re-publican los SSM. El estado
de lo creado se guarda en `serverless/lambda/.state/infra-<stage>.json`
para el `deprovision`.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Any

from serverless import aws_cli
from serverless import state
from serverless.aws_cli import AwsError
from shared.console import CYAN
from shared.console import GREEN
from shared.console import YELLOW
from shared.console import _c
from shared.console import _err


# Raiz del backend serverless del portfolio.
_SERVERLESS_DIR = Path(__file__).resolve().parents[2] / 'serverless'

# Directorio de los fragmentos de recurso compartido.
_RESOURCES_DIR = _SERVERLESS_DIR / 'lambda' / 'resources'

# Subdirectorios de _RESOURCES_DIR que contienen fragmentos de recurso.
_RESOURCE_TYPES = ('sqs', 'dynamodb', 's3', 'api_gateway', 'cloudwatch_alarms')

# Region por defecto del backend.
_REGION = aws_cli.DEFAULT_REGION

# Scope del estado de la infra compartida.
_INFRA_SCOPE = 'infra'

# Managed policy ARN del rol CloudWatch de API Gateway.
_APIGW_CWLOGS_POLICY = (
    'arn:aws:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs'
)

# Orden de provision: SQS (DLQs primero, principales despues) -> tablas
# DynamoDB -> API Gateway -> alarmas CloudWatch (necesitan los ARNs SQS).
# El deprovision recorre la lista inversa.
_PROVISION_ORDER = (
    'sqs-queue',
    'dynamodb-table',
    's3-bucket',
    'rest-api',
    'cloudwatch-alarm',
)

# SQS bloquea recrear una cola con el mismo nombre por 60s tras borrarla
# (QueueDeletedRecently). El ciclo destroy + provision-infra reintenta.
_SQS_RECREATE_RETRIES = 5
_SQS_RECREATE_WAIT = 20


@dataclass(frozen=True)
class RenderedResource:
    """Un fragmento de recurso con los `${stage}` ya interpolados.

    Attributes
    ----------
    kind : str
        `dynamodb-table` | `rest-api` | `sqs-queue`.
    name : str
        Nombre fisico del recurso (con el stage interpolado).
    spec : dict[str, Any]
        Resto del fragmento con todos los `${stage}` interpolados.
    source : Path
        Ruta del fragmento YAML del que se renderizo.
    stage : str
        Entorno (`dev` | `stage` | `prod`); usado por providers que
        seleccionan config por stage (ej. `custom_domain_by_stage` del
        `rest-api`).
    """

    kind: str
    name: str
    spec: dict[str, Any]
    source: Path
    stage: str = ''

    @property
    def publishes_ssm(self) -> dict[str, str]:
        """Mapa atributo -> path SSM declarado en el fragmento."""
        return self.spec.get('publishes_ssm', {})

    @property
    def custom_domain(self) -> dict[str, Any] | None:
        """Config del custom domain del stage actual, o None.

        Lee `custom_domain_by_stage[<stage>]` del spec. El bloque trae
        `domain_name`, `endpoint_type` (`EDGE` | `REGIONAL`),
        `certificate_arn`, y opcionalmente `base_path_mappings`.
        """
        by_stage = self.spec.get('custom_domain_by_stage')
        if not isinstance(by_stage, dict):
            return None
        config = by_stage.get(self.stage)
        if not isinstance(config, dict):
            return None
        return config


@dataclass
class InfraState:
    """Resultado de un `provision_infra`.

    Attributes
    ----------
    stage : str
        Entorno aprovisionado.
    resources : dict[str, str | None]
        Identificadores de lo creado/reconciliado (claves planas).
    ssm_published : list[str]
        Paths SSM publicados durante la provision.
    """

    stage: str
    resources: dict[str, str | None] = field(default_factory=dict)
    ssm_published: list[str] = field(default_factory=list)


# --------------------------------------------------------------------------
# Descubrimiento + render
# --------------------------------------------------------------------------
def discover_resources() -> list[Path]:
    """Lista los `*.yaml` de `serverless/lambda/resources/`.

    Recorre los subdirectorios conocidos (`sqs/`, `dynamodb/`,
    `api_gateway/`) y devuelve los fragmentos, excluyendo cualquier
    archivo cuyo nombre empiece con `_` (ej. el viejo `_header.yaml`).

    Returns
    -------
    list[Path]
        Rutas de los fragmentos, ordenadas por tipo de recurso y nombre.
    """
    found: list[Path] = []
    for resource_type in _RESOURCE_TYPES:
        directory = _RESOURCES_DIR / resource_type
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob('*.yaml')):
            if path.stem.startswith('_'):
                continue
            found.append(path)
    return found


def _interpolate(value: Any, stage: str) -> Any:
    """Reemplaza recursivamente `${stage}` por `stage` en strings.

    Parameters
    ----------
    value : Any
        Valor del fragmento (str, dict, list o escalar).
    stage : str
        Valor a interpolar.

    Returns
    -------
    Any
        El mismo valor con los `${stage}` reemplazados.
    """
    if isinstance(value, str):
        return value.replace('${stage}', stage)
    if isinstance(value, dict):
        return {k: _interpolate(v, stage) for k, v in value.items()}
    if isinstance(value, list):
        return [_interpolate(item, stage) for item in value]
    return value


def render_resource(path: Path, *, stage: str) -> RenderedResource:
    """Funcion pura: fragmento YAML -> `RenderedResource` interpolado.

    Parameters
    ----------
    path : Path
        Ruta del fragmento YAML (esquema devtools, con `kind`).
    stage : str
        Entorno; reemplaza cada `${stage}` del fragmento.

    Returns
    -------
    RenderedResource
        El fragmento con todos los `${stage}` interpolados.

    Raises
    ------
    ValueError
        Si el fragmento no declara `kind` o `name`, o el `kind` no es
        uno de los tres soportados.
    """
    import yaml

    raw = yaml.safe_load(path.read_text(encoding='utf-8'))
    if not isinstance(raw, dict):
        # configuracion del repo, no de tipo de argumento. La API publica
        # documenta ValueError y cmd_provision_infra lo captura.
        raise ValueError(  # noqa: TRY004
            f'El fragmento {path} no es un mapa YAML valido.',
        )

    interpolated: dict[str, Any] = _interpolate(raw, stage)

    kind = interpolated.get('kind')
    if kind not in {
        'dynamodb-table',
        'rest-api',
        'sqs-queue',
        's3-bucket',
        'cloudwatch-alarm',
    }:
        raise ValueError(
            f'kind invalido en {path}: {kind!r}. Validos: '
            f'dynamodb-table, rest-api, sqs-queue, s3-bucket, '
            f'cloudwatch-alarm.',
        )

    name = interpolated.get('name')
    if not isinstance(name, str) or not name:
        raise ValueError(f'El fragmento {path} no declara un `name`.')

    spec = {k: v for k, v in interpolated.items() if k != 'kind'}
    return RenderedResource(
        kind=kind,
        name=name,
        spec=spec,
        source=path,
        stage=stage,
    )


# --------------------------------------------------------------------------
# Provision por kind
# --------------------------------------------------------------------------
def _put_ssm(
    name: str,
    value: str,
    *,
    profile: str | None,
    region: str,
    dry_run: bool,
) -> None:
    """Publica un SSM Parameter (String) idempotentemente."""
    if dry_run:
        print(_c(YELLOW, f'[dry-run] ssm put-parameter {name}'))
        return
    aws_cli.aws(
        [
            'ssm',
            'put-parameter',
            '--name',
            name,
            '--type',
            'String',
            '--value',
            value,
            '--overwrite',
        ],
        profile=profile,
        region=region,
    )


def _publish_ssm(
    rendered: RenderedResource,
    values: dict[str, str | None],
    *,
    profile: str | None,
    region: str,
    dry_run: bool,
) -> list[str]:
    """Publica los SSM declarados en `publishes_ssm` del fragmento.

    En provision real solo publica los atributos cuyo valor fue resuelto
    (no None). En dry-run lista TODOS los paths declarados (el valor no
    se conoce sin consultar AWS).

    Returns
    -------
    list[str]
        Paths SSM publicados (o, en dry-run, los que se publicarian).
    """
    published: list[str] = []
    for attribute, ssm_path in rendered.publishes_ssm.items():
        value = values.get(attribute)
        if value is None and not dry_run:
            continue
        _put_ssm(
            ssm_path,
            value if value is not None else '<resuelto-en-runtime>',
            profile=profile,
            region=region,
            dry_run=dry_run,
        )
        published.append(ssm_path)
    return published


def _provision_dynamodb_table(
    rendered: RenderedResource,
    *,
    profile: str | None,
    region: str,
    dry_run: bool,
) -> tuple[dict[str, str | None], list[str]]:
    """Provisiona una tabla DynamoDB. Idempotente.

    Si la tabla ya existe (`describe-table` retorna 0) NO se recrea: solo
    se re-publican los SSM. Si no existe, se llama `create-table` y, si el
    fragmento declara `ttl_attribute`, `update-time-to-live`.
    """
    spec = rendered.spec
    table_name = rendered.name

    exists = (
        False
        if dry_run
        else aws_cli.aws_resource_exists(
            'dynamodb',
            ['describe-table', '--table-name', table_name],
            profile=profile,
            region=region,
        )
    )

    if exists:
        print(_c(CYAN, f'  tabla {table_name} ya existe — no se recrea'))
        table_arn, stream_arn = _describe_dynamodb_ids(
            table_name,
            profile=profile,
            region=region,
        )
    elif dry_run:
        print(_c(YELLOW, f'[dry-run] dynamodb create-table {table_name}'))
        table_arn = None
        stream_arn = None
    else:
        table_arn, stream_arn = _create_dynamodb_table(
            rendered,
            profile=profile,
            region=region,
        )

    values: dict[str, str | None] = {
        'name': table_name,
        'arn': table_arn,
        'stream_arn': stream_arn,
    }
    published = _publish_ssm(
        rendered,
        values,
        profile=profile,
        region=region,
        dry_run=dry_run,
    )
    resources: dict[str, str | None] = {
        f'dynamodb:{table_name}:name': table_name,
        f'dynamodb:{table_name}:arn': table_arn,
    }
    if 'stream' in spec and spec.get('stream'):
        resources[f'dynamodb:{table_name}:stream_arn'] = stream_arn
    return resources, published


def _build_create_table_args(rendered: RenderedResource) -> list[str]:
    """Arma los args de `aws dynamodb create-table` desde el fragmento."""
    spec = rendered.spec
    hash_key = spec['hash_key']
    range_key = spec.get('range_key')

    # Acumulamos los attribute definitions con un dict para deduplicar:
    # el GSI puede compartir attribute con la PK o agregar uno nuevo.
    attribute_defs_by_name: dict[str, dict[str, str]] = {
        hash_key['name']: {
            'AttributeName': hash_key['name'],
            'AttributeType': hash_key['type'],
        },
    }
    key_schema = [{'AttributeName': hash_key['name'], 'KeyType': 'HASH'}]
    if range_key:
        attribute_defs_by_name[range_key['name']] = {
            'AttributeName': range_key['name'],
            'AttributeType': range_key['type'],
        }
        key_schema.append(
            {'AttributeName': range_key['name'], 'KeyType': 'RANGE'},
        )

    # Global Secondary Indexes (opcional). Cada GSI declara su hash_key
    # (+ range_key opcional) y la projection (KEYS_ONLY / ALL / INCLUDE).
    # En PAY_PER_REQUEST no se declara ProvisionedThroughput.
    gsis_input = spec.get('global_secondary_indexes') or []
    gsis_aws: list[dict[str, object]] = []
    for gsi in gsis_input:
        gsi_hash = gsi['hash_key']
        attribute_defs_by_name.setdefault(
            gsi_hash['name'],
            {
                'AttributeName': gsi_hash['name'],
                'AttributeType': gsi_hash['type'],
            },
        )
        gsi_key_schema = [
            {'AttributeName': gsi_hash['name'], 'KeyType': 'HASH'},
        ]
        gsi_range = gsi.get('range_key')
        if gsi_range:
            attribute_defs_by_name.setdefault(
                gsi_range['name'],
                {
                    'AttributeName': gsi_range['name'],
                    'AttributeType': gsi_range['type'],
                },
            )
            gsi_key_schema.append(
                {'AttributeName': gsi_range['name'], 'KeyType': 'RANGE'},
            )
        projection_type = gsi.get('projection', 'KEYS_ONLY')
        projection: dict[str, object] = {'ProjectionType': projection_type}
        if projection_type == 'INCLUDE':
            projection['NonKeyAttributes'] = gsi.get('non_key_attributes', [])
        gsis_aws.append(
            {
                'IndexName': gsi['name'],
                'KeySchema': gsi_key_schema,
                'Projection': projection,
            },
        )

    import json as _json

    args = [
        'dynamodb',
        'create-table',
        '--table-name',
        rendered.name,
        '--billing-mode',
        spec.get('billing_mode', 'PAY_PER_REQUEST'),
        '--attribute-definitions',
        _json.dumps(list(attribute_defs_by_name.values())),
        '--key-schema',
        _json.dumps(key_schema),
    ]
    if gsis_aws:
        args += ['--global-secondary-indexes', _json.dumps(gsis_aws)]
    if spec.get('stream'):
        args += [
            '--stream-specification',
            f'StreamEnabled=true,StreamViewType={spec["stream"]}',
        ]
    if spec.get('encryption'):
        args += ['--sse-specification', 'Enabled=true']
    return args


def _create_dynamodb_table(
    rendered: RenderedResource,
    *,
    profile: str | None,
    region: str,
) -> tuple[str | None, str | None]:
    """Llama `create-table` (+ `update-time-to-live`) y devuelve los ARNs."""
    print(_c(YELLOW, f'  creando tabla {rendered.name}...'))
    result = aws_cli.aws(
        _build_create_table_args(rendered),
        profile=profile,
        region=region,
        parse_json=True,
    )
    description = (result.json or {}).get('TableDescription', {})
    table_arn = description.get('TableArn')
    stream_arn = description.get('LatestStreamArn')

    ttl_attribute = rendered.spec.get('ttl_attribute')
    if ttl_attribute:
        aws_cli.aws(
            [
                'dynamodb',
                'update-time-to-live',
                '--table-name',
                rendered.name,
                '--time-to-live-specification',
                f'Enabled=true,AttributeName={ttl_attribute}',
            ],
            profile=profile,
            region=region,
            check=False,
        )
    print(_c(GREEN, f'  OK  tabla {rendered.name} creada'))
    return table_arn, stream_arn


def _describe_dynamodb_ids(
    table_name: str,
    *,
    profile: str | None,
    region: str,
) -> tuple[str | None, str | None]:
    """Devuelve (table_arn, stream_arn) de una tabla existente."""
    result = aws_cli.aws(
        ['dynamodb', 'describe-table', '--table-name', table_name],
        profile=profile,
        region=region,
        parse_json=True,
        check=False,
    )
    description = (result.json or {}).get('Table', {})
    return description.get('TableArn'), description.get('LatestStreamArn')


def _provision_sqs_queue(
    rendered: RenderedResource,
    *,
    profile: str | None,
    region: str,
    dry_run: bool,
) -> tuple[dict[str, str | None], list[str]]:
    """Provisiona una cola SQS. Idempotente via `get-queue-url`.

    Tras crear/reusar la cola, aplica via `set-queue-attributes` los
    bloques opcionales `visibility_timeout_seconds` y `redrive_policy`
    (DLQ wiring). El RedrivePolicy resuelve el ARN de la DLQ por nombre
    en runtime con `get-queue-url` + `get-queue-attributes` — la DLQ
    debe existir antes (las DLQs van primero en `_ordered_rendered`).
    """
    queue_name = rendered.name

    if dry_run:
        print(_c(YELLOW, f'[dry-run] sqs create-queue {queue_name}'))
        if rendered.spec.get('redrive_policy'):
            print(
                _c(
                    YELLOW,
                    f'[dry-run] sqs set-queue-attributes {queue_name} '
                    f'(redrive_policy + visibility_timeout)',
                )
            )
        queue_url: str | None = None
        queue_arn: str | None = None
    else:
        queue_url = _resolve_queue_url(
            queue_name,
            profile=profile,
            region=region,
        )
        if queue_url is None:
            queue_url = _create_sqs_queue(
                rendered,
                profile=profile,
                region=region,
            )
        else:
            print(_c(CYAN, f'  cola {queue_name} ya existe — se reutiliza'))
        queue_arn = _describe_queue_arn(
            queue_url,
            profile=profile,
            region=region,
        )
        _apply_sqs_attributes(
            rendered,
            queue_url,
            profile=profile,
            region=region,
        )

    values: dict[str, str | None] = {'arn': queue_arn, 'url': queue_url}
    published = _publish_ssm(
        rendered,
        values,
        profile=profile,
        region=region,
        dry_run=dry_run,
    )
    resources: dict[str, str | None] = {
        f'sqs:{queue_name}:url': queue_url,
        f'sqs:{queue_name}:arn': queue_arn,
    }
    return resources, published


def _apply_sqs_attributes(
    rendered: RenderedResource,
    queue_url: str,
    *,
    profile: str | None,
    region: str,
) -> None:
    """Aplica `VisibilityTimeout` + `RedrivePolicy` via set-queue-attributes.

    Idempotente: AWS hace diff internamente y solo aplica si cambia.
    Si el spec no declara ninguno de los dos, NO se llama (set-queue-
    attributes con dict vacio falla).
    """
    import json as _json

    spec = rendered.spec
    attributes: dict[str, str] = {}

    visibility = spec.get('visibility_timeout_seconds')
    if visibility is not None:
        attributes['VisibilityTimeout'] = str(visibility)

    redrive = spec.get('redrive_policy')
    if redrive:
        dlq_name = redrive['target']
        dlq_url = _resolve_queue_url(
            dlq_name,
            profile=profile,
            region=region,
        )
        if dlq_url is None:
            raise RuntimeError(
                f'DLQ {dlq_name!r} no existe — debe provisionarse antes '
                f'que la cola principal {rendered.name!r}. Revisar el '
                f'orden de _ordered_rendered (DLQs primero).'
            )
        dlq_arn = _describe_queue_arn(
            dlq_url,
            profile=profile,
            region=region,
        )
        attributes['RedrivePolicy'] = _json.dumps(
            {
                'deadLetterTargetArn': dlq_arn,
                'maxReceiveCount': redrive.get('max_receive_count', 3),
            }
        )

    if not attributes:
        return

    aws_cli.aws(
        [
            'sqs',
            'set-queue-attributes',
            '--queue-url',
            queue_url,
            '--attributes',
            _json.dumps(attributes),
        ],
        profile=profile,
        region=region,
    )
    print(_c(GREEN, f'  OK  atributos aplicados a {rendered.name}'))


def _resolve_queue_url(
    queue_name: str,
    *,
    profile: str | None,
    region: str,
) -> str | None:
    """Devuelve la URL de una cola si existe, o None."""
    result = aws_cli.aws(
        ['sqs', 'get-queue-url', '--queue-name', queue_name],
        profile=profile,
        region=region,
        parse_json=True,
        check=False,
    )
    if not result.ok:
        return None
    return (result.json or {}).get('QueueUrl')


def _create_sqs_queue(
    rendered: RenderedResource,
    *,
    profile: str | None,
    region: str,
) -> str | None:
    """Llama `aws sqs create-queue` y devuelve la URL creada.

    SQS no permite recrear una cola con el mismo nombre dentro de los 60
    segundos posteriores a su borrado (`QueueDeletedRecently`). Para que
    el ciclo `destroy` + `provision-infra` no falle, ante ese error se
    espera y se reintenta.
    """
    import time

    print(_c(YELLOW, f'  creando cola {rendered.name}...'))
    retention = rendered.spec.get('message_retention_seconds', 1209600)
    args = [
        'sqs',
        'create-queue',
        '--queue-name',
        rendered.name,
        '--attributes',
        f'MessageRetentionPeriod={retention}',
    ]
    for attempt in range(_SQS_RECREATE_RETRIES):
        try:
            result = aws_cli.aws(
                args, profile=profile, region=region, parse_json=True
            )
        except aws_cli.AwsError as exc:
            last = attempt == _SQS_RECREATE_RETRIES - 1
            if 'QueueDeletedRecently' in exc.stderr and not last:
                print(
                    _c(
                        YELLOW,
                        f'  cola borrada hace poco — reintento en '
                        f'{_SQS_RECREATE_WAIT}s...',
                    ),
                )
                time.sleep(_SQS_RECREATE_WAIT)
                continue
            raise
        print(_c(GREEN, f'  OK  cola {rendered.name} creada'))
        return (result.json or {}).get('QueueUrl')
    return None


def _describe_queue_arn(
    queue_url: str | None,
    *,
    profile: str | None,
    region: str,
) -> str | None:
    """Devuelve el ARN de una cola dada su URL."""
    if queue_url is None:
        return None
    result = aws_cli.aws(
        [
            'sqs',
            'get-queue-attributes',
            '--queue-url',
            queue_url,
            '--attribute-names',
            'QueueArn',
        ],
        profile=profile,
        region=region,
        parse_json=True,
        check=False,
    )
    return (result.json or {}).get('Attributes', {}).get('QueueArn')


def _provision_rest_api(
    rendered: RenderedResource,
    *,
    profile: str | None,
    region: str,
    dry_run: bool,
) -> tuple[dict[str, str | None], list[str]]:
    """Provisiona la API Gateway REST. Idempotente.

    Crea el rol CloudWatch, asocia la cuenta de API Gateway, crea el log
    group y la REST API. Si la API ya existe (filtrando `get-rest-apis`
    por nombre) se reutiliza su Id.
    """
    spec = rendered.spec
    api_name = rendered.name

    if dry_run:
        print(
            _c(
                YELLOW,
                f'[dry-run] iam create-role {spec.get("cloudwatch_role_name")}',
            )
        )
        print(
            _c(
                YELLOW,
                f'[dry-run] logs create-log-group {spec.get("access_log_group")}',
            )
        )
        print(_c(YELLOW, f'[dry-run] apigateway create-rest-api {api_name}'))
        # Anunciar tambien el custom domain si esta declarado.
        _, _ = _ensure_custom_domain(
            rendered,
            api_id=None,
            profile=profile,
            region=region,
            dry_run=True,
        )
        values: dict[str, str | None] = {
            'id': None,
            'root_resource_id': None,
            'access_log_group_arn': None,
        }
        published = _publish_ssm(
            rendered,
            values,
            profile=profile,
            region=region,
            dry_run=dry_run,
        )
        return {}, published

    _ensure_cloudwatch_role(rendered, profile=profile, region=region)
    log_group_arn = _ensure_log_group(rendered, profile=profile, region=region)
    api_id, root_resource_id = _ensure_rest_api(
        rendered,
        profile=profile,
        region=region,
    )

    domain_resources, _ = _ensure_custom_domain(
        rendered,
        api_id=api_id,
        profile=profile,
        region=region,
        dry_run=False,
    )

    values = {
        'id': api_id,
        'root_resource_id': root_resource_id,
        'access_log_group_arn': log_group_arn,
    }
    published = _publish_ssm(
        rendered,
        values,
        profile=profile,
        region=region,
        dry_run=dry_run,
    )
    resources: dict[str, str | None] = {
        f'rest-api:{api_name}:id': api_id,
        f'rest-api:{api_name}:root_resource_id': root_resource_id,
        f'rest-api:{api_name}:access_log_group_arn': log_group_arn,
    }
    resources.update(domain_resources)
    return resources, published


def _ensure_cloudwatch_role(
    rendered: RenderedResource,
    *,
    profile: str | None,
    region: str,
) -> None:
    """Crea el rol CloudWatch de API Gateway y asocia la cuenta."""
    role_name = rendered.spec['cloudwatch_role_name']
    role_exists = aws_cli.aws_resource_exists(
        'iam',
        ['get-role', '--role-name', role_name],
        profile=profile,
        region=region,
    )
    if not role_exists:
        import json as _json

        assume_policy = {
            'Version': '2012-10-17',
            'Statement': [
                {
                    'Effect': 'Allow',
                    'Principal': {'Service': 'apigateway.amazonaws.com'},
                    'Action': 'sts:AssumeRole',
                },
            ],
        }
        print(_c(YELLOW, f'  creando rol CloudWatch {role_name}...'))
        aws_cli.aws(
            [
                'iam',
                'create-role',
                '--role-name',
                role_name,
                '--assume-role-policy-document',
                _json.dumps(assume_policy),
            ],
            profile=profile,
            region=region,
        )
        aws_cli.aws(
            [
                'iam',
                'attach-role-policy',
                '--role-name',
                role_name,
                '--policy-arn',
                _APIGW_CWLOGS_POLICY,
            ],
            profile=profile,
            region=region,
            check=False,
        )

    role_arn = _describe_role_arn(role_name, profile=profile, region=region)
    if role_arn:
        aws_cli.aws(
            [
                'apigateway',
                'update-account',
                '--patch-operations',
                f'op=replace,path=/cloudwatchRoleArn,value={role_arn}',
            ],
            profile=profile,
            region=region,
            check=False,
        )


def _describe_role_arn(
    role_name: str,
    *,
    profile: str | None,
    region: str,
) -> str | None:
    """Devuelve el ARN de un rol IAM dado su nombre."""
    result = aws_cli.aws(
        ['iam', 'get-role', '--role-name', role_name],
        profile=profile,
        region=region,
        parse_json=True,
        check=False,
    )
    return (result.json or {}).get('Role', {}).get('Arn')


def _ensure_log_group(
    rendered: RenderedResource,
    *,
    profile: str | None,
    region: str,
) -> str | None:
    """Crea el log group de access logs y devuelve su ARN."""
    log_group = rendered.spec['access_log_group']
    retention = rendered.spec.get('access_log_retention_days', 7)

    existing = aws_cli.aws(
        [
            'logs',
            'describe-log-groups',
            '--log-group-name-prefix',
            log_group,
        ],
        profile=profile,
        region=region,
        parse_json=True,
        check=False,
    )
    groups = (existing.json or {}).get('logGroups', [])
    if not any(g.get('logGroupName') == log_group for g in groups):
        print(_c(YELLOW, f'  creando log group {log_group}...'))
        aws_cli.aws(
            ['logs', 'create-log-group', '--log-group-name', log_group],
            profile=profile,
            region=region,
        )
        aws_cli.aws(
            [
                'logs',
                'put-retention-policy',
                '--log-group-name',
                log_group,
                '--retention-in-days',
                str(retention),
            ],
            profile=profile,
            region=region,
            check=False,
        )

    refreshed = aws_cli.aws(
        [
            'logs',
            'describe-log-groups',
            '--log-group-name-prefix',
            log_group,
        ],
        profile=profile,
        region=region,
        parse_json=True,
        check=False,
    )
    for group in (refreshed.json or {}).get('logGroups', []):
        if group.get('logGroupName') == log_group:
            return group.get('arn')
    return None


def _ensure_rest_api(
    rendered: RenderedResource,
    *,
    profile: str | None,
    region: str,
) -> tuple[str | None, str | None]:
    """Crea la REST API si no existe; devuelve (api_id, root_resource_id)."""
    api_name = rendered.name
    api_id = _find_rest_api_id(api_name, profile=profile, region=region)
    if api_id is None:
        endpoint_type = rendered.spec.get('endpoint_type', 'REGIONAL')
        print(_c(YELLOW, f'  creando REST API {api_name}...'))
        result = aws_cli.aws(
            [
                'apigateway',
                'create-rest-api',
                '--name',
                api_name,
                '--endpoint-configuration',
                f'types={endpoint_type}',
            ],
            profile=profile,
            region=region,
            parse_json=True,
        )
        api_id = (result.json or {}).get('id')
        print(_c(GREEN, f'  OK  REST API {api_name} creada'))
    else:
        print(_c(CYAN, f'  REST API {api_name} ya existe — se reutiliza'))

    root_resource_id = _find_root_resource_id(
        api_id,
        profile=profile,
        region=region,
    )
    return api_id, root_resource_id


def _find_rest_api_id(
    api_name: str,
    *,
    profile: str | None,
    region: str,
) -> str | None:
    """Busca el Id de una REST API por nombre, o None si no existe."""
    result = aws_cli.aws(
        ['apigateway', 'get-rest-apis'],
        profile=profile,
        region=region,
        parse_json=True,
        check=False,
    )
    for item in (result.json or {}).get('items', []):
        if item.get('name') == api_name:
            return item.get('id')
    return None


def _find_root_resource_id(
    api_id: str | None,
    *,
    profile: str | None,
    region: str,
) -> str | None:
    """Devuelve el RootResourceId (path `/`) de una REST API."""
    if api_id is None:
        return None
    result = aws_cli.aws(
        ['apigateway', 'get-resources', '--rest-api-id', api_id],
        profile=profile,
        region=region,
        parse_json=True,
        check=False,
    )
    for item in (result.json or {}).get('items', []):
        if item.get('path') == '/':
            return item.get('id')
    return None


# --------------------------------------------------------------------------
# Custom domains de API Gateway (EDGE vs REGIONAL)
# --------------------------------------------------------------------------
# Stages de deployment de API Gateway (no confundir con `stage` del repo
# que es dev/stage/prod): convencion del proyecto, usar 'prod' para todo.
_APIGW_DEPLOYMENT_STAGE = 'prod'


def _describe_custom_domain(
    domain_name: str,
    *,
    profile: str | None,
    region: str,
) -> dict[str, Any] | None:
    """Describe un custom domain de API Gateway, o None si no existe."""
    result = aws_cli.aws(
        ['apigateway', 'get-domain-name', '--domain-name', domain_name],
        profile=profile,
        region=region,
        parse_json=True,
        check=False,
    )
    return result.json or None


def _domain_endpoint_type(domain: dict[str, Any] | None) -> str | None:
    """Extrae `endpointConfiguration.types[0]` de un describe."""
    if not domain:
        return None
    types = (domain.get('endpointConfiguration') or {}).get('types') or []
    return types[0] if types else None


def _create_custom_domain(
    domain_name: str,
    endpoint_type: str,
    certificate_arn: str,
    *,
    profile: str | None,
    region: str,
) -> None:
    """Crea un custom domain con el endpoint_type pedido.

    Para EDGE: el flag es `--certificate-arn` (cert global, debe vivir
    en us-east-1). Para REGIONAL: `--regional-certificate-arn`.
    """
    cert_flag = (
        '--certificate-arn'
        if endpoint_type == 'EDGE'
        else '--regional-certificate-arn'
    )
    aws_cli.aws(
        [
            'apigateway',
            'create-domain-name',
            '--domain-name',
            domain_name,
            cert_flag,
            certificate_arn,
            '--endpoint-configuration',
            f'types={endpoint_type}',
            '--security-policy',
            'TLS_1_2',
        ],
        profile=profile,
        region=region,
    )


def _ensure_base_path_mapping(
    domain_name: str,
    api_id: str,
    base_path: str,
    stage_name: str,
    *,
    profile: str | None,
    region: str,
) -> None:
    """Asegura que existe un base-path-mapping domain -> api_id/stage.

    `base_path` vacio significa root mapping (paths `/` del custom
    domain enrutan al `/` de la API).
    """
    existing = aws_cli.aws(
        [
            'apigateway',
            'get-base-path-mappings',
            '--domain-name',
            domain_name,
        ],
        profile=profile,
        region=region,
        parse_json=True,
        check=False,
    )
    expected_path = base_path or '(none)'
    for item in (existing.json or {}).get('items', []):
        current_path = item.get('basePath', '(none)')
        # AWS devuelve '(none)' cuando es root (base_path vacio en yaml).
        if (
            current_path == expected_path
            and item.get('restApiId') == api_id
            and item.get('stage') == stage_name
        ):
            return  # mapping ya existe correctamente

    args = [
        'apigateway',
        'create-base-path-mapping',
        '--domain-name',
        domain_name,
        '--rest-api-id',
        api_id,
        '--stage',
        stage_name,
    ]
    if base_path:
        args.extend(['--base-path', base_path])
    aws_cli.aws(args, profile=profile, region=region, check=False)


def _ensure_custom_domain(
    rendered: RenderedResource,
    api_id: str | None,
    *,
    profile: str | None,
    region: str,
    dry_run: bool,
) -> tuple[dict[str, str | None], list[str]]:
    """Provisiona o reconcilia el custom domain del stage actual.

    Si el yaml declara `custom_domain_by_stage[<stage>]` y el endpoint
    type difiere de lo aprovisionado en AWS, recrea el custom domain
    (delete + create) y re-aplica el base-path-mapping. Si no existe,
    lo crea. Si ya esta alineado, no-op.

    Returns
    -------
    tuple[dict, list[str]]
        `resources` (claves planas con identificadores), `published`
        (paths SSM publicados — vacio por ahora; placeholder para
        futura publicacion del CloudFront distribution domain).
    """
    config = rendered.custom_domain
    if not config:
        return {}, []

    domain_name = config['domain_name']
    desired_type = config.get('endpoint_type', 'REGIONAL')
    certificate_arn = config['certificate_arn']
    base_paths = config.get('base_path_mappings') or [{'base_path': ''}]

    if dry_run:
        print(
            _c(
                YELLOW,
                f'[dry-run] apigateway ensure-domain {domain_name} '
                f'(endpoint={desired_type})',
            ),
        )
        return {}, []

    current = _describe_custom_domain(
        domain_name,
        profile=profile,
        region=region,
    )
    current_type = _domain_endpoint_type(current)

    if current and current_type != desired_type:
        print(
            _c(
                YELLOW,
                f'  custom domain {domain_name}: drift {current_type} -> '
                f'{desired_type}, recreando...',
            ),
        )
        aws_cli.aws(
            [
                'apigateway',
                'delete-domain-name',
                '--domain-name',
                domain_name,
            ],
            profile=profile,
            region=region,
        )
        current = None

    if current is None:
        print(
            _c(
                YELLOW,
                f'  creando custom domain {domain_name} ({desired_type})...',
            ),
        )
        _create_custom_domain(
            domain_name,
            desired_type,
            certificate_arn,
            profile=profile,
            region=region,
        )
        current = _describe_custom_domain(
            domain_name,
            profile=profile,
            region=region,
        )

    if api_id is None:
        print(
            _c(
                YELLOW,
                f'  WARN: no se pudo aplicar base-path-mapping de '
                f'{domain_name}: api_id desconocido',
            ),
        )
    else:
        for mapping in base_paths:
            base_path = mapping.get('base_path', '')
            stage_name = mapping.get('stage', _APIGW_DEPLOYMENT_STAGE)
            _ensure_base_path_mapping(
                domain_name,
                api_id,
                base_path,
                stage_name,
                profile=profile,
                region=region,
            )

    print(_c(GREEN, f'  OK  custom domain {domain_name} ({desired_type})'))

    resources: dict[str, str | None] = {
        f'custom-domain:{domain_name}:endpoint_type': desired_type,
    }
    if current:
        cf_domain = current.get('distributionDomainName') or current.get(
            'regionalDomainName',
        )
        if cf_domain:
            resources[f'custom-domain:{domain_name}:gateway_domain'] = cf_domain

    return resources, []


# --------------------------------------------------------------------------
# Orquestacion de la provision y la limpieza de la infra
# --------------------------------------------------------------------------
def _provision_cloudwatch_alarm(
    rendered: RenderedResource,
    *,
    profile: str | None,
    region: str,
    dry_run: bool,
) -> tuple[dict[str, str | None], list[str]]:
    """Provisiona una alarma CloudWatch. Idempotente via `put-metric-alarm`.

    `put-metric-alarm` es upsert: re-aplica los mismos args y AWS hace
    diff internamente. Si la alarma no existe la crea; si existe la
    actualiza con los args nuevos.
    """
    spec = rendered.spec
    alarm_name = rendered.name

    if dry_run:
        print(_c(YELLOW, f'[dry-run] cloudwatch put-metric-alarm {alarm_name}'))
        return {f'cloudwatch:{alarm_name}': None}, []

    metric = spec['metric']
    args = [
        'cloudwatch',
        'put-metric-alarm',
        '--alarm-name',
        alarm_name,
        '--namespace',
        metric['namespace'],
        '--metric-name',
        metric['name'],
        '--statistic',
        spec.get('statistic', 'Maximum'),
        '--period',
        str(spec.get('period_seconds', 300)),
        '--evaluation-periods',
        str(spec.get('evaluation_periods', 1)),
        '--threshold',
        str(spec['threshold']),
        '--comparison-operator',
        spec.get('comparison', 'GreaterThanThreshold'),
        '--treat-missing-data',
        spec.get('treat_missing_data', 'notBreaching'),
    ]
    description = spec.get('description')
    if description:
        # YAML `description: >` (folded) puede dejar trailing newline
        # que AWS CLI no maneja bien.
        args.extend(['--alarm-description', description.strip()])

    dims = metric.get('dimensions') or {}
    if dims:
        args.append('--dimensions')
        args.extend([f'Name={k},Value={v}' for k, v in dims.items()])

    actions = spec.get('alarm_actions') or []
    if actions:
        args.append('--alarm-actions')
        args.extend(actions)

    aws_cli.aws(args, profile=profile, region=region)
    print(_c(GREEN, f'  OK  alarma {alarm_name} configurada'))

    return {f'cloudwatch:{alarm_name}': alarm_name}, []


def _provision_s3_bucket(
    rendered: RenderedResource,
    *,
    profile: str | None,
    region: str,
    dry_run: bool,
) -> tuple[dict[str, str | None], list[str]]:
    """Provisiona un bucket S3 privado + cifrado. Idempotente.

    Si el bucket ya existe (`head-bucket` retorna 0) NO se recrea: solo se
    re-aplican el public-access-block + la SSE (idempotentes) y se re-publican
    los SSM. Bucket privado (todo acceso publico bloqueado) + SSE-S3 (AES256).
    El nombre del bucket es global; se usa `portfolio-<x>-<stage>` para evitar
    colisiones entre envs.
    """
    bucket = rendered.name
    arn = f'arn:aws:s3:::{bucket}'

    if dry_run:
        print(_c(YELLOW, f'[dry-run] s3api create-bucket {bucket}'))
    else:
        exists = aws_cli.aws_resource_exists(
            's3api',
            ['head-bucket', '--bucket', bucket],
            profile=profile,
            region=region,
        )
        if exists:
            print(_c(CYAN, f'  bucket {bucket} ya existe — no se recrea'))
        else:
            _create_s3_bucket(bucket, profile=profile, region=region)
        _harden_s3_bucket(rendered, bucket, profile=profile, region=region)

    values: dict[str, str | None] = {'name': bucket, 'arn': arn}
    published = _publish_ssm(
        rendered,
        values,
        profile=profile,
        region=region,
        dry_run=dry_run,
    )
    resources: dict[str, str | None] = {
        f's3:{bucket}:name': bucket,
        f's3:{bucket}:arn': arn,
    }
    return resources, published


def _create_s3_bucket(
    bucket: str,
    *,
    profile: str | None,
    region: str,
) -> None:
    """Crea el bucket. us-east-1 NO acepta LocationConstraint (es el default)."""
    args = ['s3api', 'create-bucket', '--bucket', bucket]
    if region != 'us-east-1':
        args += [
            '--create-bucket-configuration',
            f'LocationConstraint={region}',
        ]
    aws_cli.aws(args, profile=profile, region=region)
    aws_cli.aws(
        ['s3api', 'wait', 'bucket-exists', '--bucket', bucket],
        profile=profile,
        region=region,
    )


def _harden_s3_bucket(
    rendered: RenderedResource,
    bucket: str,
    *,
    profile: str | None,
    region: str,
) -> None:
    """Aplica public-access-block (todo bloqueado) + SSE-S3 (AES256)."""
    if rendered.spec.get('block_public_access', True):
        aws_cli.aws(
            [
                's3api',
                'put-public-access-block',
                '--bucket',
                bucket,
                '--public-access-block-configuration',
                'BlockPublicAcls=true,IgnorePublicAcls=true,'
                'BlockPublicPolicy=true,RestrictPublicBuckets=true',
            ],
            profile=profile,
            region=region,
        )
    if rendered.spec.get('encryption', True):
        aws_cli.aws(
            [
                's3api',
                'put-bucket-encryption',
                '--bucket',
                bucket,
                '--server-side-encryption-configuration',
                '{"Rules":[{"ApplyServerSideEncryptionByDefault":'
                '{"SSEAlgorithm":"AES256"}}]}',
            ],
            profile=profile,
            region=region,
        )


_PROVISIONERS = {
    'dynamodb-table': _provision_dynamodb_table,
    'rest-api': _provision_rest_api,
    'sqs-queue': _provision_sqs_queue,
    's3-bucket': _provision_s3_bucket,
    'cloudwatch-alarm': _provision_cloudwatch_alarm,
}


def _ordered_rendered(stage: str) -> list[RenderedResource]:
    """Renderiza todos los fragmentos y los ordena por `_PROVISION_ORDER`.

    Sub-orden dentro de `sqs-queue`: las DLQs (sin `redrive_policy`) van
    PRIMERO porque las colas principales con `redrive_policy.target` las
    necesitan creadas para resolver el ARN de la DLQ.
    """
    rendered = [
        render_resource(path, stage=stage) for path in discover_resources()
    ]
    return sorted(
        rendered,
        key=lambda r: (
            _PROVISION_ORDER.index(r.kind),
            # Sub-key para SQS: 0 = sin redrive (DLQ), 1 = con redrive (main).
            1
            if (r.kind == 'sqs-queue' and r.spec.get('redrive_policy'))
            else 0,
        ),
    )


def provision_infra(
    *,
    stage: str,
    profile: str | None,
    region: str = _REGION,
    dry_run: bool = False,
) -> InfraState:
    """Provisiona TODOS los recursos de `resources/`. Idempotente.

    Por cada recurso: si ya existe (consulta `describe-*`/`get-*`) NO se
    recrea; si no, se crea. En ambos casos se re-publican los SSM. El
    orden es SQS -> DynamoDB -> API Gateway. El resultado se registra en
    `serverless/lambda/.state/infra-<stage>.json`.

    Parameters
    ----------
    stage : str
        Entorno (`dev` | `stage` | `prod`).
    profile : str | None
        Perfil AWS CLI opcional.
    region : str
        Region AWS.
    dry_run : bool
        Si True, solo imprime que haria; no toca AWS ni el estado.

    Returns
    -------
    InfraState
        Identificadores reconciliados + paths SSM publicados.
    """
    infra = InfraState(stage=stage)
    for rendered in _ordered_rendered(stage):
        print(_c(CYAN, f'[{rendered.kind}] {rendered.name}'))
        provisioner = _PROVISIONERS[rendered.kind]
        resources, published = provisioner(
            rendered,
            profile=profile,
            region=region,
            dry_run=dry_run,
        )
        infra.resources.update(resources)
        infra.ssm_published.extend(published)

    if not dry_run:
        state.save_state(
            state.LambdaState(
                scope=_INFRA_SCOPE,
                stage=stage,
                config_hash=state.config_hash(
                    {'ssm_published': sorted(infra.ssm_published)},
                ),
                code_hash='sha256:empty',
                resources=infra.resources,
                updated_at=state.now_iso(),
            ),
        )
    return infra


def deprovision_infra(
    *,
    stage: str,
    profile: str | None,
    region: str = _REGION,
    dry_run: bool = False,
) -> None:
    """Borra todos los recursos de infra del stage en orden inverso.

    Orden: API Gateway REST -> tablas DynamoDB -> DLQ SQS. Tras borrar,
    el `.state/infra-<stage>.json` se limpia.

    Parameters
    ----------
    stage : str
        Entorno a destruir.
    profile : str | None
        Perfil AWS CLI opcional.
    region : str
        Region AWS.
    dry_run : bool
        Si True, solo imprime que haria.
    """
    rendered = _ordered_rendered(stage)
    for resource in reversed(rendered):
        print(_c(YELLOW, f'[deprovision] {resource.kind} {resource.name}'))
        if dry_run:
            continue
        _delete_resource(resource, profile=profile, region=region)

    if not dry_run:
        removed = [
            path
            for path in state.clear_state(stage)
            if path.stem == f'{_INFRA_SCOPE}-{stage}'
        ]
        for path in removed:
            print(_c(GREEN, f'  estado borrado: {path.name}'))


def _delete_resource(
    rendered: RenderedResource,
    *,
    profile: str | None,
    region: str,
) -> None:
    """Borra un recurso individual segun su `kind`."""
    if rendered.kind == 'dynamodb-table':
        aws_cli.aws(
            ['dynamodb', 'delete-table', '--table-name', rendered.name],
            profile=profile,
            region=region,
            check=False,
        )
    elif rendered.kind == 'sqs-queue':
        queue_url = _resolve_queue_url(
            rendered.name,
            profile=profile,
            region=region,
        )
        if queue_url:
            aws_cli.aws(
                ['sqs', 'delete-queue', '--queue-url', queue_url],
                profile=profile,
                region=region,
                check=False,
            )
    elif rendered.kind == 'rest-api':
        api_id = _find_rest_api_id(
            rendered.name,
            profile=profile,
            region=region,
        )
        if api_id:
            aws_cli.aws(
                ['apigateway', 'delete-rest-api', '--rest-api-id', api_id],
                profile=profile,
                region=region,
                check=False,
            )
    elif rendered.kind == 's3-bucket':
        # `rm --recursive` vacia el bucket (delete-bucket falla si no esta
        # vacio); luego borra el bucket. check=False: tolera bucket ausente.
        aws_cli.aws(
            ['s3', 'rm', f's3://{rendered.name}', '--recursive'],
            profile=profile,
            region=region,
            check=False,
        )
        aws_cli.aws(
            ['s3api', 'delete-bucket', '--bucket', rendered.name],
            profile=profile,
            region=region,
            check=False,
        )


# --------------------------------------------------------------------------
# Comandos del CLI
# --------------------------------------------------------------------------
def cmd_provision_infra(flags: dict[str, Any]) -> int:
    """Provisiona TODOS los recursos compartidos de `resources/`.

    Reemplaza el viejo `cmd_deploy_infra` (CloudFormation). En el toque
    minimo de `main.py` de la Fase 3, el comando `deploy-infra` apunta
    aqui; el nombre definitivo `provision-infra` se registra en la Fase 5.

    Flags:
      --stage       : dev | stage | prod (default dev).
      --aws-profile : perfil AWS CLI (opcional).
      --dry-run     : renderiza los recursos sin tocar AWS.
    """
    stage = flags.get('stage', 'dev')
    if stage == 'local':
        _err('La infra compartida no aplica al stage `local`.')
        return 1

    dry_run = bool(flags.get('dry_run'))
    profile = flags.get('aws_profile')

    try:
        infra = provision_infra(
            stage=stage,
            profile=profile,
            dry_run=dry_run,
        )
    except (AwsError, ValueError, OSError) as exc:
        _err(f'provision-infra fallo: {exc}')
        return 1

    suffix = ' (dry-run)' if dry_run else ''
    print(
        _c(
            GREEN,
            f'OK  infra {stage} aprovisionada{suffix}: '
            f'{len(infra.resources)} recursos, '
            f'{len(infra.ssm_published)} SSM',
        ),
    )
    return 0


def cmd_deprovision_infra(flags: dict[str, Any]) -> int:
    """Borra todos los recursos compartidos de un stage (DESTRUCTIVO).

    Flags:
      --stage       : dev | stage | prod.
      --confirm     : obligatorio (operacion destructiva).
      --aws-profile : perfil AWS CLI (opcional).
      --dry-run     : muestra que haria sin ejecutar.
    """
    stage = flags.get('stage', 'dev')
    if stage == 'local':
        _err('La infra compartida no aplica al stage `local`.')
        return 1

    dry_run = bool(flags.get('dry_run'))
    if not dry_run and not flags.get('confirm'):
        _err('deprovision-infra es destructivo: agrega --confirm.')
        return 2

    try:
        deprovision_infra(
            stage=stage,
            profile=flags.get('aws_profile'),
            dry_run=dry_run,
        )
    except (AwsError, ValueError, OSError) as exc:
        _err(f'deprovision-infra fallo: {exc}')
        return 1

    print(_c(GREEN, f'OK  infra {stage} destruida'))
    return 0


def cmd_list_resources(flags: dict[str, Any]) -> int:
    """Lista los recursos compartidos declarados en `resources/`."""
    stage = flags.get('stage', 'dev')
    paths = discover_resources()
    if not paths:
        print(_c(YELLOW, f'No hay recursos en {_RESOURCES_DIR}.'))
        return 0

    print(_c(CYAN, f'Recursos compartidos (stage {stage}):'))
    for path in paths:
        try:
            rendered = render_resource(path, stage=stage)
        except ValueError as exc:
            _err(str(exc))
            return 1
        print(f'  {rendered.kind:16s}  {rendered.name}')
    return 0
