# Rate-limiting per-IP con AWS WAF

> API Gateway nativo NO soporta rate-limit por IP. Solucion: AWS WAF
> rate-based rule. Combinacion: WAF (per-IP) + API Gateway (global).

[← Throttling fundamentals](./02-throttling-fundamentals.md) | [README](./README.md) | [Siguiente: Usage plans →](./04-usage-plans-api-keys.md)

## Problema: API Gateway no limita por IP

API Gateway throttling aplica a **TODOS los requests** sumados.
No hay forma nativa de limitar por IP de origen.

Ejemplo fallido:
- Configuras: 3 req/s per-method throttle en POST /contact
- Significado: 3 req/s TOTAL de TODAS las IPs, no 3 req/s por IP
- Escenario: 1 atacante de 1 IP puede quemar todo el budget

**Solucion**: AWS WAF con rate-based rule.

## AWS WAF rate-based rule (CRITICO)

AWS WAF es un Web Application Firewall que puede bloquear IPs por volumetria.

### Limites WAF (importantes)

- **Minimo rate**: 10 requests en ventana de 5 minutos (cambio May 2025)
- **Maximo IPs trackeadas**: 10,000 IPs simultaneas
- **Agregacion**: por IP origen (primera IPv4/IPv6 en X-Forwarded-For)
- **Accion**: Block, Count, Challenge, CAPTCHA

### Configuracion para este portfolio

| Endpoint | Limite WAF | Ventana | Logica |
|----------|-----------|---------|--------|
| `/contact` | 3 req/5min per IP | 5 min | Estricto: max 3 requests en 5 minutos |
| `/track` | 30 req/5min per IP | 5 min | Permisivo: telemetria de tracking pixel |
| `/validate-turnstile` | 30 req/5min per IP | 5 min | Validacion interna, mismo que /track |

WAF cuenta **dentro de la ventana de 5 min**. Luego resetea.

Ejemplo: IP 192.0.2.1
- t=0s: request 1 → contador=1 (OK)
- t=10s: request 2 → contador=2 (OK)
- t=20s: request 3 → contador=3 (OK)
- t=30s: request 4 → BLOCKED (contador excedio 3)
- t=300s: contador resetea a 0

## Configuracion SAM + CloudFormation

WAF se crea separado de API Gateway y se *assocan* via ARN.

### 1. Crear Web ACL + rate-based rules (SAM)

Archivo `sam.yaml` con recursos WAF:

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Description: Portfolio API con WAF rate-limiting per-IP

Parameters:
  Environment:
    Type: String
    Default: prod
    AllowedValues: [dev, prod]

