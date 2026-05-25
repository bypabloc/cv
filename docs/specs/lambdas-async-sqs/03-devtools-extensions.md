# 03 — Extensiones devtools (provisioner)

> Extiende `devtools/serverless/` para soportar: (a) `redrive_policy` +
> `visibility_timeout_seconds` en colas SQS, (b) nuevo `kind:
> cloudwatch-alarm`, (c) nuevo `trigger.type: sqs` en `manifest.yaml` de
> Lambdas, (d) nuevo nivel de acceso `uses.queues` en manifest para IAM.

[< 02](02-resources-sqs-cloudwatch.md) | [Siguiente: 04 — shared/queue >](04-shared-queue-publisher.md)

---

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `devtools/serverless/infra_provision.py` | Ampliar `_provision_sqs_queue`; agregar `_provision_cloudwatch_alarm`; cambiar `_PROVISION_ORDER` y `_RESOURCE_TYPES`; 2-pass para DLQ -> main |
| `devtools/serverless/provisioner.py` | Agregar `'sqs'` a `_VALID_TRIGGERS`; nuevo branch en `_build_trigger`; nueva ruta de IAM para `uses.queues`; nueva accion AWS CLI para Event Source Mapping |
| `devtools/serverless/aws_cli.py` (si aplica) | Ningun cambio esperado; reutiliza wrapper actual |
| `devtools/tests/serverless/test_infra_provision.py` | Tests del nuevo kind + redrive 2-pass |
| `devtools/tests/serverless/test_provisioner.py` | Tests de `trigger.type: sqs` + Event Source Mapping + IAM SQS |
| `devtools/tests/serverless/conftest.py` | Si hace falta, fixtures de SQS mocks (moto-like) |

## 1) `_provision_sqs_queue` con redrive + visibility timeout

### Diff conceptual

```python
def _provision_sqs_queue(rendered, *, profile, region, dry_run):
    spec = rendered.spec
    queue_name = rendered.name

    if dry_run:
        ...
    else:
        queue_url = _resolve_queue_url(queue_name, ...) or _create_sqs_queue(rendered, ...)
        queue_arn = _describe_queue_arn(queue_url, ...)

    # ─── NUEVO: actualizar atributos (visibility_timeout + redrive_policy) ───
    if not dry_run:
        attributes = _build_queue_attributes(
            spec,
            profile=profile,
            region=region,
        )
        if attributes:
            aws_cli.aws(
                ['sqs', 'set-queue-attributes',
                 '--queue-url', queue_url,
                 '--attributes', json.dumps(attributes)],
                profile=profile, region=region,
            )
    # ─── /NUEVO ───

    values = {'arn': queue_arn, 'url': queue_url}
    published = _publish_ssm(rendered, values, ...)
    return {f'sqs:{queue_name}:url': queue_url, f'sqs:{queue_name}:arn': queue_arn}, published


def _build_queue_attributes(spec, *, profile, region):
    """Construye el dict de atributos para set-queue-attributes.

    Soporta:
      - VisibilityTimeout (from spec.visibility_timeout_seconds)
      - RedrivePolicy (from spec.redrive_policy.{target, max_receive_count})
        Resuelve target -> ARN via get-queue-url + get-queue-attributes.
    """
    attrs = {}
    if 'visibility_timeout_seconds' in spec:
        attrs['VisibilityTimeout'] = str(spec['visibility_timeout_seconds'])

    redrive = spec.get('redrive_policy')
    if redrive:
        dlq_name = redrive['target']
        dlq_url = _resolve_queue_url(dlq_name, profile=profile, region=region)
        if dlq_url is None:
            raise InfraError(
                f'DLQ {dlq_name!r} no existe — debe provisionarse antes '
                f'que la cola principal. Revisar _PROVISION_ORDER.'
            )
        dlq_arn = _describe_queue_arn(dlq_url, profile=profile, region=region)
        attrs['RedrivePolicy'] = json.dumps({
            'deadLetterTargetArn': dlq_arn,
            'maxReceiveCount': redrive.get('max_receive_count', 3),
        })
    return attrs
```

### Orden de provisioning (2-pass interno al kind)

