"""Generacion del SAM template desde el `lambda.yaml` formato dev.

El manifiesto `lambda.yaml` describe el Lambda en terminos de
DESARROLLADOR (que recursos usa, como se invoca), sin ARNs ni politicas
IAM. Este modulo TRADUCE ese manifiesto al `template.yaml` SAM, que es
**efimero** (esta en .gitignore) y se regenera antes de cada build /
deploy / local.

Cada Lambda del portfolio es su propio stack CloudFormation. Los
recursos compartidos (API Gateway, tablas DynamoDB, DLQ) viven en el
stack `portfolio-infra-<stage>` y se importan via `Fn::ImportValue`.

Traduccion del manifiesto:
  - `trigger.type: direct`           -> sin Events.
  - `trigger.type: http`             -> Event Api sobre la API importada.
  - `trigger.type: on-table-changes` -> Event DynamoDB por cada tabla +
                                        DLQ.
  - `uses.tables`                    -> permisos DynamoDB + env vars con
                                        el nombre de tabla importado.
  - `uses.secrets`                   -> permisos SSM GetParameter + KMS
                                        Decrypt + env vars con el path.
  - `uses.sends-email`               -> permisos SES SendEmail.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from serverless.resolve import ManifestError
from serverless.resolve import ResolvedLambda


# Stages validos del manifiesto (la clave 'default' aplica a todos).
_VALID_ENV_STAGES = ('default', 'dev', 'stage', 'prod')

# Nombre del stack de infra compartida (se interpola el stage).
_INFRA_STACK = 'portfolio-infra-${stage}'

# Tipos de trigger soportados.
_VALID_TRIGGERS = ('direct', 'http', 'on-table-changes')

# --- Catalogo de recursos del backend (nombre corto -> definicion) -----
#
# El manifiesto usa nombres cortos legibles (`contacts`, `neon-url`).
# Aqui se resuelven al recurso real: el nombre de tabla fisico, el Output
# del stack de infra y el env var con que el codigo del Lambda lo lee.

# Tablas DynamoDB: nombre corto -> (nombre fisico, env var del codigo).
# El nombre fisico lleva el sufijo de stage; el codigo lo lee por env var.
_TABLES: dict[str, dict[str, str]] = {
    'contacts': {
        'physical': 'portfolio-contacts-${stage}',
        'env': 'CONTACTS_TABLE_NAME',
        'stream_export': 'ContactsStreamArn',
    },
    'tracking': {
        'physical': 'portfolio-tracking-${stage}',
        'env': 'TRACKING_TABLE_NAME',
        'stream_export': 'TrackingStreamArn',
    },
    'cache': {
        'physical': 'portfolio-cache-${stage}',
        'env': 'CACHE_TABLE_NAME',
        'stream_export': '',
    },
    'rate-limit-rules': {
        'physical': 'portfolio-rate-limit-rules-${stage}',
        'env': 'RATE_LIMIT_RULES_TABLE_NAME',
        'stream_export': '',
    },
    'rate-limit-buckets': {
        'physical': 'portfolio-rate-limit-buckets-${stage}',
        'env': 'RATE_LIMIT_BUCKETS_TABLE_NAME',
        'stream_export': '',
    },
}

# Secretos SSM: nombre corto -> (path SSM, env var del codigo).
# Algunos paths llevan el stage, otros son globales (sin stage).
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
# Configuration set por defecto de la domain identity (SES v2 lo exige).
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


def _logical_id(name: str) -> str:
    """Convierte el name del manifiesto a un LogicalId SAM PascalCase.

    Ejemplo: 'contact-form' -> 'ContactFormFunction'.
    """
    parts = name.replace('_', '-').split('-')
    return ''.join(p.capitalize() for p in parts if p) + 'Function'


def _interp(value: str, stage: str) -> str:
    """Interpola `${stage}` en un string del manifiesto."""
    return value.replace('${stage}', stage)


def _import_value(export_suffix: str, stage: str) -> dict[str, Any]:
    """Construye un `Fn::ImportValue` de un Output del stack de infra.

    El nombre del export es `portfolio-infra-<stage>-<suffix>`.
    """
    infra = _interp(_INFRA_STACK, stage)
    return {'Fn::ImportValue': f'{infra}-{export_suffix}'}


def _resolve_env(manifest: dict[str, Any], stage: str) -> dict[str, Any]:
    """Combina `env.default` + `env.<stage>` del manifiesto.

    Las claves del stage especifico sobrescriben las de default. Los
    valores se dejan tal cual (strings); las env vars derivadas de `uses`
    se agregan aparte en `build_template`.
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


