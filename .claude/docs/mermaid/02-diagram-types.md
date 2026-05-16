# Tipos de Diagramas — Ejemplos del Proyecto

<- [01-syntax-reference](01-syntax-reference.md) | [README](README.md) | [03-best-practices](03-best-practices.md) ->

---

## erDiagram para modelos de datos

### Convencion de mapeo de tipos -> Mermaid

Aplica tanto a tablas SQL de Neon PostgreSQL como a content collections Zod
del portfolio. Mermaid `erDiagram` no tiene tipo JSON: representar como string.

| Tipo origen (SQL / Zod) | Tipo Mermaid | Notas |
| --- | --- | --- |
| `uuid` / UUIDv7 | `string id PK` | El backend usa UUIDv7 nativo de PG18 |
| FK a otra tabla | `string <tabla>_id FK` | Solo el campo FK, no la relacion |
| `text` / `varchar` / `z.string()` | `string` | |
| `integer` / `bigint` / `z.number().int()` | `int` | |
| `numeric` / `real` / `z.number()` | `float` | |
| `boolean` / `z.boolean()` | `boolean` | |
| `timestamptz` / `z.date()` | `datetime` | |
| `jsonb` / `z.object()` | `string` | Representar como string, no hay tipo JSON |
| email (string + regex) | `string` | |

### Ejemplo: modelos principales

```
erDiagram
    USER ||--o{ PRODUCT : "owns"
    PRODUCT ||--o{ ORDER : "has"
    ORDER }o--|| CATEGORY : "belongs_to"
    ORDER ||--o{ ORDER_ITEM : "contains"
    ORDER_ITEM }o--o{ COLLECTION : "belongs_to"

    USER {
        string   id          PK  "UUIDv7"
        string   username    UK
        string   email       UK
        boolean  is_active
        datetime date_joined
    }

    PRODUCT {
        string   id          PK  "UUIDv7"
        string   user_id     FK
        string   name
        string   description
        boolean  is_active
        datetime created_at
        datetime updated_at
    }

    CATEGORY {
        string  id      PK
        string  name    UK
        boolean active
    }

    ORDER {
        string   id             PK  "UUIDv7"
        string   product_id    FK
        string   category_id    FK
        string   status             "pending|processing|done|failed"
        float    total
        string   config             "JSONField"
        datetime started_at
        datetime completed_at
    }

    ORDER_ITEM {
        string   id         PK  "UUIDv7"
        string   order_id   FK
        string   s3_key
        int      quantity
        float    price
        datetime created_at
    }

    COLLECTION {
        string   id         PK  "UUIDv7"
        string   user_id    FK
        string   name
        datetime created_at
    }
```

### Ejemplo: catalogo con scopes

```
erDiagram
    CATEGORY ||--o{ ORDER : "used_in"
    TAG ||--o{ ORDER : "used_in"

    CATEGORY {
        string  id          PK
        string  name        UK
        string  scope           "SYSTEM|USER|CUSTOM"
        string  owner_id    FK  "null si SYSTEM"
        string  description
        string  style_tags      "JSONField: array"
    }

    TAG {
        string  id          PK
        string  name        UK
        string  scope
        string  owner_id    FK
        string  description
    }
```

---

## flowchart para pipelines de procesamiento

### Pipeline de procesamiento de items

```
flowchart TD
    inicio([Usuario invoca accion]) --> define[Definir item\nnombre, atributos]
    define --> config[Configurar\ncon template]
    config --> proveedor{Elegir proveedor}

    proveedor -->|Provider A| provider_a[Procesar\ncon Provider A]
    proveedor -->|Provider B| provider_b[Procesar\ncon Provider B]

    provider_a --> result[Resultado\nitem procesado]
    provider_b --> result

    result --> items[Definir N items\ncon configuracion]

    items --> loop_start{Para cada item}
    loop_start --> procesar[Procesar item]
    procesar --> retry{Exito?}
    retry -->|No, max 3 reintentos| procesar
    retry -->|Si| guardar[Guardar en S3\nRegistrar en BD]
    guardar --> loop_start
    loop_start -->|Fin| reporte[Reporte final\ncosto + resultados]
```

### Flujo de autenticacion y procesamiento (simplificado)

