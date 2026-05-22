# Seeds del CV — Lambda `db`

> Datos del CV que el Lambda `db` carga en PostgreSQL (Neon) con el command
> `seed`. Es la fuente de verdad de los seeds del CV.

## Contenido

`data/` — los datos del CV, un archivo por entry:

- `data/<entidad>/<slug>.yaml` — awards, certificates, education,
  experiences, languages, projects, publications, references, skills.
- `data/profile.ts` — el profile (singleton). Vive como TS porque el
  frontend lo consume como objeto tipado; el seeder extrae el bloque del
  objeto y lo parsea como YAML laxo.

## Como se usa

El `seed_service.py` (`core/services/`) lee este directorio y hace upsert
idempotente en el schema relacional (`shared/db/models/`). Se invoca con:

```bash
python devtools/run.py serverless run --stage=dev --lambda=db \
  --event=events/seed.json --aws-profile=tfs-dev
```

El directorio se vendoriza dentro del zip de deploy del Lambda — por eso vive
en el arbol del Lambda y no se referencia `packages/content/` (que no esta
disponible en el runtime de AWS).

## Origen

Copia de `packages/content/src/data/` (la fuente de las apps Astro). Mientras
las apps no consuman el API `cv`, ambas copias coexisten identicas. Cuando el
plan `c-cv-data-service` cierre, `packages/content/src/data/` queda deprecado
y esta copia es la unica fuente del CV.