def _build_env_vars(manifest: dict[str, Any], stage: str) -> dict[str, Any]:
    """Construye el bloque de env vars de la funcion.

    Combina: las env vars explicitas (`env`), Powertools, y las derivadas
    de `uses` (nombre de cada tabla + path de cada secreto).
    """
    name = manifest['name']
    env: dict[str, Any] = {
        'POWERTOOLS_SERVICE_NAME': name,
        'POWERTOOLS_METRICS_NAMESPACE': 'Portfolio',
        'POWERTOOLS_LOG_LEVEL': 'INFO',
        'ENVIRONMENT': stage,
        'STAGE': stage,
    }
    env.update(_resolve_env(manifest, stage))

    uses = manifest.get('uses') or {}

    # Cada tabla declarada -> env var con el nombre fisico de la tabla.
    tables = uses.get('tables') or {}
    if isinstance(tables, dict):
        for short_name in tables:
            tdef = _table_def(short_name)
            env[tdef['env']] = _interp(tdef['physical'], stage)

    # Cada secreto declarado -> env var con el path SSM.
    for short_name in uses.get('secrets') or []:
        sdef = _secret_def(short_name)
        env[sdef['env']] = _interp(sdef['path'], stage)

    return env


def _build_policies(
    manifest: dict[str, Any], stage: str
) -> list[dict[str, Any]]:
    """Traduce `uses` a una lista de Statements IAM (Policies SAM).

    Reglas de traduccion:
      - cada tabla -> Statement DynamoDB con las acciones del nivel de
        acceso (read / write / read-write).
      - cada secreto -> Statement SSM GetParameter; si hay >= 1 secreto,
        un Statement KMS Decrypt (los SecureString se descifran con la
        KMS key del proyecto).
      - sends-email -> Statement SES SendEmail sobre las identidades.
      - on-table-changes -> Statement de lectura de los Streams + SQS
        SendMessage al DLQ.
    """
    region = '${AWS::Region}'
    account = '${AWS::AccountId}'
    statements: list[dict[str, Any]] = []
    uses = manifest.get('uses') or {}

    # --- DynamoDB: una Statement por tabla ---
    tables = uses.get('tables') or {}
    if isinstance(tables, dict):
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
                        {
                            'Fn::Sub': (
                                f'arn:aws:dynamodb:{region}:{account}:'
                                f'table/{physical}'
                            ),
                        },
                    ],
                }
            )

    # --- SSM + KMS: una Statement SSM por grupo de secretos, una KMS ---
    secrets = uses.get('secrets') or []
    if secrets:
        secret_arns = []
        for short_name in secrets:
            sdef = _secret_def(short_name)
            path = _interp(sdef['path'], stage)
            secret_arns.append(
                {
                    'Fn::Sub': (
                        f'arn:aws:ssm:{region}:{account}:parameter{path}'
                    ),
                }
            )
        statements.append(
            {
                'Effect': 'Allow',
                'Action': ['ssm:GetParameter'],
                'Resource': secret_arns,
            }
        )
        statements.append(
            {
                'Effect': 'Allow',
                'Action': ['kms:Decrypt'],
                'Resource': {
                    'Fn::Sub': f'arn:aws:kms:{region}:{account}:key/*',
                },
                'Condition': {
                    'StringEquals': {
                        'kms:ViaService': {
                            'Fn::Sub': f'ssm.{region}.amazonaws.com',
                        },
                    },
                },
            }
        )

    # --- SES: envio de email transaccional ---
    if uses.get('sends-email'):
        ses_resources = [
            {
                'Fn::Sub': (f'arn:aws:ses:{region}:{account}:identity/{ident}'),
            }
            for ident in _SES_IDENTITIES
        ]
        ses_resources.append(
            {
                'Fn::Sub': (
                    f'arn:aws:ses:{region}:{account}:'
                    f'configuration-set/{_SES_CONFIG_SET}'
                ),
            }
        )
        statements.append(
            {
                'Effect': 'Allow',
                'Action': ['ses:SendEmail', 'ses:SendRawEmail'],
                'Resource': ses_resources,
            }
        )

    # --- on-table-changes: leer los Streams + escribir al DLQ ---
    trigger = manifest.get('trigger') or {}
    if trigger.get('type') == 'on-table-changes':
        stream_arns = []
        for short_name in trigger.get('tables') or []:
            tdef = _table_def(short_name)
            if not tdef['stream_export']:
                raise ManifestError(
                    f'la tabla {short_name!r} no tiene Stream — no puede '
                    f'usarse en on-table-changes.',
                )
            stream_arns.append(_import_value(tdef['stream_export'], stage))
        statements.append(
            {
                'Effect': 'Allow',
                'Action': [
                    'dynamodb:DescribeStream',
                    'dynamodb:GetRecords',
                    'dynamodb:GetShardIterator',
                    'dynamodb:ListStreams',
                ],
                'Resource': stream_arns,
            }
        )
        statements.append(
            {
                'Effect': 'Allow',
                'Action': ['sqs:SendMessage'],
                'Resource': [_import_value('StreamProcessorDLQArn', stage)],
            }
        )

    return statements


