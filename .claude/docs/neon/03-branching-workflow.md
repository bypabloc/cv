# Branching: testing y preview deployments

> Git-style database branching en Neon. Instant clones, copy-on-write, testing
> per-PR, preview environments. Verificado 2026-05-14.

## Que es un branch en Neon

Un **branch** es una copia instantanea (copy-on-write) de tu database en un punto en el tiempo:

```
Production main:   [data snapshot A]
                        ↓
Test branch-1:     [copy-on-write snapshot A + writes locales]
Test branch-2:     [copy-on-write snapshot A + writes locales]
                        ↓ (cuando merge → discard)
```

- **Creation**: ~1 segundo (instant, sin esperar copy)
- **Storage**: COW = sin costo inicial (ej. 100 GB database = 100 GB copias = solo 1 copia pagada)
- **Isolation**: cambios en branch-1 NO afectan main ni branch-2
- **Retention**: ephemeral (delete cuando done) o persistent (backup)

## Use cases para el portfolio

### 1. Testing antes de migrations schema

```bash
# Main database: produccion
# Feature: agregar columna "last_contact_date" a contacts

neon branch create --name test-schema-migration --parent main

# En test branch:
# - correr migration
# - test queries que usan nueva columna
# - si falla: discard branch, iterar
# - si pasa: apply migration a main, delete branch
```

### 2. Per-PR databases (Vercel preview equivalente)

Workflow CI/CD:

```yaml
# .github/workflows/test.yml
on: pull_request

jobs:
  test-db:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Create Neon branch for PR
        run: |
          BRANCH_ID=$(neon branch create \
            --name pr-${{ github.event.number }} \
            --parent main \
            --format json | jq -r '.branch.id')
          echo "BRANCH_ID=$BRANCH_ID" >> $GITHUB_ENV

      - name: Run tests against branch
        env:
          DATABASE_URL: ${{ env.BRANCH_CONNECTION_STRING }}
        run: |
          pytest tests/integration/

      - name: Delete branch on failure
        if: failure()
        run: neon branch delete pr-${{ github.event.number }}
```

Resultado: cada PR = database independiente para testing. Main intacta.

### 3. Data recovery (point-in-time)

Neon retention: 7-30 dias (segun plan).

```bash
# Accidente: borraste tabla importante hace 2 horas

# Opcion 1: crear branch de main de 2 horas atras
neon branch create \
  --name recovery-2hago \
  --parent main \
  --lsn <snapshot-lsn-from-2-hours-ago>

# Opcion 2: PITR query (time travel)
SELECT * FROM table_name
WHERE created_at > '2026-05-14 08:00:00'::timestamptz
```

Funcionalidad unica de Neon (RDS snapshot = horas, no segundos).

## Branching workflow tipo

```
Day 1:
  Feature X:    main ──branch(feature/x-new-col)→ [testing, schema migrations]
  Feature Y:    main ──branch(feature/y-analytics)→ [testing, queries]
              
Day 2:
  PR #42 (Feature X):  merge + delete branch (data persisted in main)
  Feature Y still testing...
  
Day 3:
  PR #43 (Feature Y):  merge + delete branch
  
Main always safe, data cumulative
```

## CLI commands basicos

```bash
# Listar branches
neon branch list

# Crear branch (desde main)
neon branch create --name feature-x --parent main

# Crear branch desde snapshot (point-in-time)
neon branch create --name recovery --parent main --lsn <lsn-value>

# Obtener connection string de branch
neon connection-string --branch-id feature-x

# Cambiar compute size de branch (para testing performance)
neon compute-endpoint update \
  --branch feature-x \
  --size-cusize 1  # 1 CU (full compute)

# Delete branch (discard cambios)
neon branch delete feature-x
```

## Neon serverless driver (opcional, para HTTP)

Neon ofrece **serverless driver** (HTTP-based, sin TCP pooling):

```javascript
// Node.js ejemplo (no Python aun)
import { neon } from '@neondatabase/serverless'

const sql = neon(process.env.DATABASE_URL)

async function getContacts() {
  return await sql`SELECT * FROM contacts`
}
```

Status: Node.js + TypeScript. Python: usar psycopg3 directo (TCP).

Para portfolio: **psycopg3 + pooled endpoint** es standard path.

## Storage analysis (branching overhead)

Free tier: 0.5 GB storage.

```
Main database:            100 MB
├─ Branch A:              +0 MB (COW hasta primera write)
├─ Branch B:              +0 MB (COW)
└─ Branch C:              +5 MB (despues de escribir)

Total: 100 + 0 + 0 + 5 = 105 MB (dentro de 0.5 GB free)
```

COW = no pagar por copias no modificadas. Perfect para testing.

## Gotchas

| Gotcha | Solucion |
|--------|----------|
| Branch desaparece si no la uso | No hay timeout; persiste indefinido (o hasta deletion) |
| Compute suspendido en branch | Normal (auto-suspend 5 min). Resume transparente. |
| Cambios en branch no sincro a main | Correcto. Discard branch descarta cambios, o manually copy con SQL |
| Vercel preview no integrado | Pero CI/CD puede crear branch per PR (manual setup) |

## Limitaciones por plan

| Limite | Free | Launch | Scale |
|--------|------|--------|-------|
| Branches simultaneas | 10 | 10 | unlimited |
| Retencion snapshot | 7 dias | 7 dias | 30 dias |
| Branch TTL | indefinido | indefinido | indefinido |

Portfolio Free tier: 10 branches simultaneas (suficiente para <10 features).

## Integracion con git workflow

Workflow recomendado:

```
git branch feature/x → Neon branch feature/x
git push → CI crea DB branch, tests corre
PR approval → merge DB + code
git delete branch → neon branch delete
```

Sin automatizacion: hacer manualmente (tediable, pero posible).

Con GitHub Actions: completamente automatizado (workflow arriba).

## Summary

✓ Instant database branching (1 segundo)
✓ Copy-on-write = sin costo storage
✓ Perfect para testing schemas + migrations
✓ Point-in-time recovery (7-30 dias)
✓ Para portfolio: 10 branches free tier suficiente

Siguiente: comparativa con alternativas (RDS, Supabase, etc).

## Referencias

- [Branching Documentation](https://neon.com/docs/introduction/branching)
- [Branching Workflow Primer](https://neon.com/docs/get-started/workflow-primer)
- [CLI Documentation](https://neon.com/docs/reference/cli-commands)
- [Serverless Driver](https://neon.com/docs/serverless/serverless-driver)
