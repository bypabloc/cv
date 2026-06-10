# db_export

> Exporta TODA la data CV de Neon a YAML **seed-compatible** y la sube a
> S3 (`portfolio-db-backups-<stage>`). La DB es la fuente de verdad; el
> YAML pasa a ser el snapshot de backup que el seed/restore de la Lambda
> `db` puede volver a cargar (round-trip).

## Uso

```bash
# Export + upload a S3 (history/<fecha>/ + latest/)
python devtools/run.py db_export --stage=dev --aws-profile=tfs-dev

# Dry-run: exporta a staging local y lista lo que subiria (sin tocar S3)
python devtools/run.py db_export --stage=dev --aws-profile=tfs-dev --dry-run

# Solo local (sin S3), con copia extra para inspeccion
python devtools/run.py db_export --stage=dev --aws-profile=tfs-dev \
  --no-upload --out=tmp/db-export-copy
```

## Flags

| Flag | Requerida | Descripcion |
|------|-----------|-------------|
| `--stage=dev\|prod` | si | Stage a exportar (SSM path + bucket destino) |
| `--aws-profile=<p>` | no | Perfil AWS CLI para SSM + S3 (CI usa OIDC, sin flag) |
| `--dry-run` | no | Exporta local y lista destinos S3, sin subir |
| `--out=<dir>` | no | Copia local extra del snapshot (debug) |
| `--no-upload` | no | Solo export local, sin S3 |

## Que produce

Staging local en `tmp/db-export/<stage>/` (gitignored, se recrea en cada
run) con el MISMO shape que consumia `core/seeds/data/`:

```text
profile.yaml
experiences/<slug>.yaml      # role{es,en}, start/end, bullets, skills...
projects/<slug>.yaml         # caseStudy(Detailed), metrics, stack...
skills/<slug>.yaml           # categorias + skills[] ordenadas
certificates/<slug>.yaml
awards/<slug>.yaml
education/<slug>.yaml
endorsements/<slug>.yaml
languages/<slug>.yaml
publications/<slug>.yaml
```

Y en S3:

```text
s3://portfolio-db-backups-<stage>/history/<YYYY-MM-DD>/...  # inmutable, 84d
s3://portfolio-db-backups-<stage>/latest/...                # espejo (--delete)
```

## Garantias

- **Seed-compatible**: cada YAML usa exactamente las claves que leen los
  upserts de `shared.db.repositories.cv_write_entities` (camelCase,
  bloques bilingues `{es, en}`, `niches`, `priority`). Export ->
  seed(restore) -> export produce el mismo YAML.
- **Hermetico**: la Neon URL se resuelve de SSM
  (`/portfolio/<stage>/neon-url`, SecureString) y NUNCA se imprime; los
  errores de psycopg se sanitizan antes de salir por stderr.
- **Read-only**: la conexion a Neon se abre con `read_only = True` — el
  export no puede mutar la DB.
- **Determinista**: entidades por `slug`, niches por `display_order`,
  hijos ordenados por `position` (skills de experiencia por `name`: la
  union no tiene columna de orden).

## Automatizacion

`.github/workflows/db-backup.yml` corre el export semanal (lunes 06:00
UTC) para dev y prod via OIDC (`role/portfolio-db-backup`), y permite
dispatch manual con input `stage` (dev / prod / all).

## Modulos

| Archivo | Responsabilidad |
|---------|-----------------|
| `flags.py` | Validacion de flags (mono-comando) |
| `main.py` | Orquestador: SSM -> Neon -> staging -> S3 |
| `queries.py` | SQL read-only por entidad (psycopg v3) |
| `serializer.py` | Funciones puras filas -> dict YAML seed-shape |
| `s3_writer.py` | `aws s3 sync` a history/ + latest/ |
