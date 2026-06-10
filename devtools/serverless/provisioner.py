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
     En UPDATE_CONFIG y UPDATE_BOTH, ademas, llama a
     `_rewire_trigger_on_update` para que cambios en `trigger.*` y
     `snap_start` se materializen en API GW / EventSourceMapping
     (URI con qualifier `:live`, statement-id del add-permission).
     El wiring corre `_cleanup_legacy_permissions` antes del
     add-permission canonico, borrando statements obsoletos del
     resource-policy del Lambda (legacy SAM o devtools previo con
     qualifier distinto), scoped por `source_arn` para NO tocar
     permisos legitimos de otros origenes.
  3. `deprovision(state, ...)` — borra los recursos en orden inverso.

La traduccion `uses` -> IAM resuelve los ARNs a strings concretos
(cuenta y region reales), sin `Fn::Sub` ni `Fn::ImportValue`. Los
identificadores de infra (Stream ARN, ApiId) se leen de SSM con
`aws ssm get-parameter`.
"""

from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
import json
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
_VALID_ENV_STAGES = ('default', 'dev', 'prod')

# Tipos de trigger soportados. `on-table-changes` se elimino con el
# stream_processor (spec direct-neon-writes): los Lambdas HTTP escriben
# directo a Neon en vez de via DDB Stream. El trigger `sqs` se elimino
# al migrar el trabajo async a invoke Lambda->Lambda (sin SQS).
_VALID_TRIGGERS = ('direct', 'http')

# Metodos HTTP soportados en un trigger `http`. OPTIONS lo gestiona el
# wiring CORS (MOCK), no se declara aqui.
_VALID_HTTP_METHODS = ('GET', 'POST', 'PUT', 'PATCH', 'DELETE')

# Espera de propagacion del rol IAM recien creado antes de
# `create-function`: un rol nuevo puede no estar disponible aun.
_IAM_PROPAGATION_SECONDS = 10

# Tablas DynamoDB: nombre corto -> definicion del catalogo. Sin
# marcadores CloudFormation: nombres y ARNs concretos. Solo tablas de
# infraestructura (cache + rate-limit). Las tablas `contacts` y
# `tracking` se eliminaron en spec direct-neon-writes — esos datos
# viven ahora en Neon directo.
_TABLES: dict[str, dict[str, str]] = {
    'cache': {
        'physical': 'portfolio-cache-${stage}',
        'env': 'SSM_CACHE_TABLE_PATH',
    },
    'rate-limit-rules': {
        'physical': 'portfolio-rate-limit-rules-${stage}',
        'env': 'SSM_RATE_LIMIT_RULES_TABLE_PATH',
    },
    'rate-limit-buckets': {
        'physical': 'portfolio-rate-limit-buckets-${stage}',
        'env': 'SSM_RATE_LIMIT_BUCKETS_TABLE_PATH',
    },
    'jwt-blacklist': {
        'physical': 'portfolio-jwt-blacklist-${stage}',
        'env': 'SSM_JWT_BLACKLIST_TABLE_PATH',
    },
    'webauthn-challenges': {
        'physical': 'portfolio-webauthn-challenges-${stage}',
        'env': 'SSM_WEBAUTHN_CHALLENGES_TABLE_PATH',
    },
    'email-config': {
        'physical': 'portfolio-email-config-${stage}',
        'env': 'SSM_EMAIL_CONFIG_TABLE_PATH',
    },
}

# El inventario de secretos SSM vive en
# `serverless/lambda/resources/secrets/*.yaml`. Lo consume
# `_secret_def(short_name)` via `serverless.secrets_catalog.Catalog`.

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
        # Scan es read-only: lo usa la invalidacion por tag del cache
        # (shared.cache.invalidation.invalidate_by_tag hace table.scan
        # sobre la tabla cache). Sin esto, cualquier Lambda que escriba
        # el CV (cv_admin) revienta con AccessDeniedException al
        # invalidar el tag 'cv' tras el commit.
        'dynamodb:Scan',
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
        `direct` | `http`.
    methods : tuple[str, ...]
        Metodos HTTP del endpoint (solo `http`). Ej. `('POST',)` o
        `('GET', 'POST')`. Tupla (no list) porque el dataclass es frozen y
        `asdict()` entra al config-hash de drift (debe ser determinista).
    path : str | None
        Path del endpoint (solo `http`). Ej. `/contact`.
    """

    type: str
    methods: tuple[str, ...] = ()
    path: str | None = None


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
    snap_start: bool = False
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


def _secret_def(short_name: str) -> dict[str, Any]:
    """Resuelve un nombre corto de secreto a su definicion del catalogo.

    Lee del catalogo YAML en `serverless/lambda/resources/secrets/`
    (fuente de verdad). Devuelve la estructura {path, env, stages}
    compatible con los consumers de este modulo. `stages` es el set de
    stages donde el secreto existe (para que el provisioner NO inyecte el
    path/IAM en un stage donde el catalogo no lo declara).
    """
    from serverless.secrets_catalog import Catalog
    from serverless.secrets_catalog import CatalogError

    try:
        spec = Catalog.load().get(short_name)
    except CatalogError as exc:
        raise ManifestError(str(exc)) from exc

    return {
        'path': spec.path_template,
        'env': spec.target_env_var,
        'stages': spec.stages,
    }


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
        # Omitir el secreto si el catalogo NO lo declara en este stage
        # (ej. turnstile-bypass-public-key solo existe en dev/stage; un
        # deploy a prod no debe inyectar un path SSM inexistente).
        if stage not in sdef['stages']:
            continue
        env[sdef['env']] = _interp(sdef['path'], stage)

    env.update(_invoke_bucket_env_vars(uses, stage))

    return env


