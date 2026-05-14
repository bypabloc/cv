# AWS DynamoDB para el Portfolio (Contactos + Tracking)

> Knowledge base modular para DynamoDB en el portfolio: dos tablas (contacts, tracking), Lambda Python 3.13, IaC con AWS SAM. Capacidad On-Demand (pay-per-request), TTL para tracking.

## Contexto

El portfolio de Pablo Contreras (Astro 6 monorepo pnpm) integra dos tablas DynamoDB en us-west-2:

1. **`contacts`** — Almacena envios del formulario de contacto (50-200 items/mes)
2. **`tracking`** — Almacena page views (5000-15000 items/mes con TTL 60 dias)

Backend: Lambda Python 3.13 + boto3. IaC: AWS SAM.

## Tabla de Contenidos

| Capitulo | Tema | Cuando leer |
|----------|------|-------------|
| [01-architecture.md](01-architecture.md) | Modelo NoSQL key-value, tablas, PK/SK, items, atributos | Antes de diseñar schema |
| [02-capacity-modes.md](02-capacity-modes.md) | On-Demand vs Provisioned, pricing us-west-2 | Para decidir modelo de facturacion |
| [03-single-table-design.md](03-single-table-design.md) | Single-table pattern (Rick Houlihan), cuándo aplica | Para arquitectura avanzada (opcional) |
| [04-ttl-tracking.md](04-ttl-tracking.md) | Time To Live, configuracion, costos | Para tabla `tracking` con retencion limitada |
| [05-gsi-patterns.md](05-gsi-patterns.md) | Global Secondary Index, sparse indexes, costos | Para queries que no usan partition key |
| [06-boto3-python.md](06-boto3-python.md) | boto3 API, put_item/get_item/query, Decimal | Antes de escribir Lambda handlers |
| [07-deployment-sam.md](07-deployment-sam.md) | SAM template completo, recursos, permisos | Para IaC infrastructure as code |
| [08-cost-optimization.md](08-cost-optimization.md) | Pricing breakdown, estimaciones, free tier | Para presupuesto y seguimiento |
| [09-security-best-practices.md](09-security-best-practices.md) | IAM least privilege, encryption, VPC endpoints | Antes de produccion |
| [CHANGELOG.md](CHANGELOG.md) | Historial de cambios y decisiones | Referencia de arqueologia |

## Reglas Criticas

- SIEMPRE usar **On-Demand** (BillingMode: PAY_PER_REQUEST en SAM) — es más barato para este volumen
- NUNCA hardcodear table names — usar variables de entorno + SAM `!Ref`
- SIEMPRE especificar **TTL** en `tracking` (AttributeName: expires_at, Enabled: true)
- SIEMPRE usar **Decimal** en boto3 para dinero (no float)
- NUNCA crear GSI sin justificación (GSI cuesta 2x write cost)
- SIEMPRE aplicar IAM **least privilege** per Lambda function per table
- NUNCA usar `scan()` en tablas grandes sin **Projection** limitada

## Navegacion

- Guia rapida: leer `02-capacity-modes.md` → `06-boto3-python.md` → `07-deployment-sam.md`
- Arquitectura: leer `01-architecture.md` → `03-single-table-design.md`
- Produccion: leer `08-cost-optimization.md` → `09-security-best-practices.md`

## Datos de Referencia

- **Region:** us-west-2 (Oregon)
- **Modo:** On-Demand (PAY_PER_REQUEST)
- **Pricing (Mayo 2026):** Writes $1.25/M RU, Reads $0.25/M RU, Storage $0.25/GB-month
- **Free Tier:** 25GB storage + 25 WCU + 25 RCU (provisioned) O 200M requests/month (on-demand)
- **TTL:** Sin costo adicional, borra dentro de 48h post-expiracion
- **Verificado:** 2026-05-13

## Fuentes

- [AWS DynamoDB Developer Guide](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/)
- [boto3 DynamoDB Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/dynamodb.html)
- [AWS SAM Developer Guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/)
