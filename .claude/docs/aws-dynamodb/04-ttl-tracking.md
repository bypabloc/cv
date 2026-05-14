# Time To Live (TTL) para Tabla Tracking

> TTL en DynamoDB borra items automáticamente. Crítico para tabla `tracking` (60 dias retencion).

## ¿Qué es TTL?

Atributo Number (Unix epoch timestamp en segundos) que indica cuándo DynamoDB debe borrar un item automáticamente.

DynamoDB **verifica diariamente** items expirados y los borra sin costo (no consume WCU). Borrado ocurre **dentro de 48 horas** post-expiracion (no inmediato).

## Como Funciona

### 1. Definir Atributo TTL

En la tabla `tracking`, crear atributo `expires_at` con valor = Unix epoch seconds.

```python
import time

# Para un tracking event hoy, expirar en 60 dias
now = int(time.time())
expires_at = now + (60 * 24 * 60 * 60)  # +60 dias en segundos

item = {
    'session_id': '01ARZ3NDEKTSV4RRFFQ69G5FAV',
    'page_id': '01ARZ3NDEKTSV4RRFFQ69G5FAG',
    'url': 'https://the-full-stack.com/projects',
    'created_at': now,
    'expires_at': expires_at,   # <-- TTL attribute
}
```

### 2. Habilitar TTL en la Tabla

En SAM template:

```yaml
TrackingTable:
  Type: AWS::DynamoDB::Table
  Properties:
    TableName: tracking
    BillingMode: PAY_PER_REQUEST
    AttributeDefinitions:
      - AttributeName: session_id
        AttributeType: S
      - AttributeName: page_id
        AttributeType: S
    KeySchema:
      - AttributeName: session_id
        KeyType: HASH
      - AttributeName: page_id
        KeyType: RANGE
    TimeToLiveSpecification:
      AttributeName: expires_at        # Nombre del atributo
      Enabled: true                    # Habilitar TTL
```

### 3. Items Expirados

Después que un item alcanza su `expires_at`:
- Puede ser leído durante ~48 horas (aún visible)
- DynamoDB lo borra automáticamente (sin costo)
- Típicamente desaparece en 48h

**Recomendación:** Filtrar en aplicacion si necesitas garantizar "no mostrar expirados":

```python
import time

response = table.query(
    KeyConditionExpression='session_id = :sid',
    ExpressionAttributeValues={':sid': 'session#123', ':now': int(time.time())},
    FilterExpression='expires_at > :now'  # Excluir expirados
)
```

## Costos

**GRATIS.** TTL NO consume WCU al borrar. Ahorro masivo:

### Comparativa: Sin vs Con TTL

**Sin TTL (manual delete):**
- 15000 tracking items/mes × 1 item borrado después 60d = 250 items/dia x 60 dias = 15000 WCU/mes solo en deletes
- Costo: $1.25 × (15000 / 1M) = $0.01875/mes (ignore otros writes)

**Con TTL (automático):**
- Costo: $0 (borrado automático)
- Storage: ~0.5GB media (15000 items × 0.3KB × capacidad media de 2-3%)
- Ahorro: 100% en write cost de delete

**Para este portfolio:** TTL ahorra ~$0.02/mes, pero lo más importante es **simplicidad operacional** (no gestar deletes manual).

## Edge Cases

### 1. Items Sin TTL

Si no defines `expires_at`, el item **no se borra**. Esto está permitido (sparse attribute).

```python
# Tabla puede tener items mixed
{
    'session_id': '001',
    'expires_at': 1726000000,   # Sera borrado
}
{
    'session_id': '002',
    # Sin expires_at → se queda para siempre
}
```

### 2. Cambiar TTL Después

Si modificas un item y cambias `expires_at`, DynamoDB recalcula la expiracion:

```python
table.update_item(
    Key={'session_id': '001', 'page_id': '001'},
    UpdateExpression='SET expires_at = :new_expires',
    ExpressionAttributeValues={':new_expires': int(time.time()) + (90 * 86400)}
)
```

### 3. Items Leidos Después Expiracion

Item expirado pero no borrado aún puede ser leído:

```python
# Item expirado hace 10 horas, pero aún en tabla (borro pending)
item = table.get_item(Key={'session_id': '001', 'page_id': '001'})
print(item['Item'])  # Retorna el item aún
```

**No contar con esto:** Asumir que post-expiracion el item NO existe.

## Configuracion para Tracking

Template SAM completo (relevant part):

```yaml
Resources:
  TrackingTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: !Sub '${Environment}-tracking'
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - AttributeName: session_id
          AttributeType: S
        - AttributeName: page_id
          AttributeType: S
      KeySchema:
        - AttributeName: session_id
          KeyType: HASH
        - AttributeName: page_id
          KeyType: RANGE
      TimeToLiveSpecification:
        AttributeName: expires_at
        Enabled: true
      Tags:
        - Key: Environment
          Value: !Ref Environment
        - Key: Purpose
          Value: PageViewTracking
```

Lambda handler:

```python
import time
import uuid
import boto3

dynamodb = boto3.resource('dynamodb')
tracking_table = dynamodb.Table('tracking')

def lambda_handler(event, context):
    session_id = event.get('session_id')
    url = event.get('url')
    now = int(time.time())
    
    item = {
        'session_id': session_id,
        'page_id': str(uuid.uuid4()),
        'url': url,
        'created_at': now,
        'expires_at': now + (60 * 24 * 60 * 60),  # Expirar en 60 dias
    }
    
    tracking_table.put_item(Item=item)
    return {'statusCode': 200}
```

## Paso Siguiente

- Tabla contacts (SIN TTL): [06-boto3-python.md](06-boto3-python.md)
- Deploy: [07-deployment-sam.md](07-deployment-sam.md)
