[Anterior: Dockerfile](01-dockerfile.md) | [Volver al indice](README.md)

# Docker para Django - Docker Compose

> Configuracion de compose.yml para Django 6 + PostgreSQL 18 con health checks, volumes y secrets.

## compose.yml basico

```yaml
# compose.yml (sin campo "version:" - deprecado)
services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgres://postgres:secret@db:5432/mydb
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:18-bookworm
    environment:
      POSTGRES_DB: mydb
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: secret
    volumes:
      - pgdata:/var/lib/postgresql/18/docker
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  pgdata:
```

## PostgreSQL 18 PGDATA (breaking change)

La imagen Docker oficial de PostgreSQL 18 cambia la ruta de datos:

| Version | PGDATA por defecto |
|---------|-------------------|
| PG 14-17 | `/var/lib/postgresql/data` |
| PG 18 | `/var/lib/postgresql/18/docker` |

### Opcion 1: Usar nueva ruta (recomendado para proyectos nuevos)

```yaml
services:
  db:
    image: postgres:18-bookworm
    volumes:
      - pgdata:/var/lib/postgresql/18/docker
```

### Opcion 2: Override PGDATA (compatibilidad con volumenes existentes)

```yaml
services:
  db:
    image: postgres:18-bookworm
    environment:
      PGDATA: /var/lib/postgresql/data
      POSTGRES_PASSWORD: secret
    volumes:
      - pgdata:/var/lib/postgresql/data
```

### Opcion 3: Migrar datos existentes

```bash
# 1. Backup con pg_dumpall
docker compose exec db pg_dumpall -U postgres > backup.sql

# 2. Eliminar volumen antiguo
docker compose down -v

# 3. Actualizar compose.yml con nueva ruta
# 4. Recrear y restaurar
docker compose up -d db
docker compose exec -T db psql -U postgres < backup.sql
```

## Health checks

### PostgreSQL

```yaml
services:
  db:
    image: postgres:18-bookworm
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d mydb"]
      interval: 5s
      timeout: 5s
      retries: 5
      start_period: 10s
```

### Django

```yaml
services:
  web:
    build: .
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8000/health/ || exit 1"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 15s
    depends_on:
      db:
        condition: service_healthy
```

### depends_on con condiciones

```yaml
services:
  web:
    depends_on:
      db:
        condition: service_healthy     # espera health check
      redis:
        condition: service_started     # solo espera que inicie
      migrations:
        condition: service_completed_successfully  # espera que termine OK
```

## Volumes

### Named volumes (datos persistentes)

```yaml
volumes:
  pgdata:
    driver: local

services:
  db:
    volumes:
      - pgdata:/var/lib/postgresql/18/docker
```

### Bind mounts (desarrollo)

```yaml
services:
  web:
    volumes:
      - .:/app                    # Codigo fuente (hot reload)
      - /app/.venv                # Excluir .venv del bind mount
      - static_data:/app/static   # Static files persistentes
```

## Entorno de desarrollo

```yaml
# compose.yml (desarrollo)
services:
  web:
    build:
      context: .
      target: builder    # usar stage de builder (tiene dev dependencies)
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/app
      - /app/.venv
    ports:
      - "8000:8000"
    environment:
      - DEBUG=1
      - DATABASE_URL=postgres://postgres:secret@db:5432/mydb
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:18-bookworm
    environment:
      POSTGRES_DB: mydb
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: secret
    ports:
      - "5432:5432"    # Exponer para acceso local con pgAdmin/DBeaver
    volumes:
      - pgdata:/var/lib/postgresql/18/docker
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  pgdata:
```

### Docker Compose Watch (hot reload automatico)

```yaml
services:
  web:
    build: .
    develop:
      watch:
        - action: sync
          path: ./src
          target: /app/src
        - action: rebuild
          path: requirements.txt
```

```bash
docker compose watch  # Inicia con file watching
```

## Entorno de produccion

```yaml
# compose.prod.yml
services:
  web:
    build:
      context: .
      target: runtime
    restart: always
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.production
      - DATABASE_URL=postgres://appuser:${DB_PASSWORD}@db:5432/mydb
      - ALLOWED_HOSTS=${ALLOWED_HOSTS}
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      db:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8000/health/ || exit 1"]
      interval: 30s
      timeout: 5s
      retries: 3

  db:
    image: postgres:18-bookworm
    restart: always
    environment:
      POSTGRES_DB: mydb
      POSTGRES_USER: appuser
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/18/docker
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U appuser -d mydb"]
      interval: 10s
      timeout: 5s
      retries: 5

  nginx:
    image: nginx:1.27-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - static_data:/var/www/static:ro
    depends_on:
      web:
        condition: service_healthy

volumes:
  pgdata:
  static_data:
```

```bash
# Ejecutar con compose de produccion
docker compose -f compose.yml -f compose.prod.yml up -d
```

## Docker secrets

Manejo seguro de credenciales (no usar env vars para produccion):

```yaml
services:
  db:
    image: postgres:18-bookworm
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    secrets:
      - db_password

  web:
    build: .
    secrets:
      - db_password
      - django_secret_key

secrets:
  db_password:
    file: ./secrets/db_password.txt    # archivo local
  django_secret_key:
    file: ./secrets/django_secret.txt
```

```python
# settings.py - leer secrets desde archivo
from pathlib import Path

def read_secret(name: str, default: str = "") -> str:
    secret_path = Path(f"/run/secrets/{name}")
    if secret_path.exists():
        return secret_path.read_text().strip()
    return os.getenv(name.upper(), default)

SECRET_KEY = read_secret("django_secret_key")
DB_PASSWORD = read_secret("db_password")
```

## Migraciones en Docker

### Opcion 1: En entrypoint (simple)

```bash
# entrypoint.sh
python manage.py migrate --noinput
exec "$@"
```

### Opcion 2: Service separado (produccion)

```yaml
services:
  migrations:
    build: .
    command: python manage.py migrate --noinput
    environment:
      - DATABASE_URL=postgres://postgres:secret@db:5432/mydb
    depends_on:
      db:
        condition: service_healthy

  web:
    build: .
    depends_on:
      migrations:
        condition: service_completed_successfully
```

### Init scripts de PostgreSQL

```yaml
services:
  db:
    image: postgres:18-bookworm
    volumes:
      - pgdata:/var/lib/postgresql/18/docker
      - ./init-scripts:/docker-entrypoint-initdb.d  # Se ejecutan al crear DB
```

```sql
-- init-scripts/01-extensions.sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

## Comandos utiles

```bash
# Levantar servicios
docker compose up -d

# Ver logs
docker compose logs -f web
docker compose logs -f db

# Ejecutar comando en container
docker compose exec web python manage.py createsuperuser
docker compose exec db psql -U postgres -d mydb

# Shell Django
docker compose exec web python manage.py shell

# Rebuild sin cache
docker compose build --no-cache web

# Parar y eliminar volumenes
docker compose down -v

# Ver estado de health checks
docker compose ps
```

---

[Anterior: Dockerfile](01-dockerfile.md) | [Volver al indice](README.md)
