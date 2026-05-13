# Sintaxis de Referencia — Mermaid

[README](README.md) | **01-syntax-reference** | [02-diagram-types](02-diagram-types.md) | [03-best-practices](03-best-practices.md)

---

## erDiagram

### Estructura basica

```
erDiagram
    ENTIDAD_A ||--o{ ENTIDAD_B : "relacion"
    ENTIDAD_A {
        tipo    nombre  PK  "comentario"
        tipo    nombre  FK
        tipo    nombre
    }
```

### Atributos

Sintaxis: `tipo nombre [PK|FK|UK] ["comentario opcional"]`

- `PK` — primary key
- `FK` — foreign key
- `UK` — unique key
- Se pueden combinar: `string id PK,FK`
- El tipo es texto libre: `string`, `int`, `float`, `boolean`, `datetime`, `uuid`, `jsonb`

Ejemplo:

```
erDiagram
    PRODUCT {
        string  id          PK  "UUIDv7"
        string  user_id     FK
        string  name
        boolean is_active
        datetime created_at
    }
```

### Cardinalidades

| Sintaxis | Significado |
|----------|-------------|
| `\|\|--\|\|` | exactamente uno a exactamente uno |
| `\|\|--o\|` | exactamente uno a cero o uno |
| `\|\|--\|{` | exactamente uno a uno o mas |
| `\|\|--o{` | exactamente uno a cero o mas |
| `o\|--\|\|` | cero o uno a exactamente uno |
| `o\|--o\|` | cero o uno a cero o uno |
| `\|{--\|\|` | uno o mas a exactamente uno |
| `}o--o{` | cero o mas a cero o mas |
| `}o--\|{` | cero o mas a uno o mas |

- `--` linea solida (relacion identificatoria)
- `..` linea punteada (relacion no identificatoria)

### Aliases de entidad

```
erDiagram
    BACKGROUND_JOB [Job] {
        string id PK
    }
```

### Ejemplo completo

```
erDiagram
    USER ||--o{ PRODUCT : "owns"
    PRODUCT ||--o{ ORDER : "has"
    ORDER }o--|| CATEGORY : "belongs_to"
    ORDER ||--o{ ORDER_ITEM : "contains"

    USER {
        string  id          PK  "UUIDv7"
        string  email       UK
        string  username    UK
    }
    PRODUCT {
        string  id          PK
        string  user_id     FK
        string  name
        boolean is_active
    }
    ORDER {
        string  id          PK
        string  product_id  FK
        string  category_id FK
        string  status
        float   total
    }
```

---

## flowchart

### Estructura basica

```
flowchart TD
    A[Nodo rectangulo] --> B(Nodo redondeado)
    B --> C{Decision}
    C -->|si| D[Resultado A]
    C -->|no| E[Resultado B]
```

### Direcciones

| Keyword | Direccion |
|---------|-----------|
| `TD` o `TB` | top-down |
| `BT` | bottom-top |
| `LR` | left-right |
| `RL` | right-left |

### Shapes de nodos

| Sintaxis | Shape |
|----------|-------|
| `A[texto]` | rectangulo |
| `A(texto)` | bordes redondeados |
| `A([texto])` | estadio/pill |
| `A[[texto]]` | subrutina |
| `A[(texto)]` | cilindro / base de datos |
| `A((texto))` | circulo |
| `A{texto}` | rombo / decision |
| `A{{texto}}` | hexagono |
| `A[/texto/]` | paralelogramo |
| `A[\texto\]` | paralelogramo invertido |
| `A[/texto\]` | trapecio |
| `A>texto]` | asimetrico |

### Tipos de conexion

| Sintaxis | Tipo |
|----------|------|
| `-->` | flecha solida |
| `---` | linea solida sin flecha |
| `-.->` | flecha punteada |
| `==>` | flecha gruesa |
| `--texto-->` | flecha con label |
| `--\|texto\|` | label en linea |
| `~~~` | linea invisible (para alinear) |

### Subgraphs

```
flowchart TD
    subgraph Docker["Docker Network"]
        A[Django] --> B[(PostgreSQL)]
        A --> C[(Redis)]
    end
    D[Usuario] --> A
```

### Directiva ELK para grafos grandes

Usar cuando hay mas de 15 nodos y el layout queda caótico:

```
%%{init: {"flowchart": {"defaultRenderer": "elk"}}}%%
flowchart TD
    ...
```

### classDef para estilos

```
flowchart TD
    A[Paso 1]:::api --> B[Paso 2]:::storage

    classDef api fill:#dbeafe,stroke:#3b82f6
    classDef storage fill:#dcfce7,stroke:#22c55e
```

---

## architecture (C4 y graph)

### Opcion A: C4Context (recomendada para arquitectura de sistemas)

```
C4Context
    title Sistema portfolio

    Person(user, "Usuario", "Usa la plataforma")
    System(app, "portfolio", "Portfolio CV (Astro 6 estatico)")
    System_Ext(extApi, "External API", "API de terceros")
    System_Ext(s3, "AWS S3", "Almacenamiento de archivos")

    Rel(user, app, "Usa")
    Rel(app, extApi, "Llama a API")
    Rel(app, s3, "Sube archivos")
```

