# Cold start optimization

> Anatomia de init phase, tecnicas para reducir tiempo, SnapStart trade-offs,
> layers vs zip, package size, lambda power tuning, connection pooling.

[← Anterior: Powertools](./03-powertools.md) | [Siguiente: Deployment SAM →](./05-deployment-sam.md)

## Init phase: que pasa ahi

Durante init phase (antes de invocar handler), Lambda:

1. Carga el runtime Python (VM)
2. Importa modulos top-level (`import boto3`, `import requests`, etc.)
3. Ejecuta codigo fuera del handler (variable globales, inicializaciones)
4. Prepara contexto de ejecucion

Estos pasos son **sincronos y obligatorios**. No puedes saltar init phase.

Tipico desglose:

```
Init phase (~200-500ms):
  └─ Load runtime: 50-100ms
  └─ Import boto3: 50-80ms
  └─ Import requests: 30-50ms
  └─ Import pydantic: 40-60ms
  └─ Import powertools: 30-50ms
  └─ Global code execution: 0-50ms (depende tu codigo)
  └─ Total: 200-390ms (variable segun deps)

Invocation (~50-100ms):
  └─ Handler runs
  └─ API calls (DynamoDB, SES): 50-200ms
  └─ Total: 100-200ms

Cold start total: ~300-600ms
```

Con SnapStart, el snapshot se toma despues de init phase, y restore es
~10ms (90% mas rapido).

## Lazy loading: imports dentro del handler

Mover imports caros al handler reduce init phase:

```python
# MAL: imports al top-level
import boto3
import requests
import pandas  # PESADA (numpy dependency)

def handler(event, context):
    # boto3 ya cargado
    s3 = boto3.client('s3')

# BIEN: imports lazy (solo cuando necesario)
def handler(event, context):
    import boto3
    import requests
    s3 = boto3.client('s3')
```

Desventaja: si el handler se invoca multiples veces rapido (cold start),
el import se repite. Solo util si:
- Import es **muy pesado** (pandas, numpy, scipy)
- Invocacion es esporadica (contact-form: ~100 req/mes)
- 99% de las veces la Lambda no llama ese modulo

Para contact-form: **NO aplica** (boto3 siempre se necesita).

## Layers: dividir dependencias

Lambda Layers son archives `.zip` que se combinan en `layer/` directory
dentro del execution environment.

```
function.zip
└─ index.py (handler)

layer.zip
└─ python/lib/site-packages/
   ├─ boto3/
   ├─ requests/
   └─ pydantic/
```

Runtime combina ambos antes de invocacion. Benefit:
- Reutilizar layer en multiples funciones (menos downloads)
- Separar handler de dependencies (mas limpio)
- Layer cachea en Lambda, re-usar no duplica init time

**Para este proyecto**: 1 layer con `boto3`, `requests`, `pydantic`,
`aws-lambda-powertools`. Reusable en contact-form, tracking-pixel,
stream-processor.

Desventaja: max 5 layers por function, max size 250MB total (uncompressed).

Creacion:

```bash
# Estructura
mkdir -p python/lib/python3.13/site-packages
cd python

# Instalar deps
pip install -r requirements.txt -t lib/python3.13/site-packages

# Empaquetar
zip -r ../lambda-layer.zip python

# Deploy via SAM
Layers:
  - !Sub 'arn:aws:lambda:${AWS::Region}:${AWS::AccountId}:layer:portfolio-python-deps:1'
```

## Package size minimization

Lambda limits:
- Zip uncompressed: 50 MB
- With layers: 250 MB total uncompressed

Medir tamanio:

```bash
zip -r function.zip src/ __init__.py -l  # lista con tamanios
du -sh function.zip
unzip -l function.zip | tail -1  # tamanio uncompressed
```

Reduccion:

```bash
# Remover pyc (compilados):
find . -name '*.pyc' -delete
find . -name '__pycache__' -delete

# Remover tests de deps:
find . -path '*tests*' -delete
find . -path '*test*' -delete

# Remover documentacion:
find . -name '*.md' -delete

# Usar wheels en lugar de source:
pip install --only-binary :all: -r requirements.txt -t layer/
```

Típico:
- `boto3`: 30 MB (core AWS SDK)
- `requests`: 2 MB
- `pydantic`: 8 MB
- `aws-lambda-powertools`: 5 MB
- **Total**: ~45 MB (dentro limit de 50MB function-only)

