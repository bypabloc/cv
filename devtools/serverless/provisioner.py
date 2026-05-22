"""Provisioner de Lambdas con AWS CLI.

Sin SAM/CloudFormation, devtools traduce el `manifest.yaml` de un Lambda
directamente a una secuencia de llamadas `aws ...`. Este modulo hace tres
cosas:

  1. `render(manifest, stage)` — funcion PURA: produce un `RenderedLambda`
     con el documento de politica IAM, la config de la funcion (memory,
     timeout, env, runtime, architecture) y la descripcion del trigger.
     Sin tocar AWS. Es lo testeable.
  2. `provision(rendered, action, ...)` — ejecuta las llamadas AWS CLI
     segun la `Action` que decidio `state.diff` (CREATE / UPDATE_* ).
  3. `deprovision(state, ...)` — borra los recursos en orden inverso.

La traduccion `uses` -> IAM resuelve los ARNs a strings concretos
(cuenta y region reales), sin `Fn::Sub` ni `Fn::ImportValue`. Los
identificadores de infra (Stream ARN, ApiId) se leen de SSM con
`aws ssm get-parameter`.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
import time
from typing import TYPE_CHECKING
from typing import Any

from serverless.aws_cli import AwsError
from serverless.aws_cli import AwsResult
from serverless.aws_cli import aws
from serverless.resolve import ManifestError
from serverless.state import LambdaState
from serverless.state import now_iso


if TYPE_CHECKING:
    from pathlib import Path

    from serverless.state import Action


# Stages validos del bloque `env` del manifiesto.
_VALID_ENV_STAGES = ('default', 'dev', 'stage', 'prod')

# Tipos de trigger soportados.
_VALID_TRIGGERS = ('direct', 'http', 'on-table-changes')

# Espera de propagacion del rol IAM recien creado antes de
# `create-function`: un rol nuevo puede no estar disponible aun.
_IAM_PROPAGATION_SECONDS = 10

# Tablas DynamoDB: nombre corto -> definicion del catalogo. Sin
# marcadores CloudFormation: nombres y ARNs concretos.
_TABLES: dict[str, dict[str, str]] = {
    'contacts': {
        'physical': 'portfolio-contacts-${stage}',
        'env': 'SSM_CONTACTS_TABLE_PATH',
        'has_stream': 'yes',
    },
    'tracking': {
        'physical': 'portfolio-tracking-${stage}',
        'env': 'SSM_TRACKING_TABLE_PATH',
        'has_stream': 'yes',
    },
    'cache': {
        'physical': 'portfolio-cache-${stage}',
        'env': 'SSM_CACHE_TABLE_PATH',
        'has_stream': '',
    },
    'rate-limit-rules': {
        'physical': 'portfolio-rate-limit-rules-${stage}',
        'env': 'SSM_RATE_LIMIT_RULES_TABLE_PATH',
        'has_stream': '',
    },
    'rate-limit-buckets': {
        'physical': 'portfolio-rate-limit-buckets-${stage}',
        'env': 'SSM_RATE_LIMIT_BUCKETS_TABLE_PATH',
        'has_stream': '',
    },
}

# Secretos SSM: nombre corto -> (path SSM, env var del codigo).
_SECRETS: dict[str, dict[str, str]] = {
    'neon-url': {
        'path': '/portfolio/${stage}/neon-url',
        'env': 'SSM_NEON_URL_PATH',
    },
    'turnstile-secret': {
        'path': '/portfolio/${stage}/turnstile-secret',
        'env': 'SSM_TURNSTILE_SECRET_PATH',
    },
    'turnstile-bypass-secret': {
        'path': '/portfolio/dev/turnstile-bypass-secret',
        'env': 'SSM_TURNSTILE_BYPASS_PATH',
    },
    'owner-email': {
        'path': '/portfolio/owner-email',
        'env': 'SSM_OWNER_EMAIL_PATH',
    },
    'ses-from-address': {
        'path': '/portfolio/ses-from-address',
        'env': 'SSM_SES_FROM_PATH',
    },
}

# Identidades verificadas en SES sobre las que el Lambda puede enviar.
_SES_IDENTITIES = (
    'the-full-stack.com',
    'no-reply@the-full-stack.com',
)
# Configuration set por defecto de la domain identity.
_SES_CONFIG_SET = 'my-first-configuration-set'

# Niveles de acceso DynamoDB -> acciones IAM.
_DYNAMO_ACTIONS: dict[str, list[str]] = {
    'read': [
        'dynamodb:GetItem',
        'dynamodb:Query',
        'dynamodb:BatchGetItem',
    ],
    'write': [
        'dynamodb:PutItem',
        'dynamodb:UpdateItem',
        'dynamodb:DeleteItem',
        'dynamodb:BatchWriteItem',
    ],
}

# Trust policy del rol: permite a Lambda asumirlo.
_LAMBDA_TRUST_POLICY: dict[str, Any] = {
    'Version': '2012-10-17',
    'Statement': [
        {
            'Effect': 'Allow',
            'Principal': {'Service': 'lambda.amazonaws.com'},
            'Action': 'sts:AssumeRole',
        },
    ],
}

# Managed policy de logs basicos para el rol del Lambda.
_BASIC_EXECUTION_POLICY_ARN = (
    'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
)

# Nombre de la policy inline aplicada al rol.
_INLINE_POLICY_NAME = 'inline'

# Retencion de logs del Lambda (dias).
_LOG_RETENTION_DAYS = 7


@dataclass(frozen=True)
class TriggerSpec:
    """Descripcion del trigger renderizado de un Lambda.

    Attributes
    ----------
    type : str
        `direct` | `http` | `on-table-changes`.
    method : str | None
        Metodo HTTP (solo `http`). Ej. `POST`.
    path : str | None
        Path del endpoint (solo `http`). Ej. `/contact`.
    tables : tuple[str, ...]
        Nombres cortos de las tablas (solo `on-table-changes`).
    """

    type: str
    method: str | None = None
    path: str | None = None
    tables: tuple[str, ...] = ()


@dataclass(frozen=True)
class RenderedLambda:
    """Resultado puro de `render`: el Lambda traducido a config + IAM.

    Attributes
    ----------
    name : str
        Nombre corto del Lambda (ej. `contact-form`).
    function_name : str
        Nombre fisico de la funcion AWS (`portfolio-<name>-<stage>`).
    runtime : str
        Runtime AWS (ej. `python3.13`).
    architecture : str
        Arquitectura (`arm64` | `x86_64`).
    handler : str
        Handler del Lambda (ej. `core.handler.lambda_handler`).
    memory : int
        Memoria asignada (MB).
    timeout : int
        Timeout (segundos).
    env_vars : dict[str, str]
        Variables de entorno renderizadas.
    iam_policy : dict[str, Any]
        Documento de politica IAM (`Version` + `Statement`).
    trigger : TriggerSpec
        Descripcion del trigger.
    role_name : str
        Nombre del rol IAM (`portfolio-<name>-<stage>`).
    """

    name: str
    function_name: str
    runtime: str
    architecture: str
    handler: str
    memory: int
    timeout: int
    env_vars: dict[str, str] = field(default_factory=dict)
    iam_policy: dict[str, Any] = field(default_factory=dict)
    trigger: TriggerSpec = field(default_factory=lambda: TriggerSpec('direct'))
    role_name: str = ''


def _interp(value: str, stage: str) -> str:
    """Interpola `${stage}` en un string del manifiesto."""
    return value.replace('${stage}', stage)


def _ssm_path(resource_type: str, name: str, attribute: str) -> str:
    """Path SSM de un atributo de un recurso compartido (sin interpolar)."""
    return f'/portfolio/${{stage}}/{resource_type}/{name}/{attribute}'


def _table_def(short_name: str) -> dict[str, str]:
    """Resuelve un nombre corto de tabla a su definicion del catalogo."""
    table = _TABLES.get(short_name)
    if table is None:
        raise ManifestError(
            f'tabla desconocida: {short_name!r}. '
            f'Validas: {", ".join(sorted(_TABLES))}',
        )
    return table


def _secret_def(short_name: str) -> dict[str, str]:
    """Resuelve un nombre corto de secreto a su definicion del catalogo."""
    secret = _SECRETS.get(short_name)
    if secret is None:
        raise ManifestError(
            f'secreto desconocido: {short_name!r}. '
            f'Validos: {", ".join(sorted(_SECRETS))}',
        )
    return secret


def _resolve_env(manifest: dict[str, Any], stage: str) -> dict[str, str]:
    """Combina `env.default` + `env.<stage>` del manifiesto.

    Las claves del stage especifico sobrescriben las de `default`. Todos
    los valores se devuelven como strings con `${stage}` interpolado.
    """
    env_block = manifest.get('env') or {}
    if not isinstance(env_block, dict):
        raise ManifestError("'env' debe ser un mapa por stage")

    for key in env_block:
        if key not in _VALID_ENV_STAGES:
            raise ManifestError(
                f'env.{key} no es un stage valido. '
                f'Validos: {", ".join(_VALID_ENV_STAGES)}',
            )

    merged: dict[str, Any] = {}
    merged.update(env_block.get('default') or {})
    if stage in env_block:
        merged.update(env_block.get(stage) or {})
    return {k: _interp(str(v), stage) for k, v in merged.items()}


def _build_env_vars(manifest: dict[str, Any], stage: str) -> dict[str, str]:
    """Construye el bloque de env vars de la funcion.

    Combina las env vars explicitas (`env`), Powertools y las derivadas
    de `uses` (path SSM de cada tabla + path SSM de cada secreto).
    """
    name = manifest['name']
    env: dict[str, str] = {
        'POWERTOOLS_SERVICE_NAME': name,
        'POWERTOOLS_METRICS_NAMESPACE': 'Portfolio',
        'POWERTOOLS_LOG_LEVEL': 'INFO',
        'ENVIRONMENT': stage,
        'STAGE': stage,
    }
    env.update(_resolve_env(manifest, stage))

    uses = manifest.get('uses') or {}

    tables = uses.get('tables') or {}
    if isinstance(tables, dict):
        for short_name in tables:
            tdef = _table_def(short_name)
            env[tdef['env']] = _interp(
                _ssm_path('dynamodb', short_name, 'name'), stage
            )

    for short_name in uses.get('secrets') or []:
        sdef = _secret_def(short_name)
        env[sdef['env']] = _interp(sdef['path'], stage)

    return env


def _dynamodb_statements(
    tables: Any,
    stage: str,
    *,
    region: str,
    account: str,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Statements DynamoDB de las tablas declaradas + sus paths SSM.

    Devuelve `(statements, table_ssm_paths)`: una Statement IAM por tabla
    (acciones segun el nivel de acceso) y los paths SSM de los nombres de
    tabla, que el Lambda lee en runtime.
    """
    statements: list[dict[str, Any]] = []
    table_ssm_paths: list[str] = []
    if not isinstance(tables, dict):
        return statements, table_ssm_paths

    for short_name, access in tables.items():
        tdef = _table_def(short_name)
        actions: list[str] = []
        if access in ('read', 'read-write'):
            actions += _DYNAMO_ACTIONS['read']
        if access in ('write', 'read-write'):
            actions += _DYNAMO_ACTIONS['write']
        if not actions:
            raise ManifestError(
                f'acceso invalido {access!r} para la tabla '
                f'{short_name!r}. Usa read | write | read-write.',
            )
        physical = _interp(tdef['physical'], stage)
        statements.append(
            {
                'Effect': 'Allow',
                'Action': actions,
                'Resource': [
                    f'arn:aws:dynamodb:{region}:{account}:table/{physical}',
                ],
            }
        )
        table_ssm_paths.append(
            _interp(_ssm_path('dynamodb', short_name, 'name'), stage)
        )
    return statements, table_ssm_paths


