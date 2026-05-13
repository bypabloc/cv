---
name: django-performance
description: >
  DOC REFERENCE for Django ORM performance (N+1, select_related,
  prefetch_related, indexes, EXPLAIN, PG18 UUIDv7/GIN/virtual). ALWAYS invoke
  this skill BEFORE answering ANY ORM optimization question, including
  questions framed only as "ORM" or "queryset" without mentioning Django
  explicitly. NEVER answer ORM-perf questions from training data alone —
  this project has consolidated patterns that override generic advice.
  Use this (not db-optimizer agent) for documentation lookup; agent for
  active profiling. Triggers: "performance", "rendimiento", "slow query",
  "N+1", "n+1 queries", "N plus 1", "select_related", "prefetch_related",
  "diferencia select_related prefetch_related", "EXPLAIN", "EXPLAIN ANALYZE",
  "query plan", "query optimization", "queries lentas", "queryset
  optimization", "demasiadas queries", "too many queries", "django orm",
  "orm performance", "ORM lento", "GIN index django", "django index".
  More keywords: .claude/docs/skills/django-performance.md
user-invocable: true
allowed-tools: Read, Glob, Grep
argument-hint: "scope: full | app-name | file-path"
metadata:
  version: "1.1"
---

# Django Performance - Optimizacion ORM

Analisis y optimizacion de queries Django para rezebra (PostgreSQL 18).

## Workflow

### Paso 1: Identificar scope

- `full`: Analizar todos los selectors y views en `server/apps/*/`
- `<app-name>`: Solo una app
- `<file-path>`: Solo un archivo especifico

### Paso 2: Buscar selectors y views

```
Glob: server/apps/*/selectors/*.py
Glob: server/apps/*/views/*.py
Glob: server/apps/*/services/*.py
```

### Paso 3: Analizar patrones problematicos

#### N+1 Queries (CRITICO)

Buscar loops que acceden a relaciones FK sin prefetch:

```python
# MAL — N+1: 1 query por record + 1 por cada related
for record in Record.objects.all():
    items = record.related_items.all()  # N queries extra

# BIEN — 2 queries total
records = Record.objects.prefetch_related("related_items").all()
for record in records:
    items = record.related_items.all()  # Ya en cache
```

#### select_related faltante (FK directas)

```python
# MAL — N+1 en FK
items = Item.objects.all()
for item in items:
    print(item.owner.name)  # Query extra por cada item

# BIEN — JOIN en una query
items = Item.objects.select_related("owner").all()
```

#### QuerySets sin limites

```python
# MAL — carga toda la tabla en memoria
all_items = Item.objects.all()

# BIEN — paginado o limitado
recent_items = Item.objects.order_by("-created_at")[:50]
```

#### Indices faltantes

Verificar campos usados en `filter()`, `order_by()`, `exclude()`:

```python
# Si se filtra frecuentemente por status + provider:
class Meta:
    indexes = [
        models.Index(fields=["status", "provider"]),
    ]
```

### Paso 4: Generar reporte

```markdown
## Performance Analysis: [scope]

### N+1 Queries detectados
| Archivo | Linea | Relacion | Fix |
|---------|-------|----------|-----|

### select_related/prefetch_related faltantes
| Archivo | Linea | Campo FK | Fix |
|---------|-------|----------|-----|

### Indices recomendados
| Modelo | Campos | Razon |
|--------|--------|-------|

### QuerySets sin limites
| Archivo | Linea | Fix |
|---------|-------|-----|

### Oportunidades de cache
| Dato | TTL sugerido | Razon |
|------|-------------|-------|
```

## Reglas

- SIEMPRE leer el codigo fuente antes de sugerir optimizaciones
- SIEMPRE verificar que la relacion existe en el modelo antes de sugerir select_related
- NUNCA sugerir `select_related` para relaciones M2M (usar `prefetch_related`)
- NUNCA sugerir cache para datos que cambian frecuentemente sin TTL corto
- Priorizar: N+1 > select_related > indices > cache
- Para `Prefetch` objects complejos, verificar que el queryset base es eficiente
