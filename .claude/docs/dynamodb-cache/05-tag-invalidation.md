# 05. Tag-Based Invalidation (soft delete + invalidate por categoria)

> Patron: cachear valores con etiquetas logicas ("contacts", "recent", "analytics").
> Invalidar multiples keys de un comando: `cache.invalidate(tag='contacts')`.

**Verificado**: 2026-05-14 — Pattern scalable hasta 100k items; GSI optimization documentada.

## Concepto

```
Problema: SSM Parameter Store cacheado bajo tag "config".
          Neon queries cacheadas bajo tag "analytics".
          
          Admin actualiza config → queremos invalidar TODO tag "config"
          Sin invalidation: items config siguen cached 5 minutos mas (stale data)

Solucion: tag-based invalidation
  cache.set('ssm:/portfolio/turnstile-secret', value, tags=['config', 'secrets'])
  cache.set('config:portfolio-settings', value, tags=['config'])
  ...
  
  # Admin: actualiza config
  cache.invalidate(tag='config')  # Soft-delete todos con tag "config"
  
  Resultado: items con tag "config" tienen expires_at = 0 (instantaneo)
```

## Implementacion

### 1. Set con tags

```python
def set_with_tags(
    cache_key: str,
    value: dict,
    ttl_seconds: int = 300,
    tags: list[str] | None = None,
) -> None:
    """
    Guardar valor con tags para invalidation.
    
    Args:
        cache_key: clave del cache
        value: valor a cachear
        ttl_seconds: tiempo de vida
        tags: lista de etiquetas (ej. ['config', 'secrets'])
    """
    import json
    from datetime import datetime, UTC
    
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['CACHE_TABLE_NAME'])
    
    now = int(time.time())
    
    item = {
        'cache_key': cache_key,
        'value': json.dumps(value),
        'value_type': 'json',
        'created_at': datetime.now(UTC).isoformat(),
        'expires_at': now + ttl_seconds,
    }
    
    if tags:
        item['tags'] = set(tags)  # DynamoDB StringSet
    
    table.put_item(Item=item)
```

### 2. Invalidate por tag (Scan + soft-delete)

```python
def invalidate_by_tag(tag: str) -> int:
    """
    Invalidar todos los items con un tag especifico.
    Metodo: Scan con FilterExpression + UpdateItem para cada match.
    
    Returns: numero de items invalidados
    
    Volumen esperado: <10k items = Scan rapido (5-10 RCU)
    Alternativa para >100k items: usar GSI (ver seccion abajo)
    """
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['CACHE_TABLE_NAME'])
    
    invalidated_count = 0
    now = int(time.time())
    
    try:
        # Scan con FilterExpression
        response = table.scan(
            FilterExpression='contains(tags, :tag)',
            ExpressionAttributeValues={':tag': tag},
            ProjectionExpression='cache_key',  # Solo necesitamos la clave
        )
        
        # Soft-delete: set expires_at = now (expira inmediatamente)
        for item in response.get('Items', []):
            table.update_item(
                Key={'cache_key': item['cache_key']},
                UpdateExpression='SET expires_at = :now',
                ExpressionAttributeValues={':now': now},
            )
            invalidated_count += 1
        
        # Paginate si hay mas items
        while 'LastEvaluatedKey' in response:
            response = table.scan(
                FilterExpression='contains(tags, :tag)',
                ExpressionAttributeValues={':tag': tag},
                ProjectionExpression='cache_key',
                ExclusiveStartKey=response['LastEvaluatedKey'],
            )
            for item in response.get('Items', []):
                table.update_item(
                    Key={'cache_key': item['cache_key']},
                    UpdateExpression='SET expires_at = :now',
                    ExpressionAttributeValues={':now': now},
                )
                invalidated_count += 1
        
        print(f"Invalidated {invalidated_count} items with tag '{tag}'")
        return invalidated_count
    
    except Exception as e:
        print(f"Error invalidating tag '{tag}': {e}")
        raise
```

### 3. Ejemplo: Invalidacion de config

```python
async def handler_config_update(event, context):
    """
    Lambda trigger cuando config del proyecto cambia.
    Invalida todos los items con tag "config".
    """
    # Admin actualizo config en SSM Parameter Store
    # EventBridge o SNS trigger llama esta Lambda
    
    config_updated_tag = 'config'
    invalidated = invalidate_by_tag(config_updated_tag)
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': f'Invalidated {invalidated} cache items',
            'tag': config_updated_tag,
        })
    }
```

## Variante: Multi-tag invalidation

```python
def invalidate_by_tags(tags: list[str], match_all: bool = False) -> int:
    """
    Invalidar items que matcheen multiples tags.
    
    Args:
        tags: lista de tags a buscar
        match_all: True = item debe tener TODOS los tags (AND)
                   False = item debe tener CUALQUIERA de los tags (OR)
    """
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['CACHE_TABLE_NAME'])
    
    invalidated_count = 0
    now = int(time.time())
    
    if match_all:
        # AND: item.tags contains tag1 AND tag2 AND tag3
        filter_expr = ' AND '.join([f'contains(tags, :tag{i})' for i in range(len(tags))])
        values = {f':tag{i}': tag for i, tag in enumerate(tags)}
    else:
        # OR: item.tags contains tag1 OR tag2 OR tag3
        filter_expr = ' OR '.join([f'contains(tags, :tag{i})' for i in range(len(tags))])
        values = {f':tag{i}': tag for i, tag in enumerate(tags)}
    
    response = table.scan(
        FilterExpression=filter_expr,
        ExpressionAttributeValues=values,
        ProjectionExpression='cache_key',
    )
    
    for item in response.get('Items', []):
        table.update_item(
            Key={'cache_key': item['cache_key']},
            UpdateExpression='SET expires_at = :now',
            ExpressionAttributeValues={':now': now},
        )
        invalidated_count += 1
    
    return invalidated_count
```