def _stream_statements(
    trigger: dict[str, Any],
    stage: str,
    *,
    region: str,
    account: str,
) -> list[dict[str, Any]]:
    """Statements IAM de un trigger `on-table-changes`.

    Permisos de lectura de los Streams de las tablas + `sqs:SendMessage`
    al DLQ del stream processor. Los ARNs concretos del Stream y del DLQ
    se resuelven contra SSM en `provision` (aqui se usa el ARN base de la
    tabla, que cubre `table/<name>/stream/*`).
    """
    statements: list[dict[str, Any]] = []
    stream_resources: list[str] = []
    for short_name in trigger.get('tables') or []:
        tdef = _table_def(short_name)
        if not tdef['has_stream']:
            raise ManifestError(
                f'la tabla {short_name!r} no tiene Stream — no puede '
                f'usarse en on-table-changes.',
            )
        physical = _interp(tdef['physical'], stage)
        stream_resources.append(
            f'arn:aws:dynamodb:{region}:{account}:table/{physical}/stream/*',
        )
    statements.append(
        {
            'Effect': 'Allow',
            'Action': [
                'dynamodb:DescribeStream',
                'dynamodb:GetRecords',
                'dynamodb:GetShardIterator',
                'dynamodb:ListStreams',
            ],
            'Resource': stream_resources,
        }
    )
    statements.append(
        {
            'Effect': 'Allow',
            'Action': ['sqs:SendMessage'],
            'Resource': [
                f'arn:aws:sqs:{region}:{account}:'
                f'portfolio-stream-processor-dlq-{stage}',
            ],
        }
    )
    return statements


