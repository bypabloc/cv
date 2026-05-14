# boto3 API: DynamoDB en Python 3.13

> Referencia practica para codificar handlers Lambda con DynamoDB usando boto3.

## Setup

```python
import boto3
from boto3.dynamodb.conditions import Key, Attr
from decimal import Decimal
import time

# High-level Resource API (recomendado)
dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
contacts_table = dynamodb.Table('contacts')
tracking_table = dynamodb.Table('tracking')

# Low-level Client API (menos usado, mas control)
client = boto3.client('dynamodb', region_name='us-west-2')
```

## Operaciones Basicas

### PUT_ITEM (Escribir)

```python
import uuid

# Insertar contacto
item = {
    'id': str(uuid.uuid4()),
    'email': 'user@example.com',
    'name': 'Juan Pérez',
    'message': 'Interesado en fintech',
    'service_type': 'fintech',
    'company': 'Acme Corp',
    'budget': Decimal('5000'),      # IMPORTANTE: usar Decimal para numeros
    'created_at': int(time.time()),
}

# IMPORTANTE: No especifiques type (S, N, etc.) con Resource API
contacts_table.put_item(Item=item)
```

### GET_ITEM (Leer por PK)

```python
# Obtener contacto por ID
response = contacts_table.get_item(
    Key={'id': '01ARZ3NDEKTSV4RRFFQ69G5FAV'}
)

item = response.get('Item')
if item:
    print(f"Encontrado: {item['name']}")
else:
    print("No encontrado")
```

### QUERY (Buscar por PK + opcional SK)

```python
# Query: todos los eventos de una sesion
response = tracking_table.query(
    KeyConditionExpression=Key('session_id').eq('session#123'),
    ScanIndexForward=True  # Orden: True=ASC (chronological), False=DESC
)

items = response.get('Items', [])
print(f"Encontrados {len(items)} eventos")
for item in items:
    print(item['url'])
```

**Con rango de sort key:**

```python
response = tracking_table.query(
    KeyConditionExpression=(
        Key('session_id').eq('session#123') &
        Key('page_id').between('01ARZ3NDEK', '01ARZ3NDEZ')  # Rango en SK
    )
)
```

### UPDATE_ITEM (Actualizar)

```python
# Actualizar atributo de contacto
response = contacts_table.update_item(
    Key={'id': 'id#123'},
    UpdateExpression='SET company = :company, updated_at = :now',
    ExpressionAttributeValues={
        ':company': 'New Corp',
        ':now': int(time.time()),
    },
    ReturnValues='ALL_NEW'  # Retorna item actualizado
)

updated_item = response['Attributes']
```

### DELETE_ITEM (Borrar)

```python
# Borrar contacto
contacts_table.delete_item(
    Key={'id': 'id#123'}
)
```

### SCAN (Busqueda Completa - EVITAR en Produccion)

```python
# Scan de tabla completa (COSTOSO)
response = contacts_table.scan()

# MAS EFICIENTE: Scan con filter
response = contacts_table.scan(
    FilterExpression=Attr('service_type').eq('fintech')
)

items = response['Items']
# Paginacion
while 'LastEvaluatedKey' in response:
    response = contacts_table.scan(
        ExclusiveStartKey=response['LastEvaluatedKey'],
        FilterExpression=Attr('service_type').eq('fintech')
    )
    items.extend(response['Items'])
```

## Decimal: Manejo de Numeros

**CRITICAL:** DynamoDB almacena numeros como `Decimal`, no `float`.

```python
from decimal import Decimal

# INCORRECTO (float)
table.put_item(Item={'id': '1', 'price': 99.99})  # Float!

# CORRECTO (Decimal)
table.put_item(Item={'id': '1', 'price': Decimal('99.99')})

# En Lambda responses, convertir Decimal a float/str
import json
from decimal import Decimal

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

json.dumps(item, cls=DecimalEncoder)
```

## Conditional Writes (No Sobrescribir)

```python
# Put solo si id NO existe (anti-duplicates)
try:
    contacts_table.put_item(
        Item=item,
        ConditionExpression='attribute_not_exists(id)'
    )
    print("Insertado")
except contacts_table.meta.client.exceptions.ConditionalCheckFailedException:
    print("ID ya existe, omitido")

# Update solo si version actual == expected (optimistic lock)
contacts_table.update_item(
    Key={'id': 'id#123'},
    UpdateExpression='SET #v = :new_v',
    ConditionExpression='#v = :old_v',
    ExpressionAttributeNames={'#v': 'version'},
    ExpressionAttributeValues={
        ':new_v': 2,
        ':old_v': 1,  # Fail si version != 1 ahora
    }
)
```

## Batch Operations

```python
# Batch write (max 25 items)
with contacts_table.batch_writer(batch_size=25) as batch:
    for i in range(100):
        batch.put_item(Item={
            'id': f'id#{i}',
            'email': f'user{i}@example.com',
        })
```

## Lambda Handler Completo (Contactos)

```python
import json
import boto3
import uuid
import time
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
contacts_table = dynamodb.Table('contacts')

def lambda_handler(event, context):
    """
    Recibe POST de form contacto.
    Guardar en DynamoDB contacts table.
    """
    try:
        body = json.loads(event.get('body', '{}'))
        
        item = {
            'id': str(uuid.uuid4()),
            'email': body['email'],
            'name': body['name'],
            'message': body['message'],
            'service_type': body.get('service_type', 'generic'),
            'company': body.get('company'),
            'budget': Decimal(str(body.get('budget', 0))),
            'created_at': int(time.time()),
        }
        
        contacts_table.put_item(Item=item)
        
        return {
            'statusCode': 200,
            'body': json.dumps({'id': item['id']}),
        }
    except Exception as e:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': str(e)}),
        }
```

## Lambda Handler Completo (Tracking)

```python
import json
import boto3
import uuid
import time

dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
tracking_table = dynamodb.Table('tracking')

def lambda_handler(event, context):
    """
    Tracking pixel: registrar page view.
    """
    try:
        body = json.loads(event.get('body', '{}'))
        now = int(time.time())
        
        item = {
            'session_id': body['session_id'],
            'page_id': str(uuid.uuid4()),
            'url': body['url'],
            'referrer': body.get('referrer'),
            'utm_source': body.get('utm_source'),
            'created_at': now,
            'expires_at': now + (60 * 24 * 60 * 60),  # TTL 60 dias
        }
        
        tracking_table.put_item(Item=item)
        
        return {'statusCode': 204}  # No content
    except Exception as e:
        return {'statusCode': 400, 'body': json.dumps({'error': str(e)})}
```

## Error Handling

```python
from botocore.exceptions import ClientError

try:
    contacts_table.get_item(Key={'id': 'invalid'})
except ClientError as e:
    if e.response['Error']['Code'] == 'ResourceNotFoundException':
        print("Tabla no existe")
    elif e.response['Error']['Code'] == 'ValidationException':
        print("Validacion fallida")
    else:
        print(f"DynamoDB error: {e}")
```

## Paso Siguiente

- Deployment con SAM: [07-deployment-sam.md](07-deployment-sam.md)
- Seguridad: [09-security-best-practices.md](09-security-best-practices.md)