## Optimizacion: GSI para >100k items

Si `cache` tabla crece a >100k items, Scan se vuelve lento (5-10 RCU por scan).
Agregar GSI para evitar Scan:

### CloudFormation / SAM

```yaml
CacheTable:
  Type: AWS::DynamoDB::Table
  Properties:
    TableName: cache
    BillingMode: PAY_PER_REQUEST
    AttributeDefinitions:
      - AttributeName: cache_key
        AttributeType: S
      - AttributeName: tag
        AttributeType: S
    KeySchema:
      - AttributeName: cache_key
        KeyType: HASH
    GlobalSecondaryIndexes:
      - IndexName: tag-index
        KeySchema:
          - AttributeName: tag
            KeyType: HASH
          - AttributeName: cache_key
            KeyType: RANGE
        Projection:
          ProjectionType: KEYS_ONLY  # Solo cache_key, no value
    TimeToLiveSpecification:
      AttributeName: expires_at
      Enabled: true
```

### Invalidate via GSI (sin Scan)

```python
def invalidate_by_tag_via_gsi(tag: str) -> int:
    """
    Invalidar usando GSI (sin Scan).
    Mucho mas rapido para >100k items.
    """
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['CACHE_TABLE_NAME'])
    
    invalidated_count = 0
    now = int(time.time())
    
    # Query GSI directamente por tag
    response = table.query(
        IndexName='tag-index',
        KeyConditionExpression='tag = :tag',
        ExpressionAttributeValues={':tag': tag},
        ProjectionExpression='cache_key',
    )
    
    for item in response.get('Items', []):
        table.update_item(
            Key={'cache_key': item['cache_key']},
            UpdateExpression='SET expires_at = :now',
            ExpressionAttributeValues={':now': now},
        )
        invalidated_count += 1
    
    # Paginate
    while 'LastEvaluatedKey' in response:
        response = table.query(
            IndexName='tag-index',
            KeyConditionExpression='tag = :tag',
            ExpressionAttributeValues={':tag': tag},
            ProjectionExpression='cache_key',
            ExclusiveStartKey=response['LastEvaluatedKey'],
        )
        for item in response.get('Items', []):
            table.update_item(
                Key={'cache_key': item['cache_key']},
                UpdateExpression='SET expires_at = :now',
                ExpressionAttributeValues={':now': now},
            )
            invalidated_count += 1
    
    return invalidated_count
```

## Soft-delete vs hard-delete

### Soft-delete (RECOMENDADO)

```python
# Soft: set expires_at = now
table.update_item(
    Key={'cache_key': key},
    UpdateExpression='SET expires_at = :now',
    ExpressionAttributeValues={':now': int(time.time())},
)
# Ventajas: rapido, no elimina storage (TTL lo hace eventual), atomic
# Desventajas: items fantasma por 48h
```

### Hard-delete

```python
# Hard: eliminar item inmediatamente
table.delete_item(Key={'cache_key': key})
# Ventajas: limpio
# Desventajas: mas lento, usa WCU, requiere per-item delete
```

Para este caso: **soft-delete** es mejor (mas rapido, multiple items en un update).

## Tags recomendadas por use case

| Use case | Tags recomendadas |
|----------|-------------------|
| SSM Parameter Store | `['config', 'secrets']` |
| Turnstile siteverify | `['security', 'turnstile']` |
| Neon queries | `['analytics', 'neon', 'recent']` |
| GeoIP lookups | `['geoip', 'public']` |
| Leaderboards | `['realtime', 'gaming']` |

Consejo: mantener <5 tags por item, usar jerarquia (ej. `analytics` > `recent`).

## Costo estimado

**Scenario**: 50k items en cache, invalidate por 1 tag que afecta 5k items

**Sin GSI (Scan)**:
- Scan: 1 RCU (read ~1000 items per RCU) × 50 scans = 50 RCU
- Update: 5000 items × 1 WCU = 5000 WCU
- Total: ~5050 RCU+WCU = ~$6.30 por invalidacion

**Con GSI (Query)**:
- Query: 1 RCU (fast lookup) × 5 queries = 5 RCU (sparse GSI, <100 RCU total)
- Update: 5000 items × 1 WCU = 5000 WCU
- Total: ~5005 RCU+WCU = ~$6.26 por invalidacion

Conclusion: GSI ahorra 45 RCU (~$0.04) por invalidacion. Threshold: agregar GSI
cuando `invalidate_by_tag` se llama >100 veces/mes o items >100k.

## Anti-patrones

❌ Hard-delete todos los items (lento, costoso)  
❌ Tag string vacio o null  
❌ >10 tags por item (confuso, Scan lento)  
❌ Invalidation sin comprobar que funciono (verify count > 0)  
❌ Olvidar que TTL es eventual (items fantasma ~48h)  

## Referencias

- AWS: [DynamoDB Query vs Scan](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Query.html)
- AWS: [DynamoDB GSI](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/GSI.html)