def _build_events(manifest: dict[str, Any], stage: str) -> dict[str, Any]:
    """Construye el bloque `Events` de la funcion para triggers de eventos.

    Solo cubre `on-table-changes` (DynamoDB Stream). El trigger `http` NO
    usa Events: SAM no acepta `Fn::ImportValue` en `RestApiId` del Event
    Api, asi que las rutas HTTP se modelan con recursos nativos de API
    Gateway (ver `_build_apigw_resources`).

    - direct           -> sin eventos.
    - http             -> sin eventos (ver _build_apigw_resources).
    - on-table-changes -> un Event DynamoDB por tabla.
    """
    trigger = manifest.get('trigger') or {}
    ttype = trigger.get('type')

    if ttype not in _VALID_TRIGGERS:
        raise ManifestError(
            f'trigger.type invalido: {ttype!r}. '
            f'Validos: {", ".join(_VALID_TRIGGERS)}',
        )

    if ttype in ('direct', 'http'):
        return {}

    # on-table-changes: un Event DynamoDB por tabla.
    events: dict[str, Any] = {}
    for short_name in trigger.get('tables') or []:
        tdef = _table_def(short_name)
        if not tdef['stream_export']:
            raise ManifestError(
                f'la tabla {short_name!r} no tiene Stream.',
            )
        event_name = (
            ''.join(p.capitalize() for p in short_name.split('-')) + 'Stream'
        )
        events[event_name] = {
            'Type': 'DynamoDB',
            'Properties': {
                'Stream': _import_value(tdef['stream_export'], stage),
                'StartingPosition': 'LATEST',
                'BatchSize': 100,
                'MaximumBatchingWindowInSeconds': 10,
                'FunctionResponseTypes': ['ReportBatchItemFailures'],
            },
        }
    return events


def _build_apigw_resources(
    manifest: dict[str, Any],
    stage: str,
    function_logical_id: str,
) -> dict[str, Any]:
    """Construye los recursos de API Gateway para un trigger `http`.

    SAM no acepta `Fn::ImportValue` en el `RestApiId` de un Event Api.
    Por eso una ruta HTTP sobre la API importada del stack de infra se
    modela con recursos NATIVOS de CloudFormation (que si aceptan
    `Fn::ImportValue`):

      - `AWS::ApiGateway::Resource` : el path (ej. /contact).
      - `AWS::ApiGateway::Method`   : el metodo (POST) con integracion
                                      AWS_PROXY hacia el Lambda.
      - `AWS::ApiGateway::Deployment`: redeploya el stage de la API para
                                      que la ruta nueva quede activa.
      - `AWS::Lambda::Permission`   : autoriza a API Gateway a invocar el
                                      Lambda.

    Devuelve un dict de recursos para fusionar en `Resources`.
    """
    trigger = manifest.get('trigger') or {}
    if trigger.get('type') != 'http':
        return {}

    method = trigger.get('method')
    path = trigger.get('path')
    if not method or not path:
        raise ManifestError("trigger http requiere 'method' y 'path'.")

    region = '${AWS::Region}'
    account = '${AWS::AccountId}'
    api_id = _import_value('ApiId', stage)
    root_id = _import_value('ApiRootResourceId', stage)
    path_part = path.lstrip('/')
    func_arn = {'Fn::GetAtt': [function_logical_id, 'Arn']}

    # Integracion AWS_PROXY: API Gateway delega todo al Lambda.
    integration_uri = {
        'Fn::Sub': (
            f'arn:aws:apigateway:{region}:lambda:path/2015-03-31/'
            f'functions/${{{function_logical_id}.Arn}}/invocations'
        ),
    }

    resource_id = 'ApiResource'
    method_id = 'ApiMethod'
    deployment_id = 'ApiDeployment'
    permission_id = 'ApiInvokePermission'

    return {
        resource_id: {
            'Type': 'AWS::ApiGateway::Resource',
            'Properties': {
                'RestApiId': api_id,
                'ParentId': root_id,
                'PathPart': path_part,
            },
        },
        method_id: {
            'Type': 'AWS::ApiGateway::Method',
            'Properties': {
                'RestApiId': api_id,
                'ResourceId': {'Ref': resource_id},
                'HttpMethod': method,
                'AuthorizationType': 'NONE',
                'Integration': {
                    'Type': 'AWS_PROXY',
                    'IntegrationHttpMethod': 'POST',
                    'Uri': integration_uri,
                },
            },
        },
        deployment_id: {
            'Type': 'AWS::ApiGateway::Deployment',
            'DependsOn': [method_id],
            'Properties': {
                'RestApiId': api_id,
                'StageName': stage,
            },
        },
        permission_id: {
            'Type': 'AWS::Lambda::Permission',
            'Properties': {
                'FunctionName': func_arn,
                'Action': 'lambda:InvokeFunction',
                'Principal': 'apigateway.amazonaws.com',
                # Fn::Sub con mapa de variables: ApiId se resuelve via
                # Fn::ImportValue (no se puede inline en el string).
                'SourceArn': {
                    'Fn::Sub': [
                        (
                            f'arn:aws:execute-api:{region}:{account}:'
                            f'${{ApiId}}/{stage}/{method}{path}'
                        ),
                        {'ApiId': api_id},
                    ],
                },
            },
        },
    }


