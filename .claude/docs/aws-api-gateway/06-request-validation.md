# Request validation con JSON Schema

> Validar requests ANTES de invocar Lambda. API Gateway rechaza invalid
> requests con 400, sin costo Lambda. Ahorra dinero.

[← CORS security](./05-cors-security.md) | [README](./README.md) | [Siguiente: Deployment SAM →](./07-deployment-sam.md)

## Por que validar en API Gateway

Invocar Lambda cuesta dinero (incluso si falla). Si el cliente envia un
request invalido (body malformado, email vacio, etc.), rechazarlo en
API Gateway ANTES de invocar Lambda.

Ventajas:
- **Costo**: 0 invocaciones Lambda para requests invalidos
- **Velocidad**: respuesta 400 en <10ms (sin cold start Lambda)
- **Consistencia**: reglas de validacion en un solo lugar (no en cada Lambda)

## JSON Schema en API Gateway

API Gateway soporta **JSON Schema draft 4** para validar request body.

Ejemplo schema para /contact:

```json
{
  "type": "object",
  "required": ["email", "message"],
  "properties": {
    "email": {
      "type": "string",
      "format": "email",
      "minLength": 5,
      "maxLength": 254
    },
    "message": {
      "type": "string",
      "minLength": 10,
      "maxLength": 1000
    },
    "name": {
      "type": "string",
      "minLength": 1,
      "maxLength": 100
    }
  },
  "additionalProperties": false
}
```

Validaciones:
- `email` REQUERIDO, formato email, 5-254 caracteres
- `message` REQUERIDO, 10-1000 caracteres
- `name` OPCIONAL, 1-100 caracteres
- Sin campos extra permitidos (`additionalProperties: false`)

## Configuracion SAM

En SAM template, definir models y validators:

```yaml
Resources:
  PortfolioApi:
    Type: AWS::Serverless::Api
    Properties:
      StageName: prod
      Models:
        ContactRequest:
          type: object
          required:
            - email
            - message
          properties:
            email:
              type: string
              format: email
              minLength: 5
              maxLength: 254
            message:
              type: string
              minLength: 10
              maxLength: 1000
            name:
              type: string
              minLength: 1
              maxLength: 100
          additionalProperties: false
      
      MethodSettings:
        - ResourcePath: /contact
          HttpMethod: POST
          RequestValidatorSettings:
            ValidateRequestBody: true
            ValidateRequestParameters: false

  ContactFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: portfolio-contact
      Runtime: python3.13
      Handler: functions/contact.handler
      Events:
        ContactApi:
          Type: Api
          Properties:
            RestApiId: !Ref PortfolioApi
            Path: /contact
            Method: POST
            RequestModel:
              Model: ContactRequest
              Required: true  # Requerir modelo
```

Asi, API Gateway rechaza requests que no matchean el schema.

## Respuesta de validacion fallida

Si la validacion falla, API Gateway devuelve 400:

```
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "message": "Invalid request body",
  "details": [
    "email: Must be a valid email address",
    "message: Must be at least 10 characters"
  ]
}
```

El cliente ve esto inmediatamente sin invocar Lambda.

## Validacion de headers y query params

Tambien puedes validar headers y query strings:

```yaml
MethodSettings:
  - ResourcePath: /contact
    HttpMethod: POST
    RequestValidatorSettings:
      ValidateRequestBody: true
      ValidateRequestParameters: true  # Validar headers y query
```

Ejemplo: requerir header `x-api-key` para /validate-turnstile:

```yaml
Models:
  TurnstileRequest:
    type: object
    required:
      - token
    properties:
      token:
        type: string
        minLength: 10
```

Headers requeridos se declaran en OpenAPI inline (SAM DefinitionBody).

## Validacion de query params

Ejemplo: requerir `campaign_id` en query string de /track:

```yaml
MethodSettings:
  - ResourcePath: /track
    HttpMethod: POST
    RequestParameters:
      method.request.querystring.campaign_id: true  # Requerido
```

Si falta, API Gateway devuelve 400 sin invocar Lambda.

## Patron: diferentes schemas por endpoint

Cada endpoint puede tener su propio schema:

```yaml
Models:
  ContactRequest:
    # ... ContactRequest schema
  
  TrackPixelRequest:
    type: object
    required:
      - page_url
      - visitor_id
    properties:
      page_url:
        type: string
        format: uri
      visitor_id:
        type: string
        pattern: '^[a-f0-9]{36}$'  # UUID
      referrer:
        type: string
        format: uri
  
  TurnstileValidationRequest:
    type: object
    required:
      - token
      - ip_address
    properties:
      token:
        type: string
        minLength: 87  # Turnstile token length
      ip_address:
        type: string
        format: ipv4

MethodSettings:
  - ResourcePath: /contact
    HttpMethod: POST
    RequestParameters:
      method.request.header.Content-Type: true
  - ResourcePath: /track
    HttpMethod: POST
    RequestParameters:
      method.request.querystring.campaign_id: true
  - ResourcePath: /validate-turnstile
    HttpMethod: POST
    RequestParameters:
      method.request.header.Authorization: true
```