Resources:
  # ===== API Gateway =====
  PortfolioApi:
    Type: AWS::Serverless::Api
    Properties:
      StageName: !Ref Environment
      Name: portfolio-api
      TracingEnabled: true
      MethodSettings:
        - ResourcePath: /contact
          HttpMethod: POST
          ThrottleSettings:
            RateLimit: 3
            BurstLimit: 5
        - ResourcePath: /track
          HttpMethod: POST
          ThrottleSettings:
            RateLimit: 30
            BurstLimit: 60

  # ===== WAF Web ACL =====
  PortfolioWebAcl:
    Type: AWS::WAFv2::WebACL
    Properties:
      Name: portfolio-waf-acl
      Scope: REGIONAL
      DefaultAction:
        Allow: {}
      Rules:
        # Rate-based rule para /contact (estricto)
        - Name: RateLimitContactEndpoint
          Priority: 0
          Statement:
            RateBasedStatement:
              Limit: 3
              AggregateKeyType: IP
              ScopeDownStatement:
                ByteMatchStatement:
                  SearchString: /contact
                  FieldToMatch:
                    UriPath: {}
                  TextTransformation:
                    - NONE
                  PositionalConstraint: CONTAINS
          Action:
            Block:
              CustomResponse:
                ResponseCode: 429
                CustomResponseBodyKey: RateLimitedResponse
          VisibilityConfig:
            SampledRequestsEnabled: true
            CloudWatchMetricsEnabled: true
            MetricName: ContactRateLimitMetric
        
        # Rate-based rule para /track (permisivo)
        - Name: RateLimitTrackEndpoint
          Priority: 1
          Statement:
            RateBasedStatement:
              Limit: 30
              AggregateKeyType: IP
              ScopeDownStatement:
                ByteMatchStatement:
                  SearchString: /track
                  FieldToMatch:
                    UriPath: {}
                  TextTransformation:
                    - NONE
                  PositionalConstraint: CONTAINS
          Action:
            Block:
              CustomResponse:
                ResponseCode: 429
                CustomResponseBodyKey: RateLimitedResponse
          VisibilityConfig:
            SampledRequestsEnabled: true
            CloudWatchMetricsEnabled: true
            MetricName: TrackRateLimitMetric
      
      CustomResponseBodies:
        RateLimitedResponse:
          Content: '{"message":"Too Many Requests","code":"RATE_LIMIT_EXCEEDED"}'
          ContentType: APPLICATION_JSON
      
      VisibilityConfig:
        SampledRequestsEnabled: true
        CloudWatchMetricsEnabled: true
        MetricName: PortfolioWafMetric

  # Asociar WAF a API Gateway
  WafApiAssociation:
    Type: AWS::WAFv2::WebACLAssociation
    Properties:
      ResourceArn: !Sub arn:aws:apigateway:${AWS::Region}::/restapis/${PortfolioApi}/stages/${Environment}
      WebACLArn: !GetAtt PortfolioWebAcl.Arn

  # ===== Lambda functions =====
  ContactFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: portfolio-contact
      Runtime: python3.13
      Handler: functions/contact.handler
      CodeUri: functions/
      Events:
        ContactApi:
          Type: Api
          Properties:
            RestApiId: !Ref PortfolioApi
            Path: /contact
            Method: POST

  TrackFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: portfolio-track
      Runtime: python3.13
      Handler: functions/track.handler
      CodeUri: functions/
      Events:
        TrackApi:
          Type: Api
          Properties:
            RestApiId: !Ref PortfolioApi
            Path: /track
            Method: POST

Outputs:
  ApiEndpoint:
    Description: API Gateway endpoint URL
    Value: !Sub https://${PortfolioApi}.execute-api.${AWS::Region}.amazonaws.com/${Environment}
  
  WebAclArn:
    Description: WAF Web ACL ARN
    Value: !GetAtt PortfolioWebAcl.Arn
```

### 2. Desplegar

```bash
sam build
sam deploy --guided

# Verificar WAF creado
aws wafv2 list-web-acls --scope REGIONAL --region us-west-2
```

## Comportamiento detallado de la rate-based rule

Cuando una IP supera el limite:

1. **Evaluacion**: WAF cuenta requests de esa IP en ventana de 5 min
2. **Decision**: Si count > limit, aplica el action (Block, Count, Challenge)
3. **Custom response**: Devuelve HTTP 429 con body JSON
4. **Metricas**: CloudWatch registra en `ContactRateLimitMetric`, `TrackRateLimitMetric`
5. **Logging**: WAF logs en S3 (opcional, configurable)

La regla resetea cada 5 minutos para cada IP.

## IP detection (importante en reverse proxy)

Cuando el cliente viene detras de un proxy (CDN, LB), WAF necesita saber
la IP real del cliente, no la del proxy.

**Configuracion**: WAF busca en **X-Forwarded-For header** automaticamente.

```
Request llega a WAF:
  Header: X-Forwarded-For: 203.0.113.42, 198.51.100.1
  WAF extrae: 203.0.113.42 (primer IP) ← esta es la que conta
```

En este portfolio, los requests vienen desde:
1. **Browser del cliente** → **Cloudflare Pages** (CDN) → **API Gateway**
2. Cloudflare agrega X-Forwarded-For header automaticamente
3. WAF lo respeta

Si necesitas asegurar que X-Forwarded-For es de confianza, agregar
scope-down statement que valide el proxy conocido:

```yaml
# Solo contar requests que vienen de Cloudflare
ScopeDownStatement:
  IPSetReferenceStatement:
    Arn: arn:aws:wafv2:us-west-2:ACCOUNT:regional/ipset/cloudflare-ips/...