Funciones disponibles en C4Context:

- `Person(alias, label, descr)` — usuario
- `System(alias, label, descr)` — sistema interno
- `System_Ext(alias, label, descr)` — sistema externo
- `Rel(from, to, label)` — relacion
- `Rel(from, to, label, techn)` — relacion con tecnologia
- `UpdateElementStyle(alias, $bgColor, $fontColor, $borderColor)`
- `UpdateRelStyle(from, to, $textColor, $lineColor)`

### Opcion B: C4Container (para internos del sistema)

```
C4Container
    title Contenedores portfolio

    Person(user, "Usuario")

    Container_Boundary(app, "portfolio") {
        Container(web, "Django", "Python 3.14", "API REST")
        Container(worker, "Worker", "Python", "Background tasks")
        ContainerDb(db, "PostgreSQL 18", "SQL", "Datos principales")
        ContainerDb(cache, "Redis 7", "In-memory", "Broker + cache")
    }

    System_Ext(s3, "AWS S3")
    Rel(user, web, "HTTP/REST")
    Rel(web, worker, "Enqueue tasks")
    Rel(web, db, "Reads/Writes")
    Rel(worker, s3, "Upload files")
```

### Opcion C: graph LR (para diagramas de servicios Docker)

```
graph LR
    nginx[nginx\nreverse proxy] --> django[Django\n:8000]
    django --> pg[(PostgreSQL 18)]
    django --> redis[(Redis 7)]
    django --> worker[Worker\ntasks]
    worker --> s3[AWS S3]
    worker --> extApi[External\nAPI]
```

> NOTA: `architecture-beta` existe en Mermaid v11+ pero tiene sintaxis inestable.
> Usar C4Context o graph LR para resultados confiables.

---

## sequenceDiagram

### Estructura basica

```
sequenceDiagram
    participant A as Cliente
    participant B as Servidor
    participant C as API Externa

    A ->> B: POST /generate
    activate B
    B ->> C: Llamada API
    C -->> B: Respuesta
    B -->> A: 200 OK
    deactivate B
```

### Participantes

```
sequenceDiagram
    participant cli as Claude Code Skill
    actor user as Usuario
    participant api as fal.ai API
```

- `participant alias as Label` — caja rectangular
- `actor alias as Label` — figura de persona
- Orden de declaracion = orden de aparicion

### Tipos de flecha

| Sintaxis | Tipo |
|----------|------|
| `A -> B` | linea solida sin flecha |
| `A --> B` | linea punteada sin flecha |
| `A ->> B` | linea solida con flecha abierta |
| `A -->> B` | linea punteada con flecha abierta |
| `A <<->> B` | flecha bidireccional solida (v11+) |
| `A -x B` | linea solida con X (mensaje perdido) |
| `A --x B` | linea punteada con X |
| `A -) B` | linea solida con flecha async |
| `A --) B` | linea punteada con flecha async |

### Activaciones

```
sequenceDiagram
    A ->> B: solicitud
    activate B
    B -->> A: respuesta
    deactivate B

    %% Notacion alternativa con + y -
    A ->> +B: solicitud
    B -->> -A: respuesta
```

### autonumber

```
sequenceDiagram
    autonumber
    A ->> B: Paso 1
    B ->> C: Paso 2
    C -->> A: Paso 3
```

### Bloques de control

```
sequenceDiagram
    %% Loop
    loop cada 30 segundos
        A ->> B: healthcheck
    end

    %% Condicional
    alt exito
        B -->> A: 200 OK
    else error temporal
        B -->> A: 503 Retry-After
    else error critico
        B -->> A: 500 Error
    end

    %% Opcional
    opt si tiene descuento
        A ->> B: aplicar_descuento()
    end

    %% Paralelo
    par enviar email
        A ->> email: notificar
    and enviar webhook
        A ->> webhook: disparar
    end

    %% Break
    break si token invalido
        A -->> A: lanzar AuthError
    end

    %% Rect con color de fondo
    rect rgb(200, 220, 255)
        A ->> B: operacion con fondo
    end

    %% Box para agrupar participantes
    box Azure Interno
        participant A
        participant B
    end
```

### Notes

```
sequenceDiagram
    Note over A,B: Inicio de autenticacion
    Note right of A: Token generado
    Note left of B: Verificando permisos
```

---

## Directivas de configuracion

```
%%{init: {
  "theme": "default",
  "flowchart": {
    "curve": "stepBefore",
    "defaultRenderer": "elk"
  },
  "sequence": {
    "mirrorActors": false,
    "showSequenceNumbers": true
  }
}}%%
```

### Temas disponibles

| Tema | Uso recomendado |
|------|-----------------|
| `default` | documentacion general |
| `dark` | presentaciones con fondo oscuro |
| `neutral` | impresion / PDF |
| `forest` | documentacion tecnica verde |
| `base` | personalizacion manual con variables |

---

[README](README.md) | [02-diagram-types](02-diagram-types.md) →