Con layer: boto3 + powertools en layer (reutilizable), handler + business
logic en function (redeployar mas rapido).

## SnapStart (Python 3.13 + Nov 2025)

SnapStart toma snapshot del VM despues de init phase. Restore es ~10ms.

**Habilitar en SAM**:

```yaml
Properties:
  Handler: index.handler
  Runtime: python3.13
  SnapStart:
    ApplyOn: PublishedVersions  # Snapshot en deploy
```

SnapStart requiere **runtime hooks** para clean re-initialization:

```python
import json
from aws_lambda_powertools import Logger

logger = Logger()

# Llamado ANTES de snapshot (init phase)
def snapshot_handler(handler):
    logger.info('Taking snapshot')
    # Aqui: inicializar conexiones que puedan expirar
    return handler

# Llamado DESPUES de restore (antes de handler)
def restore_handler(handler):
    logger.info('Restoring from snapshot')
    # Aqui: limpiar state obsoleto (credentials, connections)
    return handler

# Registrar hooks
if hasattr(__import__('aws_lambda_powertools'), '_serverless_runtime'):
    import aws_lambda_powertools._serverless_runtime as rt
    rt.register_snapshot_handler(snapshot_handler)
    rt.register_restore_handler(restore_handler)
```

**Cost trade-off**: SnapStart cuesta +15% de memoria (almacenar snapshot en S3).
Para 512MB memory:
- Normal: $0.0000166667 * 512 * 1M / (1000*1000) = $8.53/mes
- SnapStart: $8.53 * 1.15 = $9.81/mes

**Recomendacion para este caso**: 
- contact-form: MAYBE (si cold start es critico, los form submissions son
  esporadicos asi que el cost extra vale pena)
- tracking-pixel: NO (bajo latency requirement)
- stream-processor: NO (invocacion async desde DynamoDB Streams, cold start
  no es percibido por el usuario)

## Connection pooling y reutilizacion global

boto3 clients **SI pueden ser globales** (reutilizables entre invocaciones):

```python
import boto3

# Global: inicializado en init phase, reutilizado en warm starts
dynamodb = boto3.resource('dynamodb')
ses = boto3.client('ses')

def handler(event, context):
    # Reutiliza connection pool
    table = dynamodb.Table('contacts')
    table.put_item(Item={...})
    
    ses.send_email(...)
```

Lambda **reutiliza el process** entre warm invocaciones, asi que las
conexiones persisten. EXCEPTO: timeout > 15 min, o function update.

Benefit: boto3 connection pool se calienta (~50-100ms saved por invocacion
posterior).

## Lambda Power Tuning

Herramienta AWS para medir exact memory/duration/cost tradeoff:

```bash
# Instalar CLI (opcional)
npm install -g lambda-power-tuning

# O usar SAR app
# https://serverlessrepo.aws.amazon.com/applications/arn:aws:serverlessrepo:us-east-1:394349908253:applications/lambda-power-tuning

# Invocar
lambda-power-tuning \
  --function contact-form \
  --payload '{"httpMethod":"POST","body":"..."}' \
  --num-runs 10 \
  --from 256 \
  --to 3008 \
  --step 256
```

Output: optimal memory + cost breakdown.

Tipico resultado:
- Menor memory = mayor duration (longer billed time)
- Optimal memory esta en punto donde: cost = memory_price + extra_duration_price
- Para Python 3.13 + boto3 + API calls, ~512MB es optimal

## Comparativa

| Tecnica | Effort | Impact | Cost |
|---------|--------|--------|------|
| Import en top-level (ya hecho) | 0 | baseline | baseline |
| Lazy imports (pandas, scipy) | Low | +50-100ms save | same |
| Layer + smaller function | Medium | +10-30ms deploy | same |
| SnapStart | Low | -270ms cold start | +15% memory |
| Provisioned concurrency | High | 0ms cold start | +0.015/unit/hr |
| Arm64 architecture | Low | +19% CPU | -20% cost |

**Para este proyecto** (low traffic, esporadico):
1. SnapStart: opcionalidad, evaluate cost/benefit post-deploy
2. Layer: recomendado (reutilizable en 3 functions)
3. Lazy import: NO (overhead > benefit)
4. Provisioned: NO (no hay traffic suficiente)

Verificado a fecha 2026-05-13.
