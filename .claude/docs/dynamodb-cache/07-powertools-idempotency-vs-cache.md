# 07. AWS Powertools Idempotency vs este Cache

> Clarificacion: idempotency decorator (@idempotent) de AWS Lambda Powertools
> **NO es un reemplazo** para este cache. Resuelven problemas DIFERENTES.

**Verificado**: 2026-05-14 — AWS Lambda Powertools 2.44.0, documentacion oficial 2026.

## Problema 1: Idempotency (Powertools)

### Caso de uso

```python
# contact-form handler
@logger.inject_lambda_context
@idempotent()
def handler_contact_form(event, context):
    """
    Lambda invocada por API Gateway con form de contacto.
    
    PROBLEMA: Si CF reintentar la request (timeout, 5xx), 
    la misma invocacion llega DOS VECES con el mismo event payload.
    
    SOLUCION: @idempotent decorator:
      - Hash el event completo
      - Store el hash en DynamoDB + resultado
      - Reintento con mismo event → retorna cached resultado (no ejecuta 2 veces)
    """
    email = event['body']['email']
    name = event['body']['name']
    
    # Esta logica executa SOLO UNA VEZ por invocacion unica
    send_email(email, f'Gracias {name}')
    save_contact_to_dynamodb(email, name)
    
    return {'statusCode': 200, 'body': 'OK'}
```

### Mecanica del @idempotent

```
CF POST /contact form (email=pablo@example.com)
  ↓
Lambda A recibe event {body: {email: pablo@example.com, ...}}
  ↓
@idempotent() calcula hash(event) = "abc123"
  ↓
DynamoDB: GET abc123 → no existe
  ↓
Ejecutar handler: send_email + save_contact
  ↓
DynamoDB: PUT abc123 = resultado (exito)
  ↓
Return 200

CF REINTENTO (timeout en respuesta)
  ↓
Lambda B recibe MISMO event {body: {email: pablo@example.com, ...}}
  ↓
@idempotent() calcula hash(event) = "abc123" (mismo hash)
  ↓
DynamoDB: GET abc123 → EXISTE
  ↓
Return cached resultado de Lambda A (sin ejecutar send_email 2 veces)
  ↓
Return 200
```

### Ventajas de @idempotent

✓ Previene duplicated processing de **mismo event**  
✓ Garantizado: hash del event es PK en Idempotency table  
✓ TTL: idempotency records expiran (default 1h)  
✓ Simple: solo decorator  
✓ Resuelve problema real: CF retries, SNS retries, etc.  

## Problema 2: Cache (este proyecto)

### Caso de uso

```python
# turnstile-verify handler
from common.cache import cached

@logger.inject_lambda_context
def handler_turnstile_verify(event, context):
    """
    Lambda que verifica Turnstile token contra siteverify API.
    
    PROBLEMA: Mismo token se valida MULTIPLES VECES en diferentes requests.
    Client A: POST /form {token: abc123} → Lambda verifica token
    Client B: POST /form {token: abc123} → Lambda reintenta verificar token (innecesario)
    Client C: POST /form {token: abc123} → Lambda reintenta verificar token (innecesario)
    
    Resultado: 3 requests a Turnstile backend (Cloudflare) por el MISMO token.
    
    SOLUCION: Cache
      - Primer cliente: verifica token, cachea resultado 30s
      - Segundo, tercero, N-esimos clientes: obtienen resultado cacheado (sin backend request)
    """
    token = event['body']['token']
    
    # Cachear resultado del verify
    @cached(ttl=30, namespace='turnstile')
    def verify_token(token: str) -> dict:
        # Este codigo SOLO ejecuta si cache miss (cada 30s maximo)
        return turnstile_siteverify(token)
    
    result = verify_token(token)
    return {'statusCode': 200 if result['success'] else 400, 'body': json.dumps(result)}
```

### Mecanica del cache

```
Client A: POST /form {token: abc123}
  ↓
@cached decorator: cache_key = "turnstile:verify_token:hash(abc123)"
  ↓
DynamoDB: GET cache_key → no existe (cache miss)
  ↓
Ejecutar verify_token: siteverify request a Cloudflare (500ms)
  ↓
DynamoDB: PUT cache_key = resultado, expires_at = now + 30s
  ↓
Return 200 con resultado

Client B: POST /form {token: abc123} (dentro de 30s)
  ↓
@cached decorator: cache_key = "turnstile:verify_token:hash(abc123)" (MISMO hash)
  ↓
DynamoDB: GET cache_key → EXISTE
  ↓
Return cached resultado (SIN siteverify request)
  ↓
Return 200 con resultado (10x mas rapido)
```

### Ventajas del cache

✓ Evita recomputar **mismo valor** (en tiempo T)  
✓ Reduce llamadas a backends caros (SSM, API externas, DB queries)  
✓ TTL configurable (30s para tokens, 1h para config)  
✓ Cache stampede prevention: lock distribuido  
✓ SWR: devolver stale mientras se refresca  

## Diferencia conceptual

| Aspecto | @idempotent (Powertools) | @cached (este proyecto) |
|--------|--------------------------|------------------------|
| **Scope** | Deduplicar **invocaciones identicas** | Deduplicar **computaciones identicas** |
| **Key** | Hash del **event payload** | Hash de **args de funcion** |
| **Problema resuelto** | CF retries, SNS retries, webhook retries | Backend latency, thundering herd |
| **TTL tipico** | 1h (duracion de idempotency window) | 30s - 1h (validez del valor) |
| **Storage** | `idempotency` DynamoDB table | `cache` DynamoDB table |
| **Cuando activar** | Handlers del tipo webhook, payment (puede recibir retries) | Handlers que usan valores computados |

