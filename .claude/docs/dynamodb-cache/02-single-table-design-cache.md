# 02. Schema de tabla `cache` (single-table design)

> Diseno de la tabla DynamoDB `cache` para almacenar key-value pairs con TTL,
> locks distribuidos, invalidation por tag, y stale-while-revalidate metadata.

**Verificado**: 2026-05-14 — Schema alineado con DynamoDB 2026 features (TTL nativo, sparse attributes).

## Tabla: `cache` (On-Demand)

### Primary Key

| Atributo | Tipo | Descripcion |
|----------|------|-------------|
| `cache_key` (HASH) | String | Identificador unico del cache entry. Formato: `<namespace>:<key>` |

### Atributos principales

| Atributo | Tipo | Requerido | Descripcion |
|----------|------|-----------|-------------|
| `cache_key` | S | Si | Partition key. Ej. `ssm:/portfolio/turnstile-secret`, `query:top-countries`, `turnstile:abc123hash` |
| `value` | S | Si | Valor cacheado (JSON-serializado o bytes base64). Ver `serializers.py` |
| `value_type` | S | Si | Tipo del valor: `'string'` \| `'json'` \| `'bytes_b64'` |
| `created_at` | S | Si | ISO8601 timestamp (ej. `2026-05-14T12:34:56Z`) |
| `expires_at` | N | Si | Unix epoch seconds. **TTL attribute** → AWS borra cuando `now() > expires_at` |
| `tags` | SS | No | Set de strings para invalidation por tag (ej. `{"contacts", "recent"}`) |
| `lock_owner` | S | No | Lambda request_id del que tomo el lock (cache stampede prevention) |
| `lock_expires` | N | No | Unix epoch seconds del lock expiration |
| `stale_until` | N | No | Unix epoch seconds para SWR: devolver expirado hasta esta fecha |

### GSI (Global Secondary Index) — NO RECOMENDADO inicialmente

Inicialmente: **una sola tabla sin GSI**. Razon: volumen bajo y una sola query pattern
(by cache_key). Si en futuro necesitas:

- Listar por tag: `tag-index` GSI con PK=`tag`, SK=`cache_key` (sparse, solo items con tags)
- Listar por namespace: `namespace-index` GSI extrayendo prefix de `cache_key`

Por ahora: evitar duplicar writes. Agregar GSI cuando sea necesario.

## Ejemplo de items (real-world)

### Item 1: SSM Parameter cacheado

```yaml
cache_key: "ssm:/portfolio/turnstile-secret"
value: "1x0000000000000000000000000000000000000A"  # JSON string
value_type: "string"
created_at: "2026-05-14T10:00:00Z"
expires_at: 1747334400  # 5 minutos despues de created_at
tags: ["config", "secrets"]
# No lock_owner (read, no write)
# No stale_until (no SWR para secrets)
```

### Item 2: Query Neon con SWR

```yaml
cache_key: "query:top-countries"
value: "[{\"country\":\"US\",\"count\":1523}, ...]"  # JSON array stringified
value_type: "json"
created_at: "2026-05-14T08:00:00Z"
expires_at: 1747334400      # 30 minutos after created_at
stale_until: 1747336200     # 40 minutos (SWR window de 10min)
tags: ["analytics", "neon"]
lock_owner: null            # Lock fue liberado tras recompute
lock_expires: null
```

### Item 3: Cache bajo contention (con lock)

```yaml
cache_key: "turnstile:hash-of-token"
value: null                          # Aun computando
value_type: null
created_at: "2026-05-14T12:34:50Z"
expires_at: 1747334400               # 30 segundos
stale_until: null
tags: null
lock_owner: "lambda-request-id-xyz"  # Lambda A tomo el lock
lock_expires: 1747334355             # Expira en 5 segundos
```

Lambdas B, C esperan en busy-loop or devuelven valor previo.

## Validacion de schema