def _build_statements(
    manifest: dict[str, Any],
    stage: str,
    *,
    region: str,
    account: str,
) -> list[dict[str, Any]]:
    """Traduce `uses` + `trigger` a una lista de Statements IAM.

    Cada tabla -> Statement DynamoDB; cada secreto -> Statement SSM
    `GetParameter` + un Statement `kms:Decrypt`; `sends-email` ->
    Statement SES; `on-table-changes` ->
    Statements de Stream + SQS al DLQ. Sin `Fn::Sub`: ARNs concretos.
    """
    uses = manifest.get('uses') or {}

    statements, table_ssm_paths = _dynamodb_statements(
        uses.get('tables') or {}, stage, region=region, account=account
    )

    secrets = uses.get('secrets') or []
    ssm_read_arns = [
        f'arn:aws:ssm:{region}:{account}:parameter{path}'
        for path in table_ssm_paths
    ]
    for short_name in secrets:
        sdef = _secret_def(short_name)
        path = _interp(sdef['path'], stage)
        ssm_read_arns.append(
            f'arn:aws:ssm:{region}:{account}:parameter{path}',
        )
    if ssm_read_arns:
        statements.append(
            {
                'Effect': 'Allow',
                'Action': ['ssm:GetParameter'],
                'Resource': ssm_read_arns,
            }
        )
    if secrets:
        statements.append(
            {
                'Effect': 'Allow',
                'Action': ['kms:Decrypt'],
                'Resource': f'arn:aws:kms:{region}:{account}:key/*',
                'Condition': {
                    'StringEquals': {
                        'kms:ViaService': f'ssm.{region}.amazonaws.com',
                    },
                },
            }
        )

    if uses.get('sends-email'):
        ses_resources = [
            f'arn:aws:ses:{region}:{account}:identity/{ident}'
            for ident in _SES_IDENTITIES
        ]
        ses_resources.append(
            f'arn:aws:ses:{region}:{account}:'
            f'configuration-set/{_SES_CONFIG_SET}',
        )
        statements.append(
            {
                'Effect': 'Allow',
                'Action': ['ses:SendEmail', 'ses:SendRawEmail'],
                'Resource': ses_resources,
            }
        )

    trigger = manifest.get('trigger') or {}
    if trigger.get('type') == 'on-table-changes':
        statements += _stream_statements(
            trigger, stage, region=region, account=account
        )

    return statements


