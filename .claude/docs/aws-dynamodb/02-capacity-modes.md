# Capacity Modes: On-Demand vs Provisioned

> Decision crítica: qué modelo de facturación usar. Para este portfolio: **On-Demand es OBLIGATORIO**.

## On-Demand (PAY_PER_REQUEST)

Pagas solo por lo que usas. Ideal para **workloads impredecibles o esporádicos**.

### Pricing us-west-2 (Mayo 2026)

- **Write:** $1.25 por 1 millón de Write Request Units (WRU)
- **Read:** $0.25 por 1 millón de Read Request Units (RRU)
- **Storage:** $0.25 por GB/mes
- **PITR (point-in-time recovery):** $0.20 por GB/mes (opcional)
- **Backup (on-demand):** $0.10 por GB

### Request Units (RU)

- **1 WRU** = escribir 1 KB (redondeo hacia arriba por KB)
- **1 RRU** = leer 4 KB fuertemente consistente OU 8 KB eventualmente consistente

### Estimacion para Este Portfolio

**Tabla `contacts` (200 items/mes):**
- Writes: 200 items × ~1.5 KB = 300 WRU/mes
- Reads: ~100 queries (listar por fecha, búsqueda por email) × 0.1 KB = 10 RRU/mes
- Storage: 200 items × 1.5 KB = 0.3 MB = negligible
- **Costo mensual:** ~$0.0004 (menos de un centavo)

**Tabla `tracking` (15000 items/mes):**
- Writes: 15000 items × 0.3 KB = 4500 WRU/mes
- Reads: 5000 queries × 0.1 KB = 500 RRU/mes
- Storage (sin TTL): 15000 × 0.3 KB = 4.5 MB, pero TTL borra en 48h → ~0.5 GB media
- **Costo mensual:** $1.25 × (4500/1M) + $0.25 × (500/1M) + $0.25 × 0.5 = **~$0.006 /mes** (media centavo)

**Total:** <$0.01/mes 🎉

## Provisioned (Capacity Units)

Reservas capacidad de antemano. Más barato si sabes exactamente cuanta necesitas, pero pagas aunque no uses.

### Pricing us-west-2 (Mayo 2026)

- **WCU:** $0.97 por WCU/mes (25 WCU gratuitos)
- **RCU:** $0.19 por RCU/mes (25 RCU gratuitos)
- **Storage:** $0.25 por GB/mes (igual que On-Demand)
- **Auto-scaling:** Sin costo adicional si habilitado

### Estimacion para Este Portfolio

Si usaras Provisioned:
- Minimo: 1 WCU + 1 RCU = ~$1.16/mes (ya supera On-Demand)
- Con auto-scaling: riesgo de sobrecapacidad (dinero muerto)

## Comparativa

| Aspecto | On-Demand | Provisioned |
|--------|-----------|------------|
| **Modelo** | Pay-per-request | Reserva capacidad |
| **Precio** | $1.25/M writes, $0.25/M reads | $0.97/WCU/mes, $0.19/RCU/mes |
| **Mejor para** | Impredecible, sporádico | Previsible, sostenido |
| **Min costo/mes** | ~$0 (si <2500 writes/mes) | ~$1.16 (25 WCU + 25 RCU) |
| **Escalabilidad** | Automática (ilimitada) | Manual o auto-scaling |
| **Latencia p99** | Variable bajo carga | Garantizada (throttling si sobrepasas) |
| **Free Tier** | 25 GB storage (limitado en requests) | 25 WCU + 25 RCU /mes |

## Free Tier 2026

AWS Free Tier para DynamoDB:
- **Siempre gratis (no 12 meses):**
  - 25 GB de storage
  - 25 WCU + 25 RCU (Provisioned mode, aprox 200M requests/mes)
  - 2.5M DynamoDB Streams reads
- **On-Demand:** No hay free tier para requests, solo storage

Para este portfolio, el free tier de Provisioned (25 WCU + 25 RCU) cubre 100x lo que necesitas. Pero On-Demand sigue siendo más barato a largo plazo si creces.

## Decision: ON-DEMAND ES OBLIGATORIO

**Razon:**

1. Volumen bajo + impredecible (contactos esporádicos, tracking variable)
2. Costo absoluto: <$0.01/mes vs mínimo $1.16/mes en Provisioned
3. Escalabilidad automática sin gestión
4. Sin riesgo de throttling
5. AWS November 2024 redujo on-demand pricing 50% → recomendación oficial es On-Demand por default

## Implementacion en SAM

En `template.yaml`:

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2013-12-31

Resources:
  ContactsTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: contacts
      BillingMode: PAY_PER_REQUEST      # On-Demand
      AttributeDefinitions:
        - AttributeName: id
          AttributeType: S
      KeySchema:
        - AttributeName: id
            KeyType: HASH               # Partition Key

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
          KeyType: RANGE              # Sort Key
      TimeToLiveSpecification:
        AttributeName: expires_at
        Enabled: true
```

## Paso Siguiente

- Codificar con boto3: [06-boto3-python.md](06-boto3-python.md)
- Implementar en SAM: [07-deployment-sam.md](07-deployment-sam.md)
