# Usage Plans y API Keys

> Cuando usar usage plans. Para este portfolio (form publico), no necesitas
> API keys. Pero si creces a clientes B2B, aqui esta el pattern.

[← Rate-limit per-IP](./03-rate-limit-per-ip.md) | [README](./README.md) | [Siguiente: CORS security →](./05-cors-security.md)

## Cuando NO necesitas usage plans (caso actual)

Este portfolio es:
- Form contacto **publico** (sin autenticacion)
- Sin clientes B2B
- Rate-limit global via API Gateway + per-IP via WAF

**Decision**: NO usar usage plans ni API keys en frontend.

Ventajas:
- Menos complejidad (no necesitas distribuir API keys)
- Mejor UX (cliente no ingresa key)
- Mismo nivel de proteccion (WAF + API GW)

## Cuando SI necesitas usage plans (futuro B2B)

Si en el futuro tienes:
- Clientes B2B con tiers distintos (Starter, Pro, Enterprise)
- Cuotas mensuales distintas por cliente
- Metering (cobro por uso)

Entonces:
1. Crear API key para cada cliente
2. Crear usage plan con throttle/quota
3. Asociar API key a usage plan
4. Cliente pasa key via header `x-api-key`
5. API Gateway verifica key y aplica limites

## Patron: Usage plan con throttle + quota

```yaml
# CloudFormation / SAM
Resources:
  # API key para "Cliente A"
  ClientAApiKey:
    Type: AWS::ApiGateway::ApiKey
    Properties:
      Name: client-a-key
      Description: "API key for Client A (Starter plan)"
      Enabled: true
      StageKeys:
        - RestApiId: !Ref PortfolioApi
          StageName: prod

  # Usage plan: Starter (cuota baja)
  StarterPlan:
    Type: AWS::ApiGateway::UsagePlan
    DependsOn: PortfolioApiProdStage
    Properties:
      PlanName: starter-plan
      Description: "Starter tier: 1K req/month, 10 req/s"
      ApiStages:
        - ApiId: !Ref PortfolioApi
          Stage: prod
      Quota:
        Limit: 1000
        Period: MONTH
      Throttle:
        RateLimit: 10
        BurstLimit: 20

  # Asociar API key a usage plan
  ClientAUsagePlanKey:
    Type: AWS::ApiGateway::UsagePlanKey
    Properties:
      KeyId: !Ref ClientAApiKey
      KeyType: API_KEY
      UsagePlanId: !Ref StarterPlan

  # Otra API key para "Cliente B"
  ClientBApiKey:
    Type: AWS::ApiGateway::ApiKey
    Properties:
      Name: client-b-key
      Description: "API key for Client B (Pro plan)"
      Enabled: true

  # Usage plan: Pro (cuota alta)
  ProPlan:
    Type: AWS::ApiGateway::UsagePlan
    DependsOn: PortfolioApiProdStage
    Properties:
      PlanName: pro-plan
      Description: "Pro tier: 100K req/month, 100 req/s"
      ApiStages:
        - ApiId: !Ref PortfolioApi
          Stage: prod
      Quota:
        Limit: 100000
        Period: MONTH
      Throttle:
        RateLimit: 100
        BurstLimit: 200

  ClientBUsagePlanKey:
    Type: AWS::ApiGateway::UsagePlanKey
    Properties:
      KeyId: !Ref ClientBApiKey
      KeyType: API_KEY
      UsagePlanId: !Ref ProPlan
```

## Cliente usa la API key

Cliente recibe API key via email: `sk_live_abc123xyz`

Request:
```bash
curl -X POST https://api.the-full-stack.com/contact \
  -H "x-api-key: sk_live_abc123xyz" \
  -H "Content-Type: application/json" \
  -d '{"email":"client@example.com","message":"..."}'
```

API Gateway verifica:
1. x-api-key existe y es valida
2. Key esta asociada a un usage plan
3. Cliente no ha excedido quota mensual
4. Cliente no ha excedido throttle por segundo

Si todo OK: 200. Si falla: 429 o 403.

## Rotacion de API keys

Las keys se rotan periodicamente por seguridad:

```bash
# Crear key nueva
aws apigateway create-api-key \
  --name client-a-key-v2 \
  --enabled \
  --region us-east-1

# Asociar a usage plan (nueva key)
aws apigateway create-usage-plan-key \
  --usage-plan-id <plan-id> \
  --key-id <new-key-id> \
  --key-type API_KEY

# Desactivar key vieja (despues de transicion)
aws apigateway update-api-key \
  --api-key <old-key-id> \
  --patch-operations op=replace,path=/enabled,value=false
```

Timeline:
1. Crear key nueva
2. Comunicar a cliente (ej. via email)
3. Cliente prueba con key nueva (1-2 semanas)
4. Deshabilitar key vieja
5. Borrar key vieja (30 dias despues)

## Metering: cobro por uso

Si necesitas cobro variable por API calls:

```yaml
UsagePlan:
  Type: AWS::ApiGateway::UsagePlan
  Properties:
    PlanName: metered-plan
    ApiStages:
      - ApiId: !Ref PortfolioApi
        Stage: prod
    Quota:
      Limit: null  # Sin cuota fija
      Period: null
    Throttle:
      RateLimit: 100
      BurstLimit: 200
```

Luego, en backend:
1. Lambda registra cada request en DynamoDB con usuario + timestamp
2. Batch job diario calcula uso por cliente
3. Integrar con billing system (Stripe, AWS Marketplace, etc.)

Este portfolio no lo necesita hoy.

## Seguridad: API keys en el cliente

**IMPORTANTE**: nunca incluyas API keys en repositorio publico.

Malas practicas:
- Hardcodear key en JavaScript
- Commitear key en git
- Exponer key en HTML

Buenas practicas:
- Guardar key en `.env.local` (no committeado)
- En produccion, obtener key via backend auth (ej. Cognito)
- Rotar keys monthly
- Usar key scoping (restriccion a rutas especificas)

Para este portfolio (form publico sin cliente B2B):
- No necesitas keys en cliente
- WAF + API GW throttle es suficiente

## Comparacion: Sin API keys vs Con API keys

| Aspecto | Sin API keys | Con API keys |
|---------|-------------|--------------|
| **Complexity** | Baja | Alta (distribucion, rotacion) |
| **Client auth** | No | Si (header x-api-key) |
| **Rate-limit** | API GW + WAF (global + per-IP) | API GW per-client |
| **Quota** | Usa API GW stage quota | Per-client quota |
| **Security** | Relatos en IP + WAF | Relatos en key + HMAC |
| **Cost** | Bajo | Bajo (keys son free) |
| **Ideal para** | Formularios publicos | APIs B2B, partners |

## Next steps

- [05-cors-security.md](./05-cors-security.md) — CORS configuration
- [07-deployment-sam.md](./07-deployment-sam.md) — template SAM completo
- [09-cost-throttling-strategy.md](./09-cost-throttling-strategy.md) — pricing estimado

Verificado a fecha 2026-05-13.