def _build_trigger(manifest: dict[str, Any]) -> TriggerSpec:
    """Construye el `TriggerSpec` desde el bloque `trigger` del manifiesto.

    Raises
    ------
    ManifestError
        Si el tipo de trigger no es valido o falta `method`/`path` en un
        trigger `http`, o `tables` en `on-table-changes`.
    """
    trigger = manifest.get('trigger') or {}
    ttype = trigger.get('type')

    if ttype not in _VALID_TRIGGERS:
        raise ManifestError(
            f'trigger.type invalido: {ttype!r}. '
            f'Validos: {", ".join(_VALID_TRIGGERS)}',
        )

    if ttype == 'http':
        method = trigger.get('method')
        path = trigger.get('path')
        if not method or not path:
            raise ManifestError("trigger http requiere 'method' y 'path'.")
        return TriggerSpec(type='http', method=method, path=path)

    if ttype == 'on-table-changes':
        tables = trigger.get('tables') or []
        for short_name in tables:
            tdef = _table_def(short_name)
            if not tdef['has_stream']:
                raise ManifestError(
                    f'la tabla {short_name!r} no tiene Stream.',
                )
        return TriggerSpec(type='on-table-changes', tables=tuple(tables))

    return TriggerSpec(type='direct')


def render(manifest: dict[str, Any], *, stage: str) -> RenderedLambda:
    """Funcion pura: `manifest.yaml` -> `RenderedLambda`. Sin tocar AWS.

    Parameters
    ----------
    manifest : dict[str, Any]
        Manifiesto del Lambda ya validado y con defaults aplicados.
    stage : str
        Stage objetivo (`dev` | `stage` | `prod`).

    Returns
    -------
    RenderedLambda
        Config de la funcion, documento de politica IAM y trigger.

    Raises
    ------
    ManifestError
        Si el manifiesto declara un recurso, acceso o trigger invalido.
    """
    name = manifest['name']
    function_name = f'portfolio-{name}-{stage}'
    region = str(manifest.get('region', 'us-east-1'))
    # La cuenta no se conoce sin tocar AWS; se usa un placeholder estable
    # para que `render` siga siendo puro. `provision` re-renderiza el IAM
    # con la cuenta real resuelta via `sts get-caller-identity`.
    account = '${account}'

    statements = _build_statements(
        manifest, stage, region=region, account=account
    )
    iam_policy: dict[str, Any] = {
        'Version': '2012-10-17',
        'Statement': statements,
    }

    return RenderedLambda(
        name=name,
        function_name=function_name,
        runtime=str(manifest['runtime']),
        architecture=str(manifest.get('architecture', 'arm64')),
        handler=str(manifest['handler']),
        memory=int(manifest.get('memory', 256)),
        timeout=int(manifest.get('timeout', 30)),
        env_vars=_build_env_vars(manifest, stage),
        iam_policy=iam_policy,
        trigger=_build_trigger(manifest),
        role_name=function_name,
    )


def _resolve_account(*, profile: str | None, region: str) -> str:
    """Resuelve el AWS Account ID via `sts get-caller-identity`."""
    result = aws(
        ['sts', 'get-caller-identity'],
        profile=profile,
        region=region,
        parse_json=True,
    )
    return str(result.json['Account'])


# Fragmentos del stderr de AWS que indican "el recurso ya existe". Un
# `create-*` que falla con uno de estos es idempotente: se ignora para
# que `provision` con `Action.CREATE` sea re-ejecutable (AC-2.8). Cada
# servicio AWS usa su propia excepcion y redaccion: IAM
# `EntityAlreadyExists`, Logs `ResourceAlreadyExistsException`, Lambda
# `ResourceConflictException` con "Function already exist".
_ALREADY_EXISTS_MARKERS = (
    'ResourceAlreadyExistsException',
    'ResourceConflictException',
    'EntityAlreadyExists',
    'already exist',
)