def build_template(
    manifest: dict[str, Any],
    *,
    stage: str = 'dev',
) -> dict[str, Any]:
    """Construye el dict del SAM template desde el manifiesto formato dev.

    Parameters
    ----------
    manifest : dict[str, Any]
        Manifiesto `lambda.yaml` ya validado y con defaults aplicados.
    stage : str
        Stage objetivo (dev | stage | prod).

    Returns
    -------
    dict[str, Any]
        Estructura del SAM template lista para volcar a YAML.
    """
    name = manifest['name']
    logical_id = _logical_id(name)

    function_props: dict[str, Any] = {
        'FunctionName': f'portfolio-{name}-{stage}',
        'CodeUri': '.',
        'Handler': manifest['handler'],
        'Runtime': manifest['runtime'],
        'Architectures': [manifest.get('architecture', 'arm64')],
        'MemorySize': int(manifest.get('memory', 256)),
        'Timeout': int(manifest.get('timeout', 30)),
        'Tracing': 'Active',
        'Environment': {'Variables': _build_env_vars(manifest, stage)},
    }

    policies = _build_policies(manifest, stage)
    if policies:
        function_props['Policies'] = [
            {'Statement': policies},
        ]

    events = _build_events(manifest, stage)
    if events:
        function_props['Events'] = events

    function_props['Tags'] = {
        'Project': 'portfolio',
        'ManagedBy': 'devtools-sam-generate',
        'Stage': stage,
    }

    resources: dict[str, Any] = {
        logical_id: {
            'Type': 'AWS::Serverless::Function',
            'Metadata': {
                'BuildMethod': manifest['runtime'],
            },
            'Properties': function_props,
        },
    }

    # Trigger http: recursos nativos de API Gateway (Resource + Method +
    # Deployment + Permission) sobre la API importada del stack de infra.
    resources.update(_build_apigw_resources(manifest, stage, logical_id))

    template: dict[str, Any] = {
        'AWSTemplateFormatVersion': '2010-09-09',
        'Transform': 'AWS::Serverless-2016-10-31',
        'Description': (
            f'Lambda {name} (stage {stage}) — generado por devtools '
            f'desde lambda.yaml. NO editar a mano.'
        ),
        'Resources': resources,
        'Outputs': {
            f'{logical_id}Arn': {
                'Description': f'ARN de la funcion {name}',
                'Value': {'Fn::GetAtt': [logical_id, 'Arn']},
                'Export': {
                    'Name': f'portfolio-{name}-{stage}-FunctionArn',
                },
            },
        },
    }
    return template


def generate_sam_file(
    resolved: ResolvedLambda,
    *,
    stage: str = 'dev',
) -> Path:
    """Genera `<root>/template.yaml` desde el manifiesto del lambda.

    Parameters
    ----------
    resolved : ResolvedLambda
        Lambda objetivo (modo lambda-controller).
    stage : str
        Stage objetivo del template.

    Returns
    -------
    Path
        Ruta del template.yaml generado.

    Raises
    ------
    ManifestError
        Si el lambda no es lambda-controller (modo legacy no genera SAM).
    """
    if not resolved.is_lambda_controller:
        raise ManifestError(
            'sam-generate solo aplica a lambdas con lambda.yaml. '
            'El backend SAM del portfolio ya tiene su template.yaml.',
        )

    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - PyYAML esta en devtools
        raise ManifestError('PyYAML no esta instalado') from exc

    template = build_template(resolved.manifest, stage=stage)
    out_path = resolved.root / 'template.yaml'

    header = (
        '# ARCHIVO GENERADO por devtools desde lambda.yaml. NO EDITAR.\n'
        '# Regenerar: python devtools/run.py serverless sam-generate '
        f'--path=<dir> --stage={stage}\n'
    )
    body = yaml.safe_dump(template, sort_keys=False, allow_unicode=True)
    out_path.write_text(header + body, encoding='utf-8')
    return out_path