### CloudFormation / SAM template

```yaml
CacheTable:
  Type: AWS::DynamoDB::Table
  Properties:
    TableName: cache
    BillingMode: PAY_PER_REQUEST
    AttributeDefinitions:
      - AttributeName: cache_key
        AttributeType: S
    KeySchema:
      - AttributeName: cache_key
        KeyType: HASH
    TimeToLiveSpecification:
      AttributeName: expires_at
      Enabled: true
    # PointInTimeRecoverySpecification: # opcional
    #   PointInTimeRecoveryEnabled: true
    # Tags:
    #   - Key: Project
    #     Value: portfolio
    #   - Key: Environment
    #     Value: !Ref EnvironmentParam
```

### Validar con AWS CLI

```bash
aws dynamodb describe-table --table-name cache --region us-east-1

# Output includes:
# - BillingMode: PAY_PER_REQUEST
# - KeySchema: [{ AttributeName: cache_key, KeyType: HASH }]
# - TimeToLiveDescription.TimeToLiveStatus: ENABLED
```

## Naming convention para `cache_key`

Usar prefijo para evitar colisiones y facilitar debugging:

| Namespace | Prefix | Ejemplo |
|-----------|--------|---------|
| SSM Parameter Store | `ssm:` | `ssm:/portfolio/turnstile-secret` |
| Turnstile siteverify | `turnstile:` | `turnstile:abc123def456hash` |
| Neon query | `query:` | `query:top-countries` |
| GeoIP lookup | `geoip:` | `geoip:IP_ADDRESS` |
| Config | `config:` | `config:portfolio-settings` |
| User-Agent parse | `ua:` | `ua:Mozilla/5.0...hash` |

**Ventajas**:
- Evita colisiones accidentales
- Facilita Scan con `cache_key begins_with 'turnstile:'`
- Auto-documental (leyendo el key sabes el origen)

## Estimacion de storage

Con volumen esperado (~1000 reads/min, ~100 writes/min):

- Item promedio: ~1KB (valor cacheado + metadata)
- Items en un tiempo T (asumiendo TTL=300s): ~5000-10000 items activos
- Storage total: ~10-15 MB
- **Bien dentro del free tier de 25GB**

## Security considerations

- **IAM**: Policy restrictiva per Lambda (ver [.claude/docs/aws-dynamodb/09-security-best-practices.md](../aws-dynamodb/09-security-best-practices.md))
  ```json
  {
    "Effect": "Allow",
    "Action": ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:UpdateItem", "dynamodb:DeleteItem"],
    "Resource": "arn:aws:dynamodb:us-east-1:*:table/cache"
  }
  ```

- **Encryption**: DynamoDB encryption at rest por defecto (AWS-owned keys). Cambiar a KMS
  si datos muy sensibles (secrets en formato plaintext).

- **No exponer secrets directamente**: Si cacheando Turnstile secret o API keys,
  considerar encriptacion adicional (KMS) o usar AWS Secrets Manager Cache.

## Evolucion futura del schema

Si emerge el patrón de "invalidacion masiva", agregar:

```yaml
CacheTagIndex:
  Type: AWS::DynamoDB::Table
  Properties:
    TableName: cache-tag-index
    BillingMode: PAY_PER_REQUEST
    AttributeDefinitions:
      - AttributeName: tag
        AttributeType: S
      - AttributeName: cache_key
        AttributeType: S
    KeySchema:
      - AttributeName: tag
        KeyType: HASH
      - AttributeName: cache_key
        KeyType: RANGE
```

Esto elimina la necesidad de `Scan` en doc 05 (tag invalidation).
**Threshold**: cuando tenant `cache` > 100k items, agregar GSI.

## Referencias

- AWS Docs: [DynamoDB Key Schema](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.core.html)
- AWS Docs: [DynamoDB TTL](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/time-to-live-ttl-before-you-start.html)
- AWS Docs: [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)