def _invoke_bucket_env_vars(uses: dict[str, Any], stage: str) -> dict[str, str]:
    """Env vars derivadas de `uses.invokes` y `uses.buckets`.

    - invokes -> LAMBDA_<UPPER>_FUNCTION_NAME (el caller resuelve el nombre
      del target sin hardcodear). El short-name del manifest se da con guion
      bajo (send_email) y el nombre fisico usa guion (portfolio-send-email-X).
    - buckets -> S3_<UPPER>_BUCKET con el nombre interpolado.
    """
    env: dict[str, str] = {}
    for target in uses.get('invokes') or []:
        upper = str(target).upper().replace('-', '_')
        dashed = str(target).replace('_', '-')
        env[f'LAMBDA_{upper}_FUNCTION_NAME'] = f'portfolio-{dashed}-{stage}'

    for bucket in uses.get('buckets') or []:
        if not isinstance(bucket, dict):
            continue
        name_full = _interp(str(bucket['name']), stage)
        short = name_full.removeprefix('portfolio-').removesuffix(f'-{stage}')
        env_key = 'S3_' + short.upper().replace('-', '_') + '_BUCKET'
        env[env_key] = name_full

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
                    # Indices (GSI/LSI) de la tabla: el Query sobre un GSI
                    # (ej. jwt-blacklist#by_family_id) exige el ARN del
                    # indice ademas del de la tabla. Scoped a la tabla; las
                    # tablas sin indices simplemente no matchean nada.
                    f'arn:aws:dynamodb:{region}:{account}:table/{physical}/index/*',
                ],
            }
        )
        table_ssm_paths.append(
            _interp(_ssm_path('dynamodb', short_name, 'name'), stage)
        )
    return statements, table_ssm_paths


def _kms_statements(
    kms_uses: list[Any],
    *,
    region: str,
    account: str,
) -> list[dict[str, Any]]:
    """Traduce `uses.kms` a Statements `kms:Encrypt`/`Decrypt` directos.

    CMK directa (NO via SSM, NO GenerateDataKey): para cifrar secretos
    at-rest como el TOTP secret (plan 02-auth-mfa, decision 1). Cada
    entrada es `{alias, actions:[Encrypt, Decrypt, ...]}`. Resource =
    `key/*` (mismo alcance que el bloque `kms:Decrypt` de SSM; la cuenta
    solo tiene la CMK `portfolio-lambdas` ademas de las AWS-managed).
    """
    statements: list[dict[str, Any]] = []
    for kms_use in kms_uses:
        if not isinstance(kms_use, dict):
            continue
        actions = [f'kms:{action}' for action in kms_use.get('actions', [])]
        if not actions:
            continue
        statements.append(
            {
                'Effect': 'Allow',
                'Action': actions,
                'Resource': f'arn:aws:kms:{region}:{account}:key/*',
            }
        )
    return statements


def _invoke_statements(
    targets: list[Any],
    stage: str,
    *,
    region: str,
    account: str,
) -> list[dict[str, Any]]:
    """Traduce `uses.invokes` a un Statement `lambda:InvokeFunction`.

    Async invoke Lambda->Lambda (reemplaza SQS). El short-name del manifest
    se da con guion bajo (ej. `send_email`) y el nombre fisico de la funcion
    usa guion (`portfolio-send-email-<stage>`). Resource = ARN base (sin
    qualifier: el invoke async pega a `$LATEST`).
    """
    arns = [
        f'arn:aws:lambda:{region}:{account}:function:'
        f'portfolio-{str(target).replace("_", "-")}-{stage}'
        for target in targets
    ]
    if not arns:
        return []
    return [
        {
            'Effect': 'Allow',
            'Action': ['lambda:InvokeFunction'],
            'Resource': arns,
        }
    ]