def _aws_create(
    args: list[str],
    *,
    profile: str | None,
    region: str,
    parse_json: bool = False,
) -> AwsResult | None:
    """Ejecuta un `create-*` AWS tolerando "el recurso ya existe".

    Si el comando falla porque el recurso ya existe (re-ejecucion de un
    `CREATE` tras un deploy parcial), devuelve None en vez de abortar.
    Cualquier otro error se propaga como `AwsError`.

    Parameters
    ----------
    args : list[str]
        Argumentos del comando `create-*`.
    profile : str | None
        Perfil AWS CLI.
    region : str
        Region AWS.
    parse_json : bool
        Si True, parsea la salida como JSON.

    Returns
    -------
    AwsResult | None
        El resultado del comando, o None si el recurso ya existia.
    """
    try:
        return aws(
            args,
            profile=profile,
            region=region,
            parse_json=parse_json,
        )
    except AwsError as exc:
        if any(marker in exc.stderr for marker in _ALREADY_EXISTS_MARKERS):
            return None
        raise


def _concrete_iam_policy(
    rendered: RenderedLambda, account: str
) -> dict[str, Any]:
    """Reemplaza el placeholder `${account}` por la cuenta real en el IAM."""
    import json

    payload = json.dumps(rendered.iam_policy).replace('${account}', account)
    return json.loads(payload)


def _environment_arg(env_vars: dict[str, str]) -> str:
    """Serializa las env vars al formato `--environment` del AWS CLI.

    `aws lambda create-function --environment` espera el JSON estructurado
    `{"Variables": {...}}` — NO el shorthand `Variables={...}`, que el CLI
    interpreta mal cuando los valores traen caracteres especiales.
    """
    import json

    return json.dumps({'Variables': env_vars}, sort_keys=True)


def _create_iam_role(
    rendered: RenderedLambda,
    policy: dict[str, Any],
    account: str,
    *,
    profile: str | None,
    region: str,
    resources: dict[str, str | None],
) -> None:
    """Crea el rol IAM, le aplica la policy inline y la de logs basicos.

    Idempotente: si el rol ya existe (re-ejecucion tras un deploy
    parcial), reconstruye su ARN y re-aplica las politicas (que son
    idempotentes).
    """
    import json

    role_result = _aws_create(
        [
            'iam',
            'create-role',
            '--role-name',
            rendered.role_name,
            '--assume-role-policy-document',
            json.dumps(_LAMBDA_TRUST_POLICY),
        ],
        profile=profile,
        region=region,
        parse_json=True,
    )
    if role_result is not None:
        resources['role_arn'] = str(role_result.json['Role']['Arn'])
    else:
        # El rol ya existia: el ARN de un rol IAM es deterministico.
        resources['role_arn'] = (
            f'arn:aws:iam::{account}:role/{rendered.role_name}'
        )
    resources['role_name'] = rendered.role_name

    aws(
        [
            'iam',
            'put-role-policy',
            '--role-name',
            rendered.role_name,
            '--policy-name',
            _INLINE_POLICY_NAME,
            '--policy-document',
            json.dumps(policy),
        ],
        profile=profile,
        region=region,
    )
    aws(
        [
            'iam',
            'attach-role-policy',
            '--role-name',
            rendered.role_name,
            '--policy-arn',
            _BASIC_EXECUTION_POLICY_ARN,
        ],
        profile=profile,
        region=region,
    )


def _create_log_group(
    rendered: RenderedLambda,
    *,
    profile: str | None,
    region: str,
    resources: dict[str, str | None],
) -> None:
    """Crea el LogGroup del Lambda y le fija la retencion a 7 dias.

    Idempotente: si el LogGroup ya existe, solo re-aplica la retencion.
    """
    log_group = f'/aws/lambda/{rendered.function_name}'
    _aws_create(
        ['logs', 'create-log-group', '--log-group-name', log_group],
        profile=profile,
        region=region,
    )
    aws(
        [
            'logs',
            'put-retention-policy',
            '--log-group-name',
            log_group,
            '--retention-in-days',
            str(_LOG_RETENTION_DAYS),
        ],
        profile=profile,
        region=region,
    )
    resources['log_group'] = log_group


def _create_function(
    rendered: RenderedLambda,
    zip_path: Path,
    role_arn: str,
    *,
    profile: str | None,
    region: str,
    resources: dict[str, str | None],
) -> None:
    """Crea la funcion Lambda con el artefacto `build.zip`.

    Idempotente: si la funcion ya existe (re-ejecucion de un `CREATE`
    tras un deploy parcial), reconcilia el codigo y la config en vez de
    abortar.
    """
    result = _aws_create(
        [
            'lambda',
            'create-function',
            '--function-name',
            rendered.function_name,
            '--runtime',
            rendered.runtime,
            '--role',
            role_arn,
            '--handler',
            rendered.handler,
            '--zip-file',
            f'fileb://{zip_path}',
            '--memory-size',
            str(rendered.memory),
            '--timeout',
            str(rendered.timeout),
            '--architectures',
            rendered.architecture,
            '--environment',
            _environment_arg(rendered.env_vars),
            '--tracing-config',
            'Mode=Active',
        ],
        profile=profile,
        region=region,
        parse_json=True,
    )
    resources['function_name'] = rendered.function_name
    if result is not None and result.json:
        resources['function_arn'] = str(result.json.get('FunctionArn'))
    elif result is None:
        # La funcion ya existia: reconcilia codigo + config.
        _provision_update_code(
            rendered, zip_path, profile=profile, region=region
        )
        _provision_update_config(rendered, profile=profile, region=region)


