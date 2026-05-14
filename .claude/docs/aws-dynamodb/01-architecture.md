# Arquitectura DynamoDB: Modelo NoSQL Key-Value

> Conceptos fundamentales del modelo de datos de DynamoDB, enfocado en el diseño de las dos tablas del portfolio (contacts y tracking).

## Conceptos Base

### 1. Tabla

Contenedor principal de datos. En este portfolio:
- **contacts** — documentos de contacto del formulario
- **tracking** — eventos de pagina (page views)

Cada tabla es independiente, con su propio schema y capacidad.

### 2. Item (Registro)

Un documento dentro de una tabla. Equivalente a una fila en SQL pero con estructura flexible (cada item puede tener diferentes atributos).

Ejemplo de item en `contacts`:
```
{
  id: "01ARZ3NDEKTSV4RRFFQ69G5FAV",     # partition key
  email: "user@example.com",
  name: "Juan Pérez",
  message: "Interesado en fintech",
  created_at: "2026-05-13T14:30:00Z",
  service_type: "full-stack",
  company: "Acme Corp"
}
```

### 3. Atributo

Campo dentro de un item. DynamoDB soporta estos tipos:

| Tipo | Ejemplo | Caso de Uso |
|------|---------|-----------|
| **String (S)** | "Juan Pérez", "https://example.com" | Texto, URLs, emails |
| **Number (N)** | 42, 3.14, 1715604600 (Unix epoch) | Cantidades, timestamps, precios |
| **Binary (B)** | blob de bytes | Imagenes, archivos (raro) |
| **Boolean (BOOL)** | true, false | Flags |
| **List (L)** | ["tag1", "tag2"] | Arrays heterogeneos |
| **Map (M)** | { address: { city: "Madrid" } } | Objetos anidados |
| **String Set (SS)** | {"tag1", "tag2"} | Conjuntos de strings (raro) |
| **Number Set (NS)** | {1, 2, 3} | Conjuntos de numeros (raro) |
| **Null (NULL)** | null | Valor nulo |

### 4. Primary Key

Define cómo se accede únicamente a un item. Dos componentes:

#### Partition Key (Hash Key)

Obligatorio. Distribuye items entre particiones. Ejemplo:
- `contacts`: `id` (UUIDv7) → cada contacto tiene ID único
- `tracking`: `session_id` (UUIDv7) → agrupa eventos de una sesión

DynamoDB hashea la partition key para distribuir datos equitativamente.

#### Sort Key (Range Key)

Opcional. Ordena items dentro de una partición. Permite queries de rango.

Ejemplo en `tracking` (si se agrega):
```
Partition Key: session_id
Sort Key: created_at
Query: "Dame todos los eventos de session_id X entre tiempo A y B"
```

En `contacts`, NO hay sort key necesario (acceso por ID únicamente).

### 5. Atributos Importantes

Para este portfolio:

**contacts tabla:**
- `id` (String, PK) — UUIDv7, clave única
- `email` (String) — para deduplicacion anti-spam
- `name` (String) — nombre del contacto
- `message` (String) — cuerpo del mensaje (max 2000 chars)
- `service_type` (String) — enum: "generic", "fintech", "architect", "leader", "vibe"
- `company` (String) — empresa del contacto (opcional)
- `role` (String) — cargo (opcional)
- `budget` (Number) — presupuesto indicativo en USD (opcional)
- `timeline` (String) — "urgent", "1-3 months", "6+ months"
- `source_url` (String) — URL del referrer (HTTP referer)
- `ip_address` (String) — IP del cliente (CF-Connecting-IP)
- `country` (String) — país (CF-IPCountry de Cloudflare)
- `user_agent` (String) — navegador user agent
- `created_at` (Number) — Unix epoch segundos

**tracking tabla:**
- `session_id` (String, PK) — UUIDv7, identifica sesión de usuario
- `page_id` (String, SK) — UUIDv7, para ordenar eventos
- `url` (String) — URL visitada
- `referrer` (String) — HTTP referer
- `utm_source`, `utm_medium`, `utm_campaign`, `utm_term`, `utm_content` (String) — query params
- `screen_resolution` (String) — "1920x1080"
- `viewport` (String) — "desktop", "tablet", "mobile"
- `lang` (String) — codigo idioma (es, en)
- `timezone` (String) — "America/Santiago"
- `user_agent` (String) — navegador
- `ip_address` (String) — IP del cliente
- `country` (String) — país de Cloudflare
- `created_at` (Number) — Unix epoch segundos
- `expires_at` (Number) — Unix epoch segundos + 60 dias (para TTL)

## Comparativa SQL vs DynamoDB

| Concepto | SQL | DynamoDB |
|----------|-----|----------|
| **Tabla** | Tabla | Tabla |
| **Fila** | Row | Item |
| **Columna** | Column | Attribute |
| **Clave Primaria** | PRIMARY KEY (col1, col2) | Partition Key + Sort Key |
| **Índice** | CREATE INDEX | Global Secondary Index (GSI) |
| **Query** | SELECT * WHERE pk = ? | Query (partition key requerido) |
| **Busqueda Completa** | SELECT * | Scan (EVITAR, costoso) |
| **Transaccion** | BEGIN; ... COMMIT; | TransactWriteItems (multi-item) |
| **Joins** | JOIN tabla2 | NO SOPORTADO (denormalizar) |

## Reglas de Diseño para Este Portfolio

1. **Partition Key por dominio:** `id` en contacts, `session_id` en tracking → distribuye bien
2. **Sort Key en tracking:** `page_id` permite ordenar eventos cronologicamente
3. **Atributos opcionales:** Map o null si no siempre presente (ej: `company`)
4. **Strings para IDs:** UUIDv7 como string (no Number) → sorteable, legible
5. **Numeros para fechas:** Unix epoch seconds (Number) → comparable, ordenable
6. **Sin denormalizacion aun:** Ambas tablas son simples, relaciones laterales no necesarias

## Paso Siguiente

- Decidir capacidad: leer [02-capacity-modes.md](02-capacity-modes.md)
- Empezar a codificar: leer [06-boto3-python.md](06-boto3-python.md)