def _bucket_statements(
    buckets: list[Any],
    stage: str,
) -> list[dict[str, Any]]:
    """Traduce `uses.buckets` a Statements S3 por bucket.

    Solo se soporta `access: read`: `s3:GetObject` sobre las keys +
    `s3:ListBucket` sobre el bucket (listar un prefijo — el restore del
    Lambda db enumera el snapshot con list_objects_v2 antes de bajarlo).
    El nombre del bucket NO va por SSM: se inyecta como env var
    S3_<X>_BUCKET.
    """
    statements: list[dict[str, Any]] = []
    for bucket in buckets:
        if not isinstance(bucket, dict):
            continue
        name_full = _interp(str(bucket['name']), stage)
        access = bucket.get('access', 'read')
        if access != 'read':
            raise ManifestError(
                f'acceso invalido {access!r} para el bucket '
                f'{name_full!r}. Solo se soporta read.',
            )
        statements.append(
            {
                'Effect': 'Allow',
                'Action': ['s3:GetObject'],
                'Resource': f'arn:aws:s3:::{name_full}/*',
            }
        )
        statements.append(
            {
                'Effect': 'Allow',
                'Action': ['s3:ListBucket'],
                'Resource': f'arn:aws:s3:::{name_full}',
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
    Statement SES. Sin `Fn::Sub`: ARNs concretos.
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
        # No conceder IAM sobre un secreto que el catalogo no declara en
        # este stage (coherente con _build_env_vars: el path no se inyecta).
        if stage not in sdef['stages']:
            continue
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

    statements.extend(
        _kms_statements(uses.get('kms') or [], region=region, account=account)
    )

    statements.extend(
        _invoke_statements(
            uses.get('invokes') or [], stage, region=region, account=account
        )
    )

    statements.extend(_bucket_statements(uses.get('buckets') or [], stage))

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

    return statements


def _normalize_http_methods(
    *,
    method: Any,
    methods: Any,
) -> tuple[str, ...]:
    """Normaliza `trigger.method` (str) o `trigger.methods` (lista) a tupla.

    Acepta UNA de las dos llaves (no ambas). Cada metodo se upper-casea,
    se valida contra `_VALID_HTTP_METHODS` y se deduplica preservando el
    orden de aparicion.

    Raises
    ------
    ManifestError
        Si estan ambas llaves, si falta el metodo, o si un metodo es
        invalido.
    """
    if method and methods:
        raise ManifestError(
            "trigger http: usar 'method' (string) O 'methods' (lista), "
            'no ambos.',
        )
    if method:
        raw = [method]
    elif methods:
        if not isinstance(methods, (list, tuple)):
            raise ManifestError("trigger http: 'methods' debe ser una lista.")
        raw = list(methods)
    else:
        raise ManifestError(
            "trigger http requiere 'method' o 'methods' y 'path'.",
        )

    normalized: list[str] = []
    for item in raw:
        verb = str(item).strip().upper()
        if verb not in _VALID_HTTP_METHODS:
            raise ManifestError(
                f'trigger http: metodo invalido {item!r}. '
                f'Validos: {", ".join(_VALID_HTTP_METHODS)}',
            )
        if verb not in normalized:
            normalized.append(verb)
    return tuple(normalized)


def _build_trigger(manifest: dict[str, Any]) -> TriggerSpec:
    """Construye el `TriggerSpec` desde el bloque `trigger` del manifiesto.

    Soporta `trigger.method` (string, ej. `POST`) y `trigger.methods`
    (lista, ej. `[GET, POST]`) — exclusivos. Internamente siempre guarda
    una tupla de metodos.

    Raises
    ------
    ManifestError
        Si el tipo de trigger no es valido, si falta `method`/`methods` o
        `path` en un trigger `http`, o si un metodo es invalido.
    """
    trigger = manifest.get('trigger') or {}
    ttype = trigger.get('type')

    if ttype not in _VALID_TRIGGERS:
        raise ManifestError(
            f'trigger.type invalido: {ttype!r}. '
            f'Validos: {", ".join(_VALID_TRIGGERS)}',
        )

    if ttype == 'http':
        path = trigger.get('path')
        if not path:
            raise ManifestError("trigger http requiere 'path'.")
        methods = _normalize_http_methods(
            method=trigger.get('method'),
            methods=trigger.get('methods'),
        )
        return TriggerSpec(type='http', methods=methods, path=path)

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
        snap_start=bool(manifest.get('snap_start', False)),
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
            # X-Ray NO se usa en este backend (sin aws-xray-sdk). PassThrough
            # = no instrumenta. Ver .claude/rules/lambda-config.md.
            '--tracing-config',
            'Mode=PassThrough',
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


def _wire_cors_options(
    *,
    api_id: str,
    resource_id: str,
    methods: tuple[str, ...],
    profile: str | None,
    region: str,
) -> None:
    """Crea el method OPTIONS para CORS preflight en un resource de API GW.

    Patron estandar de CORS:
    - PUT method OPTIONS authType=NONE.
    - MOCK integration con request template para application/json y
      passthroughBehavior=WHEN_NO_TEMPLATES (sin este flag, browsers que
      hacen preflight sin Content-Type reciben 500).
    - method-response + integration-response con los 4 headers
      Access-Control-* (Origin=*, Methods, Headers, Max-Age=600).

    Headers permitidos: Content-Type + Authorization + los headers Turnstile
    del form de contacto. `Authorization` es obligatorio: los endpoints
    autenticados (/users completo, /auth mfa/webauthn con sesion) reciben
    `Authorization: Bearer <JWT>` del admin; sin el header en el preflight el
    browser bloquea el request con CORS. El OPTIONS es un MOCK (NO ejecuta el
    Lambda), por eso este string debe coincidir con el de
    shared/http/cors.py::cors_headers. Si en el futuro el frontend manda
    headers custom, ampliar aqui (el navegador valida los de
    Access-Control-Request-Headers contra Access-Control-Allow-Headers).

    Idempotente: cada `aws apigateway put-*` acepta re-aplicacion sobre
    una entidad existente (sobrescribe). Para flexibilidad ante re-deploys,
    los errores "ConflictException: Method already exists" se ignoran.
    """
    allowed_headers = (
        'Content-Type,Authorization,X-Turnstile-Token,X-Turnstile-Bypass-Token'
    )
    allowed_methods = ','.join((*methods, 'OPTIONS'))

    # 1. put-method OPTIONS — puede fallar con ConflictException si ya
    # existe. Lo tratamos como noop.
    aws(
        [
            'apigateway',
            'put-method',
            '--rest-api-id',
            api_id,
            '--resource-id',
            resource_id,
            '--http-method',
            'OPTIONS',
            '--authorization-type',
            'NONE',
        ],
        profile=profile,
        region=region,
        check=False,
    )

    # 2. put-integration MOCK
    aws(
        [
            'apigateway',
            'put-integration',
            '--rest-api-id',
            api_id,
            '--resource-id',
            resource_id,
            '--http-method',
            'OPTIONS',
            '--type',
            'MOCK',
            '--request-templates',
            '{"application/json":"{\\"statusCode\\":200}"}',
            '--passthrough-behavior',
            'WHEN_NO_TEMPLATES',
        ],
        profile=profile,
        region=region,
        check=False,
    )

    # 3. put-method-response 200 declarando los 4 headers CORS
    aws(
        [
            'apigateway',
            'put-method-response',
            '--rest-api-id',
            api_id,
            '--resource-id',
            resource_id,
            '--http-method',
            'OPTIONS',
            '--status-code',
            '200',
            '--response-parameters',
            (
                'method.response.header.Access-Control-Allow-Origin=true,'
                'method.response.header.Access-Control-Allow-Methods=true,'
                'method.response.header.Access-Control-Allow-Headers=true,'
                'method.response.header.Access-Control-Max-Age=true'
            ),
        ],
        profile=profile,
        region=region,
        check=False,
    )

    # 4. put-integration-response 200 con los VALORES de los headers
    aws(
        [
            'apigateway',
            'put-integration-response',
            '--rest-api-id',
            api_id,
            '--resource-id',
            resource_id,
            '--http-method',
            'OPTIONS',
            '--status-code',
            '200',
            '--response-parameters',
            (
                '{'
                '"method.response.header.Access-Control-Allow-Origin":"\'*\'",'
                f'"method.response.header.Access-Control-Allow-Methods":"\'{allowed_methods}\'",'
                f'"method.response.header.Access-Control-Allow-Headers":"\'{allowed_headers}\'",'
                '"method.response.header.Access-Control-Max-Age":"\'600\'"'
                '}'
            ),
        ],
        profile=profile,
        region=region,
        check=False,
    )


def _source_arn_matches_path(*, cond_arn: str, stage: str, path: str) -> bool:
    """True si `cond_arn` apunta al mismo `{stage}` + `{path}` del API GW.

    Compara ignorando el segmento de METODO del ARN execute-api
    (`.../{stage}/{method}{path}`): matchea tanto el formato viejo de
    metodo especifico (`{stage}/POST/contact`) como el wildcard nuevo
    (`{stage}/*/contact`). Asi el cleanup sigue cubriendo statements
    legacy de cualquier metodo sobre el mismo path tras migrar al wildcard.
    """
    marker = f'/{stage}/'
    idx = cond_arn.find(marker)
    if idx == -1:
        return False
    tail = cond_arn[idx + len(marker) :]  # ej. 'POST/contact' o '*/contact'
    slash = tail.find('/')
    if slash == -1:
        return False
    arn_path = tail[slash:]  # ej. '/contact'
    return arn_path == path


def _cleanup_legacy_permissions(
    *,
    function_name: str,
    keep_sid: str,
    stage: str,
    path: str,
    profile: str | None,
    region: str,
) -> None:
    """Borra statements obsoletos del resource-policy del Lambda.

    Scoped al mismo `{stage}` + `{path}` del API GW (ignorando el metodo
    del SourceArn): solo elimina statements cuyo SourceArn apunta al mismo
    path (`/contact` para contact-form, cualquier metodo) y cuyo Sid no es
    `keep_sid`. Asi NO toca permisos legitimos de otros origenes
    (EventBridge, otra API GW, otro path).

    Cubre 2 casos reales:
    - Statement legacy de SAM (`portfolio-backend-<stage>-...Permission...`),
      que devtools nunca limpio tras la migracion de SAM a AWS CLI directo.
      Su SourceArn lleva el metodo especifico (`{stage}/POST/contact`); el
      match por path lo cubre aunque el wiring nuevo use wildcard.
    - Statement viejo de devtools cuando cambio el qualifier (`apigw-dev`
      sin live -> `apigw-dev-live` tras activar snap_start).

    Idempotente: si el policy no existe (ResourceNotFoundException) o
    no hay statements obsoletos, no-op.
    """
    pol_result = aws(
        [
            'lambda',
            'get-policy',
            '--function-name',
            function_name,
            '--query',
            'Policy',
            '--output',
            'text',
        ],
        profile=profile,
        region=region,
        check=False,
    )
    raw = (pol_result.stdout or '').strip()
    if not raw or pol_result.returncode != 0:
        return
    try:
        policy = json.loads(raw)
    except ValueError, TypeError:
        return
    for stmt in policy.get('Statement', []) or []:
        sid = stmt.get('Sid', '')
        if not sid or sid == keep_sid:
            continue
        cond_arn = (
            stmt.get('Condition', {})
            .get('ArnLike', {})
            .get('AWS:SourceArn', '')
        )
        if not _source_arn_matches_path(
            cond_arn=cond_arn, stage=stage, path=path
        ):
            continue
        aws(
            [
                'lambda',
                'remove-permission',
                '--function-name',
                function_name,
                '--statement-id',
                sid,
            ],
            profile=profile,
            region=region,
            check=False,
        )


# Backoff para `create-deployment`: API Gateway limita create-deployment a
# ~1 cada pocos segundos por cuenta. Deploys (semi)concurrentes de varios
# lambdas HTTP sobre la MISMA REST API chocan con TooManyRequestsException.
_DEPLOYMENT_RETRY_DELAYS = (3, 8, 20)


def _create_deployment(
    api_id: str,
    stage: str,
    *,
    profile: str | None,
    region: str,
) -> None:
    """`apigateway create-deployment` con retry ante TooManyRequests."""
    delays: tuple[int | None, ...] = (*_DEPLOYMENT_RETRY_DELAYS, None)
    args = [
        'apigateway',
        'create-deployment',
        '--rest-api-id',
        api_id,
        '--stage-name',
        stage,
    ]
    for attempt, delay in enumerate(delays):
        try:
            aws(args, profile=profile, region=region)
        except AwsError as exc:
            if 'TooManyRequests' not in exc.stderr or delay is None:
                raise
            print(
                f'  create-deployment throttled (intento {attempt + 1}), '
                f'reintento en {delay}s'
            )
            time.sleep(delay)
        else:
            return


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

    # Idempotente: si el resource /path ya existe (caso CREATE tras
    # deploy parcial previo o re-corrida del provisioner), reutilizar
    # su id en vez de fallar con BadRequest.
    existing_resources = aws(
        [
            'apigateway',
            'get-resources',
            '--rest-api-id',
            api_id,
            '--query',
            f'items[?pathPart==`{path_part}`].id | [0]',
            '--output',
            'text',
        ],
        profile=profile,
        region=region,
        check=False,
    )
    existing_id = (existing_resources.stdout or '').strip()
    if existing_id and existing_id != 'None':
        resource_id = existing_id
        print(f'  OK  resource /{path_part} ya existe ({resource_id})')
    else:
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
    resources['api_method'] = f'{",".join(trigger.methods)} {trigger.path}'

    # Qualifier: si SnapStart=true, apunta al alias `:live` (necesario
    # para que SnapStart aplique). Sino, $LATEST (sin qualifier).
    qualifier = _snap_start_qualifier(rendered)
    invoke_arn = (
        f'arn:aws:apigateway:{region}:lambda:path/2015-03-31/functions/'
        f'arn:aws:lambda:{region}:{account}:function:'
        f'{rendered.function_name}{qualifier}/invocations'
    )
    # Un par put-method + put-integration por cada metodo HTTP del trigger
    # (ej. GET y POST para /auth: el magic-link entra por GET, el resto del
    # flujo por POST). Idempotente: si el metodo ya existe (re-deploy /
    # UPDATE_CONFIG), put-method falla con ConflictException y se trata como
    # noop; put-integration sobrescribe.
    for http_method in trigger.methods:
        aws(
            [
                'apigateway',
                'put-method',
                '--rest-api-id',
                api_id,
                '--resource-id',
                resource_id,
                '--http-method',
                http_method,
                '--authorization-type',
                'NONE',
            ],
            profile=profile,
            region=region,
            check=False,
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
                http_method,
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
    # CORS preflight: agrega OPTIONS al resource para que los browsers que
    # disparan preflight (Content-Type application/json o headers custom)
    # reciban un 200 con los headers Access-Control-* correctos. Sin esto,
    # API Gateway responde MissingAuthenticationTokenException (HTTP 403) y
    # el browser bloquea la request real. Idempotente — los `put-*` aceptan
    # re-aplicacion sobre un metodo existente. Access-Control-Allow-Methods
    # lista todos los metodos reales + OPTIONS.
    _wire_cors_options(
        api_id=api_id,
        resource_id=resource_id,
        methods=trigger.methods,
        profile=profile,
        region=region,
    )
    _create_deployment(api_id, stage, profile=profile, region=region)
    # source_arn con wildcard de metodo `*`: un solo statement de permiso
    # cubre todos los metodos del path (GET+POST). OPTIONS es MOCK (no
    # invoca el Lambda), asi que el wildcard no causa invocaciones extra.
    source_arn = (
        f'arn:aws:execute-api:{region}:{account}:{api_id}/{stage}/'
        f'*{trigger.path}'
    )
    target_sid = (
        f'apigw-{stage}-live' if rendered.snap_start else f'apigw-{stage}'
    )
    # Borra statements obsoletos del policy del Lambda (legacy SAM o
    # statement viejo de devtools cuando cambio el qualifier). Scoped al
    # mismo source_arn para NO tocar permisos legitimos de otros origenes.
    _cleanup_legacy_permissions(
        function_name=rendered.function_name,
        keep_sid=target_sid,
        stage=stage,
        path=str(trigger.path),
        profile=profile,
        region=region,
    )
    # Borra el statement con el `target_sid` ANTES de re-crearlo: si ya
    # existe con un SourceArn distinto (ej. el viejo `{method}{path}` antes
    # de migrar al wildcard `*{path}`), `add-permission` con check=False NO
    # lo actualizaria (el Sid ya existe -> noop), dejando el GET sin permiso.
    # `_cleanup_legacy_permissions` NO lo cubre (preserva el `keep_sid`).
    # remove-permission es idempotente (noop si no existe).
    #
    # CRITICO con SnapStart: el statement vive en el alias `:live` (el
    # `add-permission` lleva `--qualifier live`). El `remove-permission`
    # DEBE usar el MISMO qualifier o borraria el statement del $LATEST
    # (vacio) y dejaria el del alias intacto -> add-permission no lo
    # sobrescribe (Sid ya existe) -> queda el SourceArn viejo.
    remove_args = [
        'lambda',
        'remove-permission',
        '--function-name',
        rendered.function_name,
        '--statement-id',
        target_sid,
    ]
    if rendered.snap_start:
        remove_args += ['--qualifier', _SNAP_START_ALIAS]
    aws(
        remove_args,
        profile=profile,
        region=region,
        check=False,
    )
    permission_args = [
        'lambda',
        'add-permission',
        '--function-name',
        rendered.function_name,
        '--statement-id',
        target_sid,
        '--action',
        'lambda:InvokeFunction',
        '--principal',
        'apigateway.amazonaws.com',
        '--source-arn',
        source_arn,
    ]
    if rendered.snap_start:
        permission_args += ['--qualifier', _SNAP_START_ALIAS]
    aws(
        permission_args,
        profile=profile,
        region=region,
        check=False,  # Idempotente: el statement-id puede ya existir
    )


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


def _rewire_trigger_on_update(
    rendered: RenderedLambda,
    stage: str,
    *,
    profile: str | None,
    region: str,
    resources: dict[str, str | None],
) -> None:
    """Re-aplica el wiring del trigger en `provision()` con UPDATE_*.

    Antes de este fix, `_wire_trigger` solo corria en `_provision_create`.
    Si un manifest cambiaba `trigger.methods`, `trigger.path` o
    `snap_start` (que afecta el qualifier `:live` de la URI de API GW y
    el statement-id del `add-permission`), el cambio NO se aplicaba al
    redeployar (solo al borrar+recrear). Tambien dejaba colgando el
    statement-id legacy de SAM en Lambdas migrados.

    Cada paso de `_wire_trigger` es idempotente:
    - `get-resources`/`create-resource` reutiliza el resource existente.
    - `put-method`/`put-integration` aceptan re-aplicacion.
    - `_cleanup_legacy_permissions` borra obsoletos antes de `add-permission`.

    Solo aplica a triggers `http`. El trigger `direct` no tiene wiring.
    """
    if rendered.trigger.type != 'http':
        return
    account = _resolve_account(profile=profile, region=region)
    _wire_trigger(
        rendered,
        stage,
        account,
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
    if rendered.snap_start:
        _ensure_snap_start_config(rendered, profile=profile, region=region)
        alias_arn = _publish_and_update_alias(
            rendered,
            profile=profile,
            region=region,
        )
        if alias_arn:
            resources['snap_start_alias_arn'] = alias_arn
    _wire_trigger(
        rendered,
        rendered.function_name.rsplit('-', 1)[-1],
        account,
        profile=profile,
        region=region,
        resources=resources,
    )
    # Si el manifest tiene snap_start=False pero la funcion YA existia en
    # AWS con SnapStart activo (CREATE por state local perdido), hay que
    # apagarlo + liberar sus snapshots. No-op barato en una funcion
    # genuinamente nueva (sin SnapStart ni versiones). Corre tras el
    # wiring (que ya apunto a $LATEST con qualifier vacio).
    _disable_snap_start(rendered, profile=profile, region=region)


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


# --------------------------------------------------------------------------
# SnapStart (publish-version + alias `live`)
# --------------------------------------------------------------------------
_SNAP_START_ALIAS = 'live'


def _ensure_snap_start_config(
    rendered: RenderedLambda,
    *,
    profile: str | None,
    region: str,
) -> None:
    """Aplica `--snap-start ApplyOn=PublishedVersions` (idempotente).

    Si la funcion ya tiene SnapStart activo, este update es no-op (AWS
    devuelve la misma config sin cambios). Si no, lo activa.
    """
    target = 'PublishedVersions' if rendered.snap_start else 'None'
    current = aws(
        [
            'lambda',
            'get-function-configuration',
            '--function-name',
            rendered.function_name,
        ],
        profile=profile,
        region=region,
        parse_json=True,
        check=False,
    )
    current_apply = (
        (current.json or {}).get('SnapStart', {}).get('ApplyOn', 'None')
    )
    if current_apply == target:
        return
    _wait_function_active(
        rendered.function_name,
        profile=profile,
        region=region,
    )
    aws(
        [
            'lambda',
            'update-function-configuration',
            '--function-name',
            rendered.function_name,
            '--snap-start',
            f'ApplyOn={target}',
        ],
        profile=profile,
        region=region,
    )


def _publish_and_update_alias(
    rendered: RenderedLambda,
    *,
    profile: str | None,
    region: str,
) -> str | None:
    """Publica nueva version + actualiza alias `live` para SnapStart.

    Solo se invoca cuando `rendered.snap_start=True`. Returns el ARN del
    alias (o None si snap_start=False).
    """
    if not rendered.snap_start:
        return None
    _wait_function_active(
        rendered.function_name,
        profile=profile,
        region=region,
    )
    pub = aws(
        [
            'lambda',
            'publish-version',
            '--function-name',
            rendered.function_name,
            '--description',
            f'devtools deploy at {now_iso()}',
        ],
        profile=profile,
        region=region,
        parse_json=True,
    )
    version = (pub.json or {}).get('Version')
    if not version:
        raise RuntimeError(
            f'publish-version de {rendered.function_name} no retorno Version',
        )

    # Crear o actualizar alias `live`.
    existing = aws(
        [
            'lambda',
            'get-alias',
            '--function-name',
            rendered.function_name,
            '--name',
            _SNAP_START_ALIAS,
        ],
        profile=profile,
        region=region,
        parse_json=True,
        check=False,
    )
    if existing.ok:
        aws(
            [
                'lambda',
                'update-alias',
                '--function-name',
                rendered.function_name,
                '--name',
                _SNAP_START_ALIAS,
                '--function-version',
                version,
            ],
            profile=profile,
            region=region,
        )
        alias_arn = (existing.json or {}).get('AliasArn', '')
    else:
        created = aws(
            [
                'lambda',
                'create-alias',
                '--function-name',
                rendered.function_name,
                '--name',
                _SNAP_START_ALIAS,
                '--function-version',
                version,
            ],
            profile=profile,
            region=region,
            parse_json=True,
        )
        alias_arn = (created.json or {}).get('AliasArn', '')
    print(f'  OK  alias {_SNAP_START_ALIAS} -> version {version}')
    _prune_old_versions(
        rendered.function_name,
        keep_version=version,
        profile=profile,
        region=region,
    )
    return alias_arn


def _prune_old_versions(
    function_name: str,
    *,
    keep_version: str | None,
    profile: str | None,
    region: str,
) -> None:
    """Borra snapshots SnapStart facturables (versiones publicadas).

    Cada version publicada con SnapStart retiene un snapshot que AWS
    factura por hora (`Lambda-SnapStart-Cached-GB-S`) mientras exista.
    Sin purga, cada `deploy` acumula una version mas y el costo crece de
    forma ilimitada.

    Si `keep_version` no es None (deploy con SnapStart activo): deja SOLO
    esa version (la que apunta el alias `live`) + cualquier version
    referenciada por OTRO alias, y borra el resto. Si `keep_version` es
    None (desactivacion de SnapStart): borra TODAS las versiones
    publicadas que NINGUN alias referencie. `$LATEST` nunca se toca (no
    es una version publicada y no tiene snapshot).

    Es best-effort: un fallo al borrar una version NO rompe el deploy
    (se loguea un WARN y se continua).
    """
    aliased = aws(
        [
            'lambda',
            'list-aliases',
            '--function-name',
            function_name,
            '--query',
            'Aliases[].FunctionVersion',
        ],
        profile=profile,
        region=region,
        parse_json=True,
        check=False,
    )
    keep = {*(aliased.json or [])}
    if keep_version is not None:
        keep.add(keep_version)
    listed = aws(
        [
            'lambda',
            'list-versions-by-function',
            '--function-name',
            function_name,
            '--query',
            'Versions[].Version',
        ],
        profile=profile,
        region=region,
        parse_json=True,
        check=False,
    )
    versions = [
        v for v in (listed.json or []) if v != '$LATEST' and v not in keep
    ]
    if not versions:
        return
    deleted = 0
    for version in versions:
        result = aws(
            [
                'lambda',
                'delete-function',
                '--function-name',
                function_name,
                '--qualifier',
                version,
            ],
            profile=profile,
            region=region,
            check=False,
        )
        if result.ok:
            deleted += 1
        else:
            print(
                f'  WARN  no se pudo borrar {function_name}:{version} '
                '(snapshot SnapStart)',
            )
    if deleted:
        print(
            f'  OK  purgados {deleted} snapshots SnapStart de {function_name}',
        )


def _disable_snap_start(
    rendered: RenderedLambda,
    *,
    profile: str | None,
    region: str,
) -> None:
    """Desactiva SnapStart en una funcion y libera sus snapshots.

    Solo se invoca cuando `rendered.snap_start=False`. Tres pasos:
    1. `update-function-configuration --snap-start ApplyOn=None` (apaga
       SnapStart; idempotente via `_ensure_snap_start_config`).
    2. Borra el alias `live` (la integracion del trigger ya se re-apunto
       a `$LATEST` en `_wire_http_trigger` porque el qualifier es vacio
       con snap_start=False).
    3. Purga TODAS las versiones publicadas restantes (sus snapshots
       facturables `Lambda-SnapStart-Cached-GB-S`).

    Best-effort en el borrado del alias y las versiones: un fallo NO
    rompe el deploy.
    """
    if rendered.snap_start:
        return
    # 1. Apagar SnapStart (target 'None').
    _ensure_snap_start_config(rendered, profile=profile, region=region)
    # 2. Borrar el alias `live` (ya nadie lo referencia tras el rewire).
    deleted_alias = aws(
        [
            'lambda',
            'delete-alias',
            '--function-name',
            rendered.function_name,
            '--name',
            _SNAP_START_ALIAS,
        ],
        profile=profile,
        region=region,
        check=False,
    )
    if deleted_alias.ok:
        print(f'  OK  alias {_SNAP_START_ALIAS} eliminado')
    # 3. Purgar todas las versiones publicadas (snapshots facturables).
    _prune_old_versions(
        rendered.function_name,
        keep_version=None,
        profile=profile,
        region=region,
    )


def _snap_start_qualifier(rendered: RenderedLambda) -> str:
    """Sufijo de qualifier para integraciones: `:live` o `` (vacio)."""
    return f':{_SNAP_START_ALIAS}' if rendered.snap_start else ''


def _provision_update_code(
    rendered: RenderedLambda,
    zip_path: Path,
    *,
    profile: str | None,
    region: str,
) -> None:
    """Secuencia `Action.UPDATE_CODE`: solo `update-function-code`.

    Si `snap_start=True`: tras el update, publish-version genera un nuevo
    snapshot y el alias `live` se mueve a esa version, exponiendo el
    nuevo codigo al trigger (API GW apunta a `:live`).
    """
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
    if rendered.snap_start:
        _ensure_snap_start_config(rendered, profile=profile, region=region)
        _publish_and_update_alias(rendered, profile=profile, region=region)


def _provision_update_config(
    rendered: RenderedLambda,
    *,
    profile: str | None,
    region: str,
) -> None:
    """Secuencia `Action.UPDATE_CONFIG`: config de funcion + IAM inline.

    Garantiza que el rol canonico (`rendered.role_name`) existe y que el
    Lambda esta amarrado a el via `--role`. Sin `--role`, un Lambda
    creado originalmente por SAM/CFN nunca cambiaria de rol y quedaria
    bloqueado en las permisos del legado (causa raiz del incidente del
    25/05/2026 en prod /track y /contact: las nuevas Lambdas leen los
    nombres de tablas DynamoDB desde SSM en cold start, pero el rol
    legacy SAM no tenia `ssm:GetParameter`).
    """
    account = _resolve_account(profile=profile, region=region)
    policy = _concrete_iam_policy(rendered, account)

    resources: dict[str, str | None] = {}
    _create_iam_role(
        rendered,
        policy,
        account,
        profile=profile,
        region=region,
        resources=resources,
    )
    role_arn = str(resources['role_arn'])

    _wait_function_active(
        rendered.function_name, profile=profile, region=region
    )
    aws(
        [
            'lambda',
            'update-function-configuration',
            '--function-name',
            rendered.function_name,
            '--role',
            role_arn,
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
            # Apaga X-Ray en funciones ya existentes (Mode=Active legacy).
            '--tracing-config',
            'Mode=PassThrough',
        ],
        profile=profile,
        region=region,
    )
    if rendered.snap_start:
        _ensure_snap_start_config(rendered, profile=profile, region=region)
        _publish_and_update_alias(rendered, profile=profile, region=region)


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
            _rewire_trigger_on_update(
                rendered,
                stage,
                profile=profile,
                region=region,
                resources=resources,
            )
            # Tras re-apuntar el trigger a $LATEST, apaga SnapStart y
            # libera los snapshots (orden critico: el rewire debe correr
            # ANTES de borrar el alias `live`).
            _disable_snap_start(rendered, profile=profile, region=region)
        elif action == _Action.UPDATE_BOTH:
            _provision_update_code(
                rendered, zip_path, profile=profile, region=region
            )
            _provision_update_config(rendered, profile=profile, region=region)
            _rewire_trigger_on_update(
                rendered,
                stage,
                profile=profile,
                region=region,
                resources=resources,
            )
            _disable_snap_start(rendered, profile=profile, region=region)
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
        # Wiring del trigger: si cambia type/method/path/snap_start el
        # diff debe materializar el cambio en API GW (URI con qualifier
        # `:live`, statement-id del add-permission). Sin esto, el
        # provisioner se queda en NOOP y el cambio queda registrado solo
        # en el manifest, no en AWS.
        'trigger': asdict(rendered.trigger),
        'snap_start': rendered.snap_start,
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
    """Borra el wiring del trigger HTTP (API method/resource)."""
    resources = state.resources

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
