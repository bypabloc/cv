# Catalogo de colas SQS

Cada archivo `<short-name>.yaml` declara una cola SQS del backend. devtools
las provisiona con `aws sqs create-queue` + `aws sqs set-queue-attributes`
y publica name/arn/url en SSM. Los archivos se procesan en 2-pass: primero
las DLQs (sin `redrive_policy`), despues las principales (que apuntan a
su DLQ por nombre).

## Schema

```yaml
kind: sqs-queue

name: portfolio-<short>-${stage}     # ${stage} interpolado por devtools
message_retention_seconds: 345600    # 4 dias (default) | 1209600 (14 dias, max para DLQ)
visibility_timeout_seconds: 60       # debe ser >= 6x el timeout del worker

# Bloque opcional: cola principal con DLQ
redrive_policy:
  target: portfolio-<short>-dlq-${stage}   # nombre de la DLQ (debe existir)
  max_receive_count: 3

publishes_ssm:
  arn: /portfolio/${stage}/sqs/<short>/arn
  url: /portfolio/${stage}/sqs/<short>/url

tags: { Project: portfolio, ManagedBy: devtools }
```

## Convenciones

- DLQ con sufijo `-dlq` en el nombre.
- DLQ retention 14 dias (max SQS) para inspeccion + reproceso manual.
- Cola principal `visibility_timeout` = 6x el timeout del worker (recomendado AWS).
- `max_receive_count: 3` por defecto.
- NO usar FIFO (`.fifo` suffix) — 5x mas caro y orden no es requisito.
- SSE-SQS managed key (default, $0). El contenido de los mensajes NO es secreto.

## Como agregar una cola

1. Si necesita DLQ, crear PRIMERO `<short>-dlq.yaml` (sin `redrive_policy`).
2. Crear `<short>-queue.yaml` con `redrive_policy.target` apuntando a la DLQ.
3. Provisionar: `python devtools/run.py serverless provision-infra --stage=<env>
   --aws-profile=tfs-dev`.
4. Si el consumer es una Lambda, agregar `uses.queues` en su `manifest.yaml`.

## Inventario actual

| Archivo | Path SSM url | Retention | Visibility | Redrive |
|---------|-------------|-----------|------------|---------|
| `contact-form-dlq.yaml` | `/portfolio/${stage}/sqs/contact-form-dlq/url` | 14d | 30s | — |
| `contact-form-queue.yaml` | `/portfolio/${stage}/sqs/contact-form/url` | 4d | 180s | -> dlq (3x) |
| `tracking-events-dlq.yaml` | `/portfolio/${stage}/sqs/tracking-events-dlq/url` | 14d | 30s | — |
| `tracking-events-queue.yaml` | `/portfolio/${stage}/sqs/tracking-events/url` | 4d | 60s | -> dlq (3x) |