def _ssm_value(path: str, *, profile: str | None, region: str) -> str:
    """Lee el valor de un parametro SSM (publicado por la infra)."""
    result = aws(
        ['ssm', 'get-parameter', '--name', path],
        profile=profile,
        region=region,
        parse_json=True,
    )
    return str(result.json['Parameter']['Value'])


def _wire_http_trigger(
    rendered: RenderedLambda,
    stage: str,
    account: str,
    *,
    profile: str | None,
    region: str,
    resources: dict[str, str | None],
) -> None:
    """Conecta el Lambda a la API Gateway compartida (trigger `http`)."""
    trigger = rendered.trigger
    api_id = _ssm_value(
        f'/portfolio/{stage}/api_gateway/portfolio-api/id',
        profile=profile,
        region=region,
    )
    root_id = _ssm_value(
        f'/portfolio/{stage}/api_gateway/portfolio-api/root-resource-id',
        profile=profile,
        region=region,
    )
    path_part = (trigger.path or '').lstrip('/')

    resource_result = aws(
        [
            'apigateway',
            'create-resource',
            '--rest-api-id',
            api_id,
            '--parent-id',
            root_id,
            '--path-part',
            path_part,
        ],
        profile=profile,
        region=region,
        parse_json=True,
    )
    resource_id = str(resource_result.json['id'])
    resources['api_resource_id'] = resource_id
    resources['api_method'] = f'{trigger.method} {trigger.path}'

    aws(
        [
            'apigateway',
            'put-method',
            '--rest-api-id',
            api_id,
            '--resource-id',
            resource_id,
            '--http-method',
            str(trigger.method),
            '--authorization-type',
            'NONE',
        ],
        profile=profile,
        region=region,
    )
    invoke_arn = (
        f'arn:aws:apigateway:{region}:lambda:path/2015-03-31/functions/'
        f'arn:aws:lambda:{region}:{account}:function:'
        f'{rendered.function_name}/invocations'
    )
    aws(
        [
            'apigateway',
            'put-integration',
            '--rest-api-id',
            api_id,
            '--resource-id',
            resource_id,
            '--http-method',
            str(trigger.method),
            '--type',
            'AWS_PROXY',
            '--integration-http-method',
            'POST',
            '--uri',
            invoke_arn,
        ],
        profile=profile,
        region=region,
    )
    aws(
        [
            'apigateway',
            'create-deployment',
            '--rest-api-id',
            api_id,
            '--stage-name',
            stage,
        ],
        profile=profile,
        region=region,
    )
    source_arn = (
        f'arn:aws:execute-api:{region}:{account}:{api_id}/{stage}/'
        f'{trigger.method}{trigger.path}'
    )
    aws(
        [
            'lambda',
            'add-permission',
            '--function-name',
            rendered.function_name,
            '--statement-id',
            f'apigw-{stage}',
            '--action',
            'lambda:InvokeFunction',
            '--principal',
            'apigateway.amazonaws.com',
            '--source-arn',
            source_arn,
        ],
        profile=profile,
        region=region,
    )


def _wire_table_changes_trigger(
    rendered: RenderedLambda,
    stage: str,
    *,
    profile: str | None,
    region: str,
    resources: dict[str, str | None],
) -> None:
    """Conecta el Lambda a los DynamoDB Streams (`on-table-changes`)."""
    uuids: list[str] = []
    for short_name in rendered.trigger.tables:
        stream_arn = _ssm_value(
            f'/portfolio/{stage}/dynamodb/{short_name}/stream-arn',
            profile=profile,
            region=region,
        )
        result = aws(
            [
                'lambda',
                'create-event-source-mapping',
                '--function-name',
                rendered.function_name,
                '--event-source-arn',
                stream_arn,
                '--starting-position',
                'LATEST',
                '--batch-size',
                '100',
                '--maximum-batching-window-in-seconds',
                '10',
                '--function-response-types',
                'ReportBatchItemFailures',
            ],
            profile=profile,
            region=region,
            parse_json=True,
        )
        if result.json:
            uuids.append(str(result.json.get('UUID')))
    resources['event_source_uuids'] = ','.join(uuids)


def _wire_trigger(
    rendered: RenderedLambda,
    stage: str,
    account: str,
    *,
    profile: str | None,
    region: str,
    resources: dict[str, str | None],
) -> None:
    """Conecta el trigger del Lambda segun su tipo."""
    if rendered.trigger.type == 'http':
        _wire_http_trigger(
            rendered,
            stage,
            account,
            profile=profile,
            region=region,
            resources=resources,
        )
    elif rendered.trigger.type == 'on-table-changes':
        _wire_table_changes_trigger(
            rendered,
            stage,
            profile=profile,
            region=region,
            resources=resources,
        )


