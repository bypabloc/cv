# Global Secondary Index (GSI) - Cuándo Usarlos

> GSI permite queries que no usan la partition key. Costo: 2x write amplification. PARA ESTE PORTFOLIO: NO GSI requerido (aun).

## ¿Qué es un GSI?

Índice separado en DynamoDB que permite queries con una partition key diferente a la tabla base.

**Tabla base (contacts):**
- PK: `id` (UUIDv7)
- Query: get_item(id) ✅
- Query: find by email? ❌ (no index)

**GSI sobre contacts:**
- PK: `email` (String)
- Query: find by email ✅
- Pero escrito automáticamente en paralelo con tabla base

## Costos de GSI

Escribir item en tabla base = escribir en TODAS las GSI también.

### Ejemplo: 5 GSI

```
Tabla contacts + 4 GSI (email, company, date_range, ip_address)

write_item(id=X, email=Y, company=Z) 
  → 1 write a tabla base
  → 1 write a GSI(email)
  → 1 write a GSI(company)
  → 1 write a GSI(date_range)
  → 1 write a GSI(ip_address)
  = 5 writes totales!

Costo: 5x vs sin GSI
```

**Free tier:** 25 WCU significan 25 WCU totales (tabla + índices). Con 5 GSI, cada write consume 5 WCU → solo 5 items/segundo. SIN GSI: 25 items/segundo.

## Para Este Portfolio: ¿GSI?

### Tabla `contacts`

Queries actuales:
- `get_item(id=X)` → USA partition key ✅
- `list by date range` → Agregar SORT key? (NO POR AHORA)
- `find duplicates by email` → Query? (Raramente, anti-spam offline)

**Veredicto:** 0 GSI necesarios hoy. La busqueda de duplicados puede ser app-logic (scan lento, OK para admin).

### Tabla `tracking`

Queries actuales:
- `query(session_id=X)` → USA partition key ✅
- `get all events from session X` → Sort key `page_id` (YA EXISTE en design)
- `find events by URL` → NO requerido

**Veredicto:** 0 GSI necesarios. Sort key `page_id` cubre los casos.

## Cuando Agregar GSI (Futuro)

Si el portfolio evoluciona a un **dashboard de analytics:**

- "Dame todos los contactos de dominio X" → GSI(company)
- "Dame todos los eventos de usuario IP Y" → GSI(ip_address)
- "Dame contactos por fecha de creacion" → GSI(created_at)

**Decision:** Agregar GSI SOLO cuando la query sea frecuente (>100 queries/dia).

## Sparse GSI (Optimizacion)

GSI que solo indexa items con cierto atributo (ahorra writes).

```yaml
# GSI para "premium contacts" (solo si company != null)
ContactsByCompanyGSI:
  Type: AWS::DynamoDB::GlobalSecondaryIndex
  Properties:
    IndexName: company-index
    KeySchema:
      - AttributeName: company
        KeyType: HASH
    Projection:
      ProjectionType: KEYS_ONLY  # Solo PK de tabla base
    BillingMode: PAY_PER_REQUEST
```

Cuando escribes item SIN `company`, DynamoDB no escribe en el GSI → saves cost.

## Projection (KEYS_ONLY vs ALL)

Si creas GSI, decide qué atributos copiar:

| Tipo | Atributos | Caso |
|------|-----------|------|
| **KEYS_ONLY** | PK + SK de tabla base + PK del GSI | Queries que solo necesitan IDs, luego fetch full item |
| **ALL** | Todos los atributos | Queries que necesitan datos completos |
| **INCLUDE** | Especificar cuáles | Balance: proyectar algunos atributos |

**Recomendacion:** KEYS_ONLY (ahorra storage, reduce writes para copia).

## Decision Log

- **2026-05-13:** Evaluacion de GSI completada
- **Tabla contacts:** 0 GSI (tabla pequeña, queries simples)
- **Tabla tracking:** 0 GSI (partition key + sort key cubren casos)
- **Futuro:** Revisar si dashboard requiere GSI en Q3 2026

## Paso Siguiente

- Seguridad con Least Privilege: [09-security-best-practices.md](09-security-best-practices.md)
- Deploy: [07-deployment-sam.md](07-deployment-sam.md)
