[Volver al indice](README.md) | [Siguiente: Docker Compose](02-docker-compose.md)

# Docker para Django - Dockerfile

> Patrones de Dockerfile para Django 6 con multi-stage builds, uv y seguridad.

## Base image

```dockerfile
# Recomendado: slim-bookworm (~41MB)
FROM python:3.12-slim-bookworm

# Alternativa: bookworm completo (~350MB) - solo si necesitas compiladores
FROM python:3.12-bookworm

# NO recomendado: alpine (~17MB) - musl libc rompe psycopg2, Pillow, numpy
FROM python:3.12-alpine  # EVITAR
```

| Image | Size | Pros | Contras |
|-------|------|------|---------|
| `slim-bookworm` | ~41MB | Balance tamano/compatibilidad | Falta compiladores |
| `bookworm` | ~350MB | Todo incluido | Grande |
| `alpine` | ~17MB | Minima | musl rompe wheels binarios |

**Recomendacion**: `python:3.12-slim-bookworm` para todos los proyectos Django.

## Multi-stage build

Reduce imagen de ~1.2GB a ~150MB separando build de runtime:

```dockerfile
# ============================================
# Stage 1: Builder - instala dependencias
# ============================================
FROM python:3.12-slim-bookworm AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ============================================
# Stage 2: Runtime - solo lo necesario
# ============================================
FROM python:3.12-slim-bookworm AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Non-root user
RUN useradd --create-home --shell /bin/bash appuser

# Copiar dependencias del builder
COPY --from=builder /install /usr/local

WORKDIR /app
COPY --chown=appuser:appuser . .

# Collectstatic
RUN python manage.py collectstatic --noinput

USER appuser

EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
```

## Instalacion con uv

10-15x mas rapido que pip. Recomendado para 2025+:

```dockerfile
# ============================================
# Stage 1: Builder con uv
# ============================================
FROM python:3.12-slim-bookworm AS builder

# Instalar uv desde imagen oficial
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar archivos de dependencias primero (cache de layers)
COPY pyproject.toml uv.lock ./

# Instalar dependencias con uv
ENV UV_LINK_MODE=copy
RUN uv sync --frozen --no-dev --no-install-project

# ============================================
# Stage 2: Runtime
# ============================================
FROM python:3.12-slim-bookworm AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# Copiar virtualenv del builder
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

COPY --chown=appuser:appuser . .
RUN python manage.py collectstatic --noinput

USER appuser
EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
```

**Nota**: `UV_LINK_MODE=copy` evita symlinks rotos al copiar entre stages.

## Instalacion con pip

Alternativa tradicional con cache mount:

```dockerfile
FROM python:3.12-slim-bookworm AS builder

WORKDIR /app
COPY requirements.txt .

# Cache mount acelera rebuilds
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir --prefix=/install -r requirements.txt
```

## Non-root user

Seguridad obligatoria en produccion:

```dockerfile
# Crear usuario sin privilegios
RUN useradd --create-home --shell /bin/bash --uid 1000 appuser

# Dar ownership del directorio de trabajo
COPY --chown=appuser:appuser . /app

# Cambiar a non-root ANTES de CMD
USER appuser
```

**Nunca** ejecutar `gunicorn` o `manage.py` como root.

## ENTRYPOINT vs CMD

```dockerfile
# Patron recomendado: entrypoint.sh + CMD
COPY --chown=appuser:appuser entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
```

```bash
#!/bin/bash
# entrypoint.sh
set -e

# Esperar a que PostgreSQL este listo
echo "Waiting for PostgreSQL..."
while ! python -c "import psycopg; psycopg.connect('$DATABASE_URL')" 2>/dev/null; do
    sleep 1
done
echo "PostgreSQL ready"

# Ejecutar migraciones
python manage.py migrate --noinput

# Ejecutar comando pasado como argumento
exec "$@"
```

## Health checks

```dockerfile
# Health check en Dockerfile
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/')" || exit 1
```

```python
# urls.py - endpoint de health check
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({"status": "ok"})

urlpatterns = [
    path("health/", health_check),
]
```

## .dockerignore

```text
# .dockerignore
.git
.gitignore
.env
.env.*
*.pyc
__pycache__
*.pyo
.pytest_cache
.mypy_cache
.ruff_cache
htmlcov
.coverage
*.egg-info
dist
build
node_modules
tmp/
.claude/
*.md
!requirements*.txt
docker-compose*.yml
Dockerfile*
.dockerignore
.venv
.vscode
```

## Optimizacion de cache de layers

Orden de instrucciones para maximizar cache:

```dockerfile
# 1. Base image (cambia raramente)
FROM python:3.12-slim-bookworm

# 2. System packages (cambia raramente)
RUN apt-get update && apt-get install -y ...

# 3. Dependencias Python (cambia ocasionalmente)
COPY requirements.txt .
RUN pip install -r requirements.txt

# 4. Codigo fuente (cambia frecuentemente)
COPY . .

# 5. Build steps (collectstatic, etc.)
RUN python manage.py collectstatic --noinput
```

Copiar `requirements.txt` ANTES del codigo fuente permite reusar la cache de pip cuando solo cambia el codigo.

> Nota: el server de rezebra usa la imagen oficial `ghcr.io/astral-sh/uv:python3.14-bookworm-slim` con `uv sync --frozen --no-install-project`, que aplica el mismo principio (lockfile copiado primero, luego codigo) pero con uv en lugar de pip. Ver `docker/dockerfiles/{prod,dev,local,test}/server` y la guia de migracion en este repo.

## Ejemplo completo production-ready

```dockerfile
# Dockerfile
FROM python:3.12-slim-bookworm AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml uv.lock ./
ENV UV_LINK_MODE=copy
RUN uv sync --frozen --no-dev --no-install-project

FROM python:3.12-slim-bookworm AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 curl \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /bin/bash --uid 1000 appuser

WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY --chown=appuser:appuser . .
RUN python manage.py collectstatic --noinput

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

USER appuser
EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "3", \
     "--timeout", "120", \
     "--access-logfile", "-"]
```

---

[Volver al indice](README.md) | [Siguiente: Docker Compose](02-docker-compose.md)