## Validacion de tipos de datos

JSON Schema draft 4 soporta:

| Tipo | Ejemplo |
|------|---------|
| `string` | `"hello"` |
| `number` | `42`, `3.14` |
| `integer` | `42` |
| `boolean` | `true`, `false` |
| `array` | `[1, 2, 3]` |
| `object` | `{"key": "value"}` |
| `null` | `null` |

Restricciones:
- `minLength`, `maxLength` — strings
- `minimum`, `maximum` — numbers
- `pattern` — regex (ej. UUID, email)
- `format` — validadores built-in (email, uri, ipv4, etc.)
- `enum` — valores permitidos
- `items` — esquema de elementos en array
- `properties` — campos de objetos

Ejemplo exhaustivo:

```json
{
  "type": "object",
  "required": ["event_type", "timestamp", "data"],
  "properties": {
    "event_type": {
      "type": "string",
      "enum": ["click", "scroll", "submit", "error"]
    },
    "timestamp": {
      "type": "integer",
      "minimum": 1000000000,
      "maximum": 9999999999
    },
    "data": {
      "type": "object",
      "properties": {
        "page_url": {
          "type": "string",
          "format": "uri"
        },
        "user_agent": {
          "type": "string",
          "minLength": 5,
          "maxLength": 1000
        },
        "custom_fields": {
          "type": "array",
          "maxItems": 10,
          "items": {
            "type": "object",
            "properties": {
              "key": {"type": "string"},
              "value": {"type": ["string", "number", "boolean"]}
            }
          }
        }
      }
    }
  }
}
```

## Validacion asimetrica: strict input, flexible output

**Pattern recomendado**:
- **Input** (request): validacion ESTRICTA (rechazar invalido)
- **Output** (response): flexible (enviar lo que Lambda genera)

Esto protege el backend pero no ahoga el cliente con validaciones.

En Lambda, si necesitas mas validacion sofisticada (ej. email ya registrado),
valida alli y devuelve 400 + detalle.

## Testing validacion

```bash
# Request valido
curl -X POST https://api.the-full-stack.com/contact \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","message":"This is a test message"}'
# Esperado: 200 OK (pasa a Lambda)

# Request sin email (requerido)
curl -X POST https://api.the-full-stack.com/contact \
  -H "Content-Type: application/json" \
  -d '{"message":"Missing email"}'
# Esperado: 400 Bad Request (validacion falla en API Gateway)

# Request con email invalido
curl -X POST https://api.the-full-stack.com/contact \
  -H "Content-Type: application/json" \
  -d '{"email":"not-an-email","message":"Invalid email"}'
# Esperado: 400 Bad Request (validacion falla)

# Request con body invalido JSON
curl -X POST https://api.the-full-stack.com/contact \
  -H "Content-Type: application/json" \
  -d '{invalid json}'
# Esperado: 400 Bad Request (parsing error)
```

## Monitoreo: validaciones fallidas

CloudWatch Metrics (builtin):
- `4XXError` — incluye validaciones fallidas
- `Latency` — debe ser bajo (<10ms para validacion)

Crear alarma:
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name api-validation-failures \
  --alarm-description "Alert if too many 400 errors" \
  --metric-name 4XXError \
  --namespace AWS/ApiGateway \
  --statistic Sum \
  --period 300 \
  --threshold 50 \
  --comparison-operator GreaterThanThreshold
```

Si 4XXError esta muy alta, posible ataque volumetrico de requests malformados.

## Gotchas

### Gotcha 1: JSON Schema draft 4 es viejo

Draft 4 es de 2013. Algunas features modernas faltan:
- No soporta `draft-06` features (ej. `$id`, `$schema` en properties)
- Regex es ECMA 262, no Perl (diferencias subtiles)
- No hay `$ref` externo (solo inline)

Pero para validacion basica es suficiente.

### Gotcha 2: Mensaje de error generico

API Gateway devuelve error generico ("Invalid request body"), no detalle.

Si necesitas error message detallado (ej. "email must be valid"), hacer
validacion adicional en Lambda:

```python
def lambda_handler(event, context):
    body = json.loads(event['body'])
    
    # Validacion adicional
    if not email_is_valid_business_domain(body['email']):
        return {
            'statusCode': 400,
            'body': json.dumps({
                'error': 'Email must be from a business domain'
            })
        }
    
    # ... procesar
```

### Gotcha 3: Content-Type requerido

API Gateway espera `Content-Type: application/json` para validar JSON body.

Si cliente envia otro Content-Type, la validacion NO se ejecuta.

Requerir explicitamente en method settings:
```yaml
RequestParameters:
  method.request.header.Content-Type: true
```

## Next steps

- [07-deployment-sam.md](./07-deployment-sam.md) — template SAM con validation
- [08-monitoring-logs.md](./08-monitoring-logs.md) — logs de validacion fallida
- [09-cost-throttling-strategy.md](./09-cost-throttling-strategy.md) — ahorro de costo

Verificado a fecha 2026-05-13.
