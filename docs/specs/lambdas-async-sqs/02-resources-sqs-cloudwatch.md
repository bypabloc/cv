# 02 — Recursos SQS + CloudWatch (YAMLs)

> Agrega las 4 colas SQS (2 main + 2 DLQ) y las 2 alarmas CloudWatch en
> `serverless/lambda/resources/`. Solo declarativo (YAMLs + READMEs). No
> toca codigo ni provisioner — eso es fase 03.

[< 01](01-contexto-y-decision.md) | [Siguiente: 03 — Devtools extensions >](03-devtools-extensions.md)

---

## Que se agrega

### Estructura nueva en `resources/`

```text
serverless/lambda/resources/
├── sqs/                          ← NUEVO
│   ├── README.md
│   ├── contact-form-dlq.yaml
│   ├── contact-form-queue.yaml
│   ├── tracking-events-dlq.yaml
│   └── tracking-events-queue.yaml
└── cloudwatch_alarms/            ← NUEVO
    ├── README.md
    ├── contact-form-dlq-alarm.yaml
    └── tracking-events-dlq-alarm.yaml
```

### `sqs/README.md`

Schema doc al estilo de `secrets/README.md`. Documenta:
- `kind: sqs-queue`
- Campos: `name`, `message_retention_seconds`, `visibility_timeout_seconds`,
  `redrive_policy.{target, max_receive_count}`, `publishes_ssm.{arn, url}`,
  `tags`.
- Convencion: DLQ con sufijo `-dlq`, retention 14 dias (max SQS).
- Convencion: cola principal con `visibility_timeout` = 6x el timeout del
  worker (recomendado AWS).

### `sqs/contact-form-dlq.yaml`

```yaml
# Esquema devtools — NO CloudFormation: esquema plano, sin funciones
# intrinsecas. DLQ del worker contact_worker. SQS retiene los mensajes
# 14 dias para inspeccion + reproceso manual.
kind: sqs-queue
name: portfolio-contact-form-dlq-${stage}
message_retention_seconds: 1209600       # 14 dias (max SQS)
visibility_timeout_seconds: 30
publishes_ssm:
  arn: /portfolio/${stage}/sqs/contact-form-dlq/arn
  url: /portfolio/${stage}/sqs/contact-form-dlq/url
tags: { Project: portfolio, ManagedBy: devtools }
```

### `sqs/contact-form-queue.yaml`

```yaml
# Cola principal del worker contact_worker. visibility_timeout = 180s
# (6x el timeout del worker que es 30s) — recomendado AWS para evitar
# duplicate processing por timeout antes de ack.
kind: sqs-queue
name: portfolio-contact-form-${stage}
message_retention_seconds: 345600        # 4 dias (default SQS)
visibility_timeout_seconds: 180
redrive_policy:
  target: portfolio-contact-form-dlq-${stage}
  max_receive_count: 3
publishes_ssm:
  arn: /portfolio/${stage}/sqs/contact-form/arn
  url: /portfolio/${stage}/sqs/contact-form/url
tags: { Project: portfolio, ManagedBy: devtools }
```

### `sqs/tracking-events-dlq.yaml`

```yaml
kind: sqs-queue
name: portfolio-tracking-events-dlq-${stage}
message_retention_seconds: 1209600       # 14 dias
visibility_timeout_seconds: 30
publishes_ssm:
  arn: /portfolio/${stage}/sqs/tracking-events-dlq/arn
  url: /portfolio/${stage}/sqs/tracking-events-dlq/url
tags: { Project: portfolio, ManagedBy: devtools }
```

### `sqs/tracking-events-queue.yaml`

```yaml
# Cola del worker tracking_worker. batch_size=10 en el ESM (declarado en
# el manifest del worker, no aqui). visibility_timeout = 60s para batch
# de 10 events (un batch entero debe procesar <60s).
kind: sqs-queue
name: portfolio-tracking-events-${stage}
message_retention_seconds: 345600        # 4 dias
visibility_timeout_seconds: 60
redrive_policy:
  target: portfolio-tracking-events-dlq-${stage}
  max_receive_count: 3
publishes_ssm:
  arn: /portfolio/${stage}/sqs/tracking-events/arn
  url: /portfolio/${stage}/sqs/tracking-events/url
tags: { Project: portfolio, ManagedBy: devtools }
```

### `cloudwatch_alarms/README.md`

Schema doc para `kind: cloudwatch-alarm`. Documenta:
- Campos: `metric.{namespace, name, dimensions}`, `threshold`, `comparison`,
  `evaluation_periods`, `period_seconds`, `statistic`, `alarm_actions`.
- Convencion: una alarma por DLQ; `alarm_actions: []` por defecto (solo
  dashboard) — futuro: SNS topic para email.