def _provision_create(
    rendered: RenderedLambda,
    zip_path: Path,
    *,
    profile: str | None,
    region: str,
    resources: dict[str, str | None],
) -> None:
    """Secuencia `Action.CREATE`: rol, logs, funcion, wiring del trigger.

    Cada paso registra su identificador en `resources` ANTES de pasar al
    siguiente, de modo que un fallo a mitad de camino deja el estado con
    los recursos ya creados y la re-ejecucion es idempotente (AC-2.8).
    """
    account = _resolve_account(profile=profile, region=region)
    policy = _concrete_iam_policy(rendered, account)

    _create_iam_role(
        rendered,
        policy,
        account,
        profile=profile,
        region=region,
        resources=resources,
    )
    _create_log_group(
        rendered,
        profile=profile,
        region=region,
        resources=resources,
    )

    # El rol recien creado puede no estar disponible aun para
    # `create-function`: se espera la propagacion IAM.
    time.sleep(_IAM_PROPAGATION_SECONDS)

    role_arn = resources['role_arn']
    _create_function(
        rendered,
        zip_path,
        str(role_arn),
        profile=profile,
        region=region,
        resources=resources,
    )
    _wire_trigger(
        rendered,
        rendered.function_name.rsplit('-', 1)[-1],
        account,
        profile=profile,
        region=region,
        resources=resources,
    )


def _wait_function_active(
    function_name: str, *, profile: str | None, region: str
) -> None:
    """Espera a que la funcion Lambda este lista para un update.

    Tras `create-function` o un `update-function-*`, la funcion queda en
    estado `Pending` unos segundos; un update concurrente falla con
    `ResourceConflictException`. `aws lambda wait function-updated-v2`
    bloquea hasta que `LastUpdateStatus` sale de `InProgress`.
    """
    aws(
        [
            'lambda',
            'wait',
            'function-updated-v2',
            '--function-name',
            function_name,
        ],
        profile=profile,
        region=region,
        check=False,
    )


def _provision_update_code(
    rendered: RenderedLambda,
    zip_path: Path,
    *,
    profile: str | None,
    region: str,
) -> None:
    """Secuencia `Action.UPDATE_CODE`: solo `update-function-code`."""
    _wait_function_active(
        rendered.function_name, profile=profile, region=region
    )
    aws(
        [
            'lambda',
            'update-function-code',
            '--function-name',
            rendered.function_name,
            '--zip-file',
            f'fileb://{zip_path}',
        ],
        profile=profile,
        region=region,
    )


def _provision_update_config(
    rendered: RenderedLambda,
    *,
    profile: str | None,
    region: str,
) -> None:
    """Secuencia `Action.UPDATE_CONFIG`: config de funcion + IAM inline."""
    import json

    account = _resolve_account(profile=profile, region=region)
    policy = _concrete_iam_policy(rendered, account)

    _wait_function_active(
        rendered.function_name, profile=profile, region=region
    )
    aws(
        [
            'lambda',
            'update-function-configuration',
            '--function-name',
            rendered.function_name,
            '--runtime',
            rendered.runtime,
            '--handler',
            rendered.handler,
            '--memory-size',
            str(rendered.memory),
            '--timeout',
            str(rendered.timeout),
            '--environment',
            _environment_arg(rendered.env_vars),
        ],
        profile=profile,
        region=region,
    )
    aws(
        [
            'iam',
            'put-role-policy',
            '--role-name',
            rendered.role_name,
            '--policy-name',
            _INLINE_POLICY_NAME,
            '--policy-document',
            json.dumps(policy),
        ],
        profile=profile,
        region=region,
    )


def provision(
    rendered: RenderedLambda,
    *,
    action: Action,
    zip_path: Path,
    previous: LambdaState | None,
    profile: str | None,
    region: str,
) -> LambdaState:
    """Ejecuta las llamadas AWS CLI segun `action`. Devuelve el estado nuevo.

    Parameters
    ----------
    rendered : RenderedLambda
        Lambda renderizado por `render`.
    action : Action
        Accion decidida por `state.diff` (CREATE / UPDATE_* / NOOP).
    zip_path : Path
        Ruta al `build.zip` del artefacto de deploy.
    previous : LambdaState | None
        Estado previo (None si nunca se deployo).
    profile : str | None
        Perfil AWS CLI.
    region : str
        Region AWS.

    Returns
    -------
    LambdaState
        Estado nuevo, con los identificadores de los recursos creados. Si
        `provision` falla a mitad de camino, el estado parcial queda en la
        excepcion via `resources` ya poblado del llamador.
    """
    from serverless.state import Action as _Action

    stage = rendered.function_name.rsplit('-', 1)[-1]
    resources: dict[str, str | None] = dict(
        previous.resources if previous else {}
    )

    if action == _Action.NOOP:
        return _build_state(rendered, stage, resources)

    try:
        if action == _Action.CREATE:
            _provision_create(
                rendered,
                zip_path,
                profile=profile,
                region=region,
                resources=resources,
            )
        elif action == _Action.UPDATE_CODE:
            _provision_update_code(
                rendered, zip_path, profile=profile, region=region
            )
        elif action == _Action.UPDATE_CONFIG:
            _provision_update_config(rendered, profile=profile, region=region)
        elif action == _Action.UPDATE_BOTH:
            _provision_update_code(
                rendered, zip_path, profile=profile, region=region
            )
            _provision_update_config(rendered, profile=profile, region=region)
    except Exception as exc:
        # El estado parcial (con role_arn / log_group ya creados) se
        # adjunta a la excepcion para que el llamador lo persista y la
        # re-ejecucion sea idempotente.
        exc.partial_state = _build_state(rendered, stage, resources)
        raise

    return _build_state(rendered, stage, resources)