```
flowchart LR
    subgraph Cliente
        user[Usuario]
    end

    subgraph Backend["Backend serverless"]
        auth[API Gateway\nrequest validator]
        fn[Lambda handler]
        factory[ProviderFactory]
    end

    subgraph Async["Background Workers"]
        job[Job processor]
    end

    subgraph External["APIs Externas"]
        providerA[Provider A]
        providerB[Provider B]
        s3[AWS S3]
    end

    user --> auth --> fn --> factory
    factory --> job
    job --> providerA & providerB
    job --> s3
```

---

## architecture para flujo de build / despliegue

### Pipeline de build estatico Astro (ejemplo C4)

```
C4Container
    title portfolio — Pipeline de build y deploy

    Person(dev, "Developer")
    Person(visitor, "Visitante del portfolio")

    Container_Boundary(local, "Local dev") {
        Container(astro, "Astro 6 dev server", "Node", "Puerto 4321")
        Container(vitest, "Vitest", "Unit tests")
        Container(playwright, "Playwright", "E2E tests (opcional)")
    }

    Container_Boundary(ci, "GitHub Actions") {
        Container(lint, "Biome check", "Lint + format")
        Container(typecheck, "tsc + astro check", "Typecheck")
        Container(build, "Astro build", "dist/ estatico")
    }

    System_Ext(cdn, "CDN hosting\n(Vercel / Netlify / Cloudflare Pages)")

    Rel(dev, astro, "pnpm run dev")
    Rel(dev, vitest, "pnpm exec vitest")
    Rel(astro, lint, "git push")
    Rel(lint, typecheck, "next step")
    Rel(typecheck, build, "next step")
    Rel(build, cdn, "deploy")
    Rel(visitor, cdn, "HTTPS")
```

### Version simplificada con graph LR

```
graph LR
    user[Visitante] --> api

    subgraph AWS["AWS us-west-2"]
        api[API Gateway\nREST] --> fn[Lambda\nPython 3.13]
        fn --> ddb[(DynamoDB)]
        ddb -.-> stream[DynamoDB Streams]
        stream --> proc[Lambda\nstream_processor]
        proc --> pg[(Neon\nPostgreSQL 18)]
    end

    fn --> ses[AWS SES]
```

---

## sequenceDiagram para llamadas a API

### Procesamiento con external provider y retry

```
sequenceDiagram
    autonumber
    participant skill as Mermaid Skill
    participant factory as ProviderFactory
    participant provider as Provider
    participant api as External API
    participant s3 as AWS S3
    participant db as PostgreSQL

    skill ->> factory: get_provider("provider_a")
    factory -->> skill: ProviderAdapter

    skill ->> +provider: process(input, params)

    loop hasta 3 reintentos
        provider ->> +api: POST /api/v1/process
        alt exito (200)
            api -->> provider: result_url
        else rate limit (429)
            api -->> provider: 429 Retry-After: 60s
            Note over provider: sleep(backoff * 2^intento)
        else error servidor (500)
            api -->> -provider: 500 Server Error
        end
    end

    provider ->> s3: upload_result(result_bytes, key)
    s3 -->> provider: s3_url

    provider ->> db: INSERT Result(job_id, s3_key, cost)
    db -->> provider: Result.id

    provider -->> -skill: ProcessingResult(result_id, cost)
```

### Flujo de autenticacion OAuth

```
sequenceDiagram
    participant user as Usuario
    participant api as Lambda API
    participant db as Neon PostgreSQL

    user ->> api: POST /auth/login\n{email, password}
    activate api
    api ->> db: SELECT user WHERE email=...
    db -->> api: User object

    alt credenciales validas
        api ->> api: generate_jwt(user.id)
        api -->> user: 200 {access_token, refresh_token}
    else credenciales invalidas
        api -->> user: 401 Unauthorized
    end
    deactivate api

    Note over user,api: Requests autenticadas

    user ->> api: GET /products\nAuthorization: Bearer <token>
    activate api
    api ->> api: validate_jwt(token)

    alt token valido
        api ->> db: SELECT products WHERE user_id=...
        db -->> api: [Product, ...]
        api -->> user: 200 {products: [...]}
    else token expirado
        api -->> user: 401 Token expired
    end
    deactivate api
```

---

<- [01-syntax-reference](01-syntax-reference.md) | [README](README.md) | [03-best-practices](03-best-practices.md) ->