```

(Obtener IPs de Cloudflare desde https://www.cloudflare.com/ips/)

## Listar IPs siendo rate-limited

Comando para ver que IPs estan siendo bloqueadas ahora:

```bash
aws wafv2 list-ip-sets \
  --scope REGIONAL \
  --region us-west-2 \
  --query 'IPSets[?Name==`portfolio-waf-acl`]' \
  --output table

# Obtener estadisticas de rate-limiting en CloudWatch
aws cloudwatch get-metric-statistics \
  --namespace AWS/WAFV2 \
  --metric-name BlockedRequests \
  --dimensions Name=Rule,Value=RateLimitContactEndpoint \
  --start-time 2026-05-13T00:00:00Z \
  --end-time 2026-05-14T00:00:00Z \
  --period 300 \
  --statistics Sum
```

## Monitoreo en CloudWatch

WAF publica metricas automaticamente:

| Metrica | Significa |
|---------|----------|
| `AllowedRequests` | Requests permitidos (no matched la rule) |
| `BlockedRequests` | Requests bloqueados por WAF |
| `CountedRequests` | Requests contados pero no bloqueados (action=Count) |
| `SampledRequests` | Muestra de requests para log |

Crear dashboard:
```bash
aws cloudwatch put-dashboard \
  --dashboard-name portfolio-waf-dashboard \
  --dashboard-body file://dashboard.json
```

Contenido `dashboard.json`:
```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/WAFV2", "AllowedRequests", {"stat": "Sum"}],
          [".", "BlockedRequests", {"stat": "Sum"}],
          [".", "CountedRequests", {"stat": "Sum"}]
        ],
        "period": 300,
        "stat": "Sum",
        "region": "us-west-2",
        "title": "WAF Traffic"
      }
    }
  ]
}
```

## Testing la rate-based rule

Simular ataque volumetrico:

```bash
#!/bin/bash
API_URL="https://api.the-full-stack.com/contact"

# Enviar 5 requests rapido
for i in {1..5}; do
  curl -X POST "$API_URL" \
    -H "Content-Type: application/json" \
    -d '{"email":"test@example.com","message":"Test"}' \
    -w "Status: %{http_code}\n"
  sleep 0.5
done

# Esperado: primeros 3 = 200, 4 y 5 = 429
```

## Diferencia: WAF vs API Gateway throttling

| Aspecto | API Gateway | WAF |
|---------|------------|-----|
| Scope | Global (all IPs sumadas) | Per-IP |
| Ventana | Token bucket dinamico | 5 minutos fija |
| Minimo | 1 req/s | 10 req/5min = 0.033 req/s |
| Latency | ~5ms | ~10ms (WAF adicional) |
| Cost | Incluido | $1/rule/mes + $0.60/M requests |
| Action | 429 generico | Custom 429 + custom response body |

**Uso combinado (recomendado)**:
- **WAF**: primera linea, per-IP, volumetria masiva
- **API GW**: segunda linea, global, protege account-level limits

## Gotchas

### Gotcha 1: Limite minimo de 10 req/5min en WAF

No puedes configurar un limite menor. Si necesitas 1 req/5min, usar Lambda
authorizer customizado (mas caro, mas complejo).

### Gotcha 2: Contadores resetean cada 5 min

No es posible resetear con frecuencia menor. Si necesitas throttle por minuto,
usar API Gateway step functions o Lambda con DynamoDB TTL.

### Gotcha 3: 10K IPs max trackeadas

Si >10K IPs exceeden el limite simultaneamente, WAF bloquea las con rates
mas altas. Las menos agresivas pueden pasar. En volumetria masiva DDoS,
esto es aceptable (mejor que nada).

## Next steps

- [04-usage-plans-api-keys.md](./04-usage-plans-api-keys.md) — si necesitas quotas por cliente
- [07-deployment-sam.md](./07-deployment-sam.md) — template SAM completo
- [08-monitoring-logs.md](./08-monitoring-logs.md) — metricas y alarmas

Verificado a fecha 2026-05-13.