def rendered_config(rendered: RenderedLambda) -> dict[str, Any]:
    """Subset de `RenderedLambda` que define el `config_hash` del diff.

    Tanto `provision` (al construir el estado nuevo) como
    `cmd_deploy_lambda` (al decidir la accion del diff) hashean ESTE
    dict, asi el `config_hash` es consistente entre el deploy y el diff.

    Parameters
    ----------
    rendered : RenderedLambda
        Lambda renderizado por `render`.

    Returns
    -------
    dict[str, Any]
        Campos de config que, al cambiar, fuerzan un re-deploy de config.
    """
    return {
        'runtime': rendered.runtime,
        'architecture': rendered.architecture,
        'handler': rendered.handler,
        'memory': rendered.memory,
        'timeout': rendered.timeout,
        'env_vars': rendered.env_vars,
        'iam_policy': rendered.iam_policy,
    }


def _build_state(
    rendered: RenderedLambda,
    stage: str,
    resources: dict[str, str | None],
) -> LambdaState:
    """Construye el `LambdaState` resultante de un `provision`."""
    from serverless.state import config_hash

    return LambdaState(
        scope=rendered.name,
        stage=stage,
        config_hash=config_hash(rendered_config(rendered)),
        code_hash='',
        resources=resources,
        updated_at=now_iso(),
    )


def deprovision(
    state: LambdaState,
    *,
    profile: str | None,
    region: str,
) -> None:
    """Borra los recursos del Lambda en orden inverso al de creacion.

    Orden: wiring del trigger -> funcion -> rol IAM -> LogGroup. Cada
    `aws` se invoca con `check=False` para que la ausencia de un recurso
    (ya borrado) no aborte el resto del borrado.

    Parameters
    ----------
    state : LambdaState
        Estado del Lambda a destruir.
    profile : str | None
        Perfil AWS CLI.
    region : str
        Region AWS.
    """
    resources = state.resources

    _deprovision_trigger(state, profile=profile, region=region)

    function_name = resources.get('function_name')
    if function_name:
        aws(
            [
                'lambda',
                'delete-function',
                '--function-name',
                function_name,
            ],
            profile=profile,
            region=region,
            check=False,
        )

    role_name = resources.get('role_name')
    if role_name:
        aws(
            [
                'iam',
                'delete-role-policy',
                '--role-name',
                role_name,
                '--policy-name',
                _INLINE_POLICY_NAME,
            ],
            profile=profile,
            region=region,
            check=False,
        )
        aws(
            [
                'iam',
                'detach-role-policy',
                '--role-name',
                role_name,
                '--policy-arn',
                _BASIC_EXECUTION_POLICY_ARN,
            ],
            profile=profile,
            region=region,
            check=False,
        )
        aws(
            ['iam', 'delete-role', '--role-name', role_name],
            profile=profile,
            region=region,
            check=False,
        )

    log_group = resources.get('log_group')
    if log_group:
        aws(
            [
                'logs',
                'delete-log-group',
                '--log-group-name',
                log_group,
            ],
            profile=profile,
            region=region,
            check=False,
        )


def _deprovision_trigger(
    state: LambdaState,
    *,
    profile: str | None,
    region: str,
) -> None:
    """Borra el wiring del trigger (API method/resource o event mapping)."""
    resources = state.resources

    uuids = resources.get('event_source_uuids')
    if uuids:
        for uuid in uuids.split(','):
            if not uuid:
                continue
            aws(
                [
                    'lambda',
                    'delete-event-source-mapping',
                    '--uuid',
                    uuid,
                ],
                profile=profile,
                region=region,
                check=False,
            )

    function_name = resources.get('function_name')
    api_resource_id = resources.get('api_resource_id')
    if api_resource_id and function_name:
        aws(
            [
                'lambda',
                'remove-permission',
                '--function-name',
                function_name,
                '--statement-id',
                f'apigw-{state.stage}',
            ],
            profile=profile,
            region=region,
            check=False,
        )
        api_id = _ssm_value(
            f'/portfolio/{state.stage}/api_gateway/portfolio-api/id',
            profile=profile,
            region=region,
        )
        aws(
            [
                'apigateway',
                'delete-resource',
                '--rest-api-id',
                api_id,
                '--resource-id',
                api_resource_id,
            ],
            profile=profile,
            region=region,
            check=False,
        )