### `cloudwatch_alarms/contact-form-dlq-alarm.yaml`

```yaml
# Alarma: dispara si la DLQ del contact_worker tiene >=1 mensaje visible
# por mas de 5 min. Indica que el worker no pudo procesar 3 retries
# seguidos -> requiere intervencion manual.
kind: cloudwatch-alarm
name: portfolio-contact-form-dlq-not-empty-${stage}
description: >
  Hay mensajes en la DLQ del contact_worker. Revisar
  CloudWatch Logs del worker y la consola SQS de la DLQ.
metric:
  namespace: AWS/SQS
  name: ApproximateNumberOfMessagesVisible
  dimensions:
    QueueName: portfolio-contact-form-dlq-${stage}
threshold: 0
comparison: GreaterThanThreshold
evaluation_periods: 1
period_seconds: 300
statistic: Maximum
alarm_actions: []
tags: { Project: portfolio, ManagedBy: devtools }
```

### `cloudwatch_alarms/tracking-events-dlq-alarm.yaml`

```yaml
kind: cloudwatch-alarm
name: portfolio-tracking-events-dlq-not-empty-${stage}
description: >
  Hay mensajes en la DLQ del tracking_worker. Revisar
  CloudWatch Logs del worker y la consola SQS de la DLQ.
metric:
  namespace: AWS/SQS
  name: ApproximateNumberOfMessagesVisible
  dimensions:
    QueueName: portfolio-tracking-events-dlq-${stage}
threshold: 0
comparison: GreaterThanThreshold
evaluation_periods: 1
period_seconds: 300
statistic: Maximum
alarm_actions: []
tags: { Project: portfolio, ManagedBy: devtools }
```

## Reglas duras

- **SIEMPRE** la DLQ se declara como un YAML separado (no inline en la
  cola principal). Asi puede tener su propia retention y se reutilizan los
  primitives del provisioner.
- **SIEMPRE** el orden de provisioning es: DLQs PRIMERO, despues colas
  principales. La cola principal necesita el ARN de la DLQ para el
  `RedrivePolicy`. Eso lo resuelve la fase 03 en el provisioner (2-pass).
- **SIEMPRE** `${stage}` se interpola con `local`/`dev`/`stage`/`prod`. En
  local NO se provisionan colas — el modo `direct` no usa SQS.
- **SIEMPRE** los nombres de colas son < 80 chars (limite SQS). Con
  `portfolio-tracking-events-dlq-prod` (35 chars) estamos OK.
- **NUNCA** FIFO (`.fifo` suffix) — no aplica al caso y suma 5x coste.
- **NUNCA** encryption con CMK propia — usar SSE-SQS managed key (default,
  $0). El contenido de los mensajes no es sensible (no son secretos).

## Verificacion incremental (antes de commitear)

```bash
# 1) YAMLs parseables (yaml puro, sin necesidad del catalogo todavia)
python -c "
import yaml, pathlib
for p in pathlib.Path('serverless/lambda/resources/sqs').glob('*.yaml'):
    yaml.safe_load(p.read_text())
    print(f'OK {p.name}')
for p in pathlib.Path('serverless/lambda/resources/cloudwatch_alarms').glob('*.yaml'):
    yaml.safe_load(p.read_text())
    print(f'OK {p.name}')
"

# 2) Convencion de nombres
python -c "
import yaml, pathlib
for p in pathlib.Path('serverless/lambda/resources/sqs').glob('*.yaml'):
    d = yaml.safe_load(p.read_text())
    assert d['kind'] == 'sqs-queue', p
    assert d['name'].startswith('portfolio-'), p
    assert '\${stage}' in d['name'], p
    print(f'OK schema {p.name}')
"
```

## AC cubiertos

- AC-16 (cola principal con redrive_policy hacia DLQ) — declarado aqui;
  provisioning en fase 03; verificacion E2E en fase 11.
- AC-17 (alarma CloudWatch) — declarado aqui; provisioning en fase 03.

## Anti-patrones

| Anti-patron | Por que | Correccion |
|-------------|---------|------------|
| DLQ inline en el YAML de la cola | Mezcla 2 recursos en 1 archivo | Un YAML por cola |
| `visibility_timeout` = timeout del worker | SQS re-entrega antes de que el worker complete bajo carga | `visibility_timeout >= 6x timeout` (AWS recomendacion) |
| `max_receive_count > 5` | Logs flood + costo SQS extra antes de DLQ | 3 es buena referencia |
| Alarma `threshold > 0` (ej. >=10) | Pierde el primer fallo critico | `> 0` para alertar desde el 1er mensaje |
| FIFO queue | 5x coste y orden no es requisito | Standard |

---

[< 01](01-contexto-y-decision.md) | [Siguiente: 03 — Devtools extensions >](03-devtools-extensions.md)