```python
# Antes:
_PROVISION_ORDER = ('sqs-queue', 'dynamodb-table', 'rest-api')

# Despues: SQS sigue siendo primero, pero el handler de SQS internamente
# ordena: DLQs (las que NO tienen redrive_policy) PRIMERO, despues las
# principales (las que SI tienen redrive_policy).
```

Implementacion: en `_collect_all_resources()` ordenar los rendered de tipo
`sqs-queue` con un sort key:

```python
def _sqs_provision_priority(rendered):
    """DLQs primero (sin redrive_policy), luego principales (con redrive)."""
    return 1 if 'redrive_policy' in rendered.spec else 2
```

### Idempotencia

- `set-queue-attributes` es idempotente: aplicar 2 veces con los mismos
  valores no falla. AWS hace diff y solo aplica si cambia.
- `RedrivePolicy` se aplica como JSON string; AWS lo compara exacto.

## 2) Nuevo `kind: cloudwatch-alarm`

### Funcion nueva

```python
def _provision_cloudwatch_alarm(rendered, *, profile, region, dry_run):
    """Provisiona una alarma CloudWatch. Idempotente via put-metric-alarm."""
    spec = rendered.spec
    alarm_name = rendered.name

    if dry_run:
        print(_c(YELLOW, f'[dry-run] cloudwatch put-metric-alarm {alarm_name}'))
        return {f'cloudwatch:{alarm_name}': None}, []

    metric = spec['metric']
    args = [
        'cloudwatch', 'put-metric-alarm',
        '--alarm-name', alarm_name,
        '--namespace', metric['namespace'],
        '--metric-name', metric['name'],
        '--statistic', spec.get('statistic', 'Maximum'),
        '--period', str(spec.get('period_seconds', 300)),
        '--evaluation-periods', str(spec.get('evaluation_periods', 1)),
        '--threshold', str(spec['threshold']),
        '--comparison-operator', spec.get('comparison', 'GreaterThanThreshold'),
        '--treat-missing-data', spec.get('treat_missing_data', 'notBreaching'),
    ]
    if spec.get('description'):
        args.extend(['--alarm-description', spec['description']])

    # Dimensions (lista plana Name=K,Value=V para AWS CLI)
    dims = metric.get('dimensions', {})
    if dims:
        args.append('--dimensions')
        args.extend([f'Name={k},Value={v}' for k, v in dims.items()])

    # Actions (SNS ARNs, vacio = solo dashboard)
    actions = spec.get('alarm_actions', [])
    if actions:
        args.append('--alarm-actions')
        args.extend(actions)

    aws_cli.aws(args, profile=profile, region=region)
    print(_c(GREEN, f'  OK alarma {alarm_name} configurada'))

    return {f'cloudwatch:{alarm_name}': alarm_name}, []
```

### Wiring en `infra_provision.py`

```python
_RESOURCE_TYPES = ('sqs', 'dynamodb', 'api_gateway', 'cloudwatch_alarms')
_PROVISION_ORDER = ('sqs-queue', 'dynamodb-table', 'rest-api', 'cloudwatch-alarm')

_PROVISIONERS = {
    'dynamodb-table': _provision_dynamodb_table,
    'rest-api': _provision_rest_api,
    'sqs-queue': _provision_sqs_queue,
    'cloudwatch-alarm': _provision_cloudwatch_alarm,
}
```

### `kind` validacion

Agregar `'cloudwatch-alarm'` al set valido en `_render_resource_spec`:

```python
if kind not in {'dynamodb-table', 'rest-api', 'sqs-queue', 'cloudwatch-alarm'}:
    raise InfraError(...)
```

## 3) `trigger.type: sqs` en `provisioner.py`

### Cambios en `_VALID_TRIGGERS`

```python
# Antes:
_VALID_TRIGGERS = ('direct', 'http')

# Despues:
_VALID_TRIGGERS = ('direct', 'http', 'sqs')
```

### Nuevo branch en `_build_trigger`