## Cuando usar AMBOS (patrón recomendado)

```python
from aws_lambda_powertools.utilities.idempotency import idempotent
from common.cache import cached
import json

@idempotent()  # Deduplicar invocaciones identicas
@logger.inject_lambda_context
def handler_form_submission(event, context):
    """
    CF puede reintentar la POST (retries).
    Queremos que el mismo form NO se procese 2 veces.
    
    Dentro del handler, queries pueden ser identicas (multiples clientes mismo form).
    Queremos cachear las queries.
    """
    
    @cached(ttl=300, namespace='form', tags=['contacts'])
    def get_country_list():
        # Esta query tarda 2s
        # Con @cached: primera invocacion = 2s, siguientes en 5min = 0ms
        return list_countries_from_neon()
    
    email = event['body']['email']
    message = event['body']['message']
    
    # Usar cached function
    countries = get_country_list()
    
    # Procesar form
    save_contact(email, message, countries)
    send_confirmation_email(email)
    
    return {'statusCode': 200, 'body': json.dumps({'ok': True})}
```

### Flujo combinado

```
CF POST /form {email: pablo@example.com, message: "..."}
  ↓
Lambda A invocada
  ↓
@idempotent() → hash event = "req123"
  ↓
Idempotency table: GET req123 → no existe
  ↓
Dentro del handler:
  @cached(get_country_list) → cache_key = "form:get_country_list:hash()"
  ↓
Cache table: GET cache_key → no existe (primera invocacion)
  ↓
query_neon() → 2s
  ↓
Cache table: PUT cache_key = resultado
  ↓
save_contact() → enviar email
  ↓
Idempotency table: PUT req123 = resultado
  ↓
Return 200

CF REINTENTO (timeout)
  ↓
Lambda B invocada CON MISMO event
  ↓
@idempotent() → hash event = "req123" (MISMO)
  ↓
Idempotency table: GET req123 → EXISTE
  ↓
Return cached resultado de Lambda A (sin ejecutar handler)
  ↓
Return 200 (no duplicated email)

CF POST /form {email: pablo@example.com} (DIF message)
  ↓
Lambda C invocada
  ↓
@idempotent() → hash event = "req456" (DIFERENTE event)
  ↓
Idempotency table: GET req456 → no existe
  ↓
Dentro del handler:
  @cached(get_country_list) → cache_key = "form:get_country_list:hash()"
  ↓
Cache table: GET cache_key → EXISTE (guardado por Lambda A)
  ↓
Return cached resultado (0ms, sin query_neon)
  ↓
save_contact() → enviar email
  ↓
Idempotency table: PUT req456 = resultado
  ↓
Return 200
```

## Tabla de decisiones

```
¿El mismo EVENT payload puede llegar multiples veces?
→ SI: usar @idempotent

¿El mismo VALUE puede computarse multiples veces en el mismo periodo?
→ SI: usar @cached

¿Ambos?
→ AMBOS: @idempotent fuera, @cached dentro
```

## Ejemplo real: payment webhook

```python
from aws_lambda_powertools.utilities.idempotency import idempotent
from common.cache import cached

@idempotent()
def handler_payment_webhook(event, context):
    """
    Webhook de Stripe/payment provider.
    
    Problema 1: Stripe reintenta webhook si timeout → mismo event 2 veces
    Problema 2: Dentro del handler, consultamos customer data (redundante si invocaciones rapidamente)
    
    Solucion: @idempotent (deduplica retries) + @cached (deduplica queries)
    """
    
    @cached(ttl=60, namespace='stripe', tags=['payment'])
    def get_customer(customer_id: str) -> dict:
        # Customer no cambia frecuentemente
        # Con @cached: primera lookup = DB query, siguientes 60s = cache
        return stripe.customers.retrieve(customer_id)
    
    event_type = event['type']
    
    if event_type == 'charge.succeeded':
        charge = event['data']['object']
        customer_id = charge['customer']
        
        customer = get_customer(customer_id)  # Cached
        
        # Procesar pago (deduplicado por @idempotent)
        update_subscription_status(customer_id, 'active')
        send_invoice_email(customer['email'])
    
    return {'statusCode': 200}
```

## Configuracion de Powertools

```python
# core/settings/idempotency_config.py (dentro del Lambda)
from aws_lambda_powertools.utilities.idempotency import IdempotencyConfig

idempotency_config = IdempotencyConfig(
    event_key_jmespath='body',  # Usar solo el body, ignore headers
    raise_on_no_idempotent_record=False,
    use_local_cache=False,  # Usar DynamoDB, no in-memory
)

# core/handler.py (dentro del Lambda)
from aws_lambda_powertools.utilities.idempotency import idempotent
from config.idempotency_config import idempotency_config

@idempotent(config=idempotency_config)
def handler_webhook(event, context):
    ...
```

## Referencias

- AWS Docs: [Powertools Idempotency](https://docs.aws.amazon.com/powertools/python/latest/utilities/idempotency/)
- AWS Blog: [Handling Lambda functions idempotency with AWS Lambda Powertools](https://aws.amazon.com/blogs/compute/handling-lambda-functions-idempotency-with-aws-lambda-powertools/)
- Stripe Docs: [Webhook retries](https://stripe.com/docs/webhooks/endpoint)

