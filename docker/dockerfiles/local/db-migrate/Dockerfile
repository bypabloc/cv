# One-shot container que corre `alembic upgrade head` contra el Postgres
# local. Se usa en docker-compose/local.yml y test.yml como dependencia
# inicializadora (depends_on: postgres-local: service_healthy). Sin uv:
# pip directo, deps pinneadas a las versiones del lambda `db`.
#
# El `serverless/lambda/shared/` (que trae el package `shared.db` + las
# migraciones Alembic) se bind-montea en /app/shared para que cualquier
# cambio al schema se refleje sin rebuild de la imagen.

FROM python:3.13-slim

# libpq5 lo necesita psycopg[binary] en runtime para conectar a Postgres.
RUN apt-get update -qq \
    && apt-get install -y -qq --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir \
        'psycopg[binary]>=3.2,<4' \
        'sqlalchemy>=2.0,<3' \
        'alembic>=1.13,<2'

WORKDIR /app

# `alembic.ini` define `prepend_sys_path = %(here)s/../..` que apunta a
# `/app/`; asi `import shared.db.models` resuelve dentro del container.
ENV PYTHONPATH=/app

# Default: aplicar todas las migraciones pendientes. Override-able via
# `command:` en docker-compose para correr `current`, `downgrade`, etc.
CMD ["alembic", "-c", "shared/db/alembic.ini", "upgrade", "head"]