```python
def _build_trigger(manifest):
    trigger = manifest.get('trigger') or {}
    ttype = trigger.get('type')

    if ttype not in _VALID_TRIGGERS:
        raise ManifestError(...)

    if ttype == 'http':
        ...
    elif ttype == 'sqs':
        queue_name = trigger.get('queue')
        batch_size = trigger.get('batch_size', 1)
        response_types = trigger.get('function_response_types', [])
        if not queue_name:
            raise ManifestError("trigger sqs requiere 'queue'.")
        return TriggerSpec(
            type='sqs',
            queue_name=queue_name,           # se interpola con stage en provision
            batch_size=batch_size,
            function_response_types=response_types,
        )

    return TriggerSpec(type=ttype)
```

### Provisioning del Event Source Mapping

Nueva funcion en `provisioner.py` (o un helper):

```python
def _wire_sqs_trigger(function_name, trigger, *, stage, profile, region):
    """Crea o actualiza el Event Source Mapping SQS -> Lambda.

    Idempotente: list-event-source-mappings para ver si ya existe.
    """
    queue_name = _interp(trigger.queue_name, stage)
    queue_url = _resolve_queue_url(queue_name, profile=profile, region=region)
    if queue_url is None:
        raise ProvisionerError(f'Cola {queue_name!r} no existe — provision-infra primero.')
    queue_arn = _describe_queue_arn(queue_url, profile=profile, region=region)

    # Buscar ESM existente para este Lambda + esta cola
    result = aws_cli.aws(
        ['lambda', 'list-event-source-mappings',
         '--function-name', function_name,
         '--event-source-arn', queue_arn],
        profile=profile, region=region, parse_json=True,
    )
    existing = (result.json or {}).get('EventSourceMappings', [])

    if existing:
        uuid = existing[0]['UUID']
        # Update batch_size si cambio
        aws_cli.aws(
            ['lambda', 'update-event-source-mapping',
             '--uuid', uuid,
             '--batch-size', str(trigger.batch_size),
             '--function-response-types', *trigger.function_response_types],
            profile=profile, region=region,
        )
    else:
        args = [
            'lambda', 'create-event-source-mapping',
            '--function-name', function_name,
            '--event-source-arn', queue_arn,
            '--batch-size', str(trigger.batch_size),
            '--enabled',
        ]
        if trigger.function_response_types:
            args.extend(['--function-response-types', *trigger.function_response_types])
        aws_cli.aws(args, profile=profile, region=region)
```

Llamarlo desde el deploy de la Lambda despues de `create-function` /
`update-function-configuration`:

```python
if rendered.trigger.type == 'sqs':
    _wire_sqs_trigger(
        function_name=rendered.config_name,
        trigger=rendered.trigger,
        stage=stage, profile=profile, region=region,
    )
```

## 4) `uses.queues` para IAM

### Schema esperado

```yaml
uses:
  queues:
    - { name: portfolio-contact-form-${stage}, access: consumer }
    - { name: portfolio-tracking-events-${stage}, access: producer }
```

### Mapeo access -> acciones IAM

```python
_SQS_ACTIONS = {
    'producer': ['sqs:SendMessage'],
    'consumer': [
        'sqs:ReceiveMessage',
        'sqs:DeleteMessage',
        'sqs:GetQueueAttributes',
    ],
}
```

### Statement IAM generado

```python
def _sqs_statements(uses, *, stage, account_id, region):
    """Traduce uses.queues a Statements IAM scoped al ARN exacto."""
    statements = []
    for entry in uses.get('queues') or []:
        queue_name = _interp(entry['name'], stage)
        access = entry.get('access', 'producer')
        actions = _SQS_ACTIONS[access]
        arn = f'arn:aws:sqs:{region}:{account_id}:{queue_name}'
        statements.append({
            'Effect': 'Allow',
            'Action': actions,
            'Resource': arn,
        })
    return statements
```

Agregarlo a `_build_statements` (que ya construye los demas).

## 5) Env vars inyectadas al encoder (SQS URL)

Cuando un Lambda tiene `uses.queues` con `access: producer`, devtools inyecta:

```python
SSM_<UPPER_QUEUE_NAME>_URL_PATH = /portfolio/${stage}/sqs/<short>/url
```

Ejemplo:
- queue `portfolio-contact-form-${stage}` -> env var
  `SSM_CONTACT_FORM_QUEUE_URL_PATH` con valor
  `/portfolio/dev/sqs/contact-form/url`.

El encoder lee ese path con `shared.aws.ssm.get_secret(path)` en cold start.

## 6) Documentar `_PUBLISHES_SSM_KEY_MAP`

El helper `_publish_ssm` (en `infra_provision.py`) ya existe y publica los
valores `arn` y `url` del rendered. Confirmar que respeta los paths
declarados en `publishes_ssm` del YAML (no hace falta cambio si ya lo hace).

## Tests nuevos

### `test_infra_provision.py`

```python
def test_sqs_queue_with_redrive_provisions_dlq_first():
    """
    Given catalog con DLQ + cola principal con redrive_policy,
    When provision_all corre,
    Then DLQ se crea ANTES y la principal recibe RedrivePolicy con su ARN.
    """
    # Arrange: mock aws_cli con dos colas declaradas
    # Act: provision_all(...)
    # Assert: orden de llamadas + set-queue-attributes con RedrivePolicy

def test_cloudwatch_alarm_idempotent():
    """
    Given una alarma declarada en cloudwatch_alarms/X.yaml,
    When provision_all corre 2 veces,
    Then la 2da corrida hace put-metric-alarm con los mismos args (idempotente).
    """
```

### `test_provisioner.py`

```python
def test_trigger_sqs_creates_event_source_mapping():
    """
    Given manifest con trigger.type: sqs + queue + batch_size,
    When _wire_sqs_trigger corre,
    Then create-event-source-mapping se invoca con --function-response-types.
    """

def test_uses_queues_consumer_generates_iam_statement():
    """
    Given uses.queues con access=consumer sobre una cola,
    When _build_statements corre,
    Then el statement tiene actions=[ReceiveMessage, DeleteMessage, GetQueueAttributes]
        scoped al ARN de la cola.
    """

def test_uses_queues_producer_inyecta_env_var_ssm_url_path():
    """
    Given uses.queues con access=producer sobre 'portfolio-contact-form-${stage}',
    When _build_env_vars corre con stage='dev',
    Then env tiene SSM_CONTACT_FORM_QUEUE_URL_PATH=/portfolio/dev/sqs/contact-form/url.
    """
```

## Reglas duras

- **SIEMPRE** el provisioner es idempotente. Las nuevas funciones tambien.
- **SIEMPRE** `_PROVISION_ORDER` se respeta: SQS antes que Lambda (que
  necesita el ARN de la cola para el ESM); Alarmas al final (necesitan
  los ARN de SQS).
- **SIEMPRE** el ARN de la DLQ se resuelve via `get-queue-attributes` —
  NUNCA se hardcodea ni se construye con account_id local (drift risk).
- **NUNCA** `serverless:*` IAM (least privilege siempre).
- **NUNCA** `set-queue-attributes` con un dict vacio (AWS CLI falla).

## Verificacion incremental

```bash
# Tests nuevos verdes
cd devtools && python -m pytest tests/serverless/test_infra_provision.py \
  tests/serverless/test_provisioner.py -v

# Linting
ruff check devtools/serverless/
ruff format --check devtools/serverless/

# Dry-run (sin AWS) — debe imprimir el plan sin errores
python devtools/run.py serverless provision-infra --stage=dev --dry-run \
  --aws-profile=tfs-dev
```

## AC cubiertos

- AC-15 (Event Source Mapping con `function_response_types`)
- AC-16 (RedrivePolicy aplicado correctamente)
- AC-17 (alarma CloudWatch provisionada — el verde real es en fase 11
  cuando se deploy en dev)

## Anti-patrones

| Anti-patron | Por que | Correccion |
|-------------|---------|------------|
| Hardcodear ARN de DLQ en YAML de la cola main | Drift entre catalog y AWS | Resolver via `get-queue-attributes` en runtime del provisioner |
| `create-event-source-mapping` sin `list` previo | Crea duplicados al re-deployar | List + update si existe |
| Pasar `--function-response-types` solo en `create`, no en `update` | Si cambia se ignora | Pasar siempre en ambos |
| IAM `sqs:*` | Excede least privilege | Acciones explicitas por access |
| `cloudwatch put-metric-alarm` sin `--treat-missing-data` | Default `missing` rompe la alarma | `notBreaching` para metricas SQS |

---

[< 02](02-resources-sqs-cloudwatch.md) | [Siguiente: 04 — shared/queue >](04-shared-queue-publisher.md)
