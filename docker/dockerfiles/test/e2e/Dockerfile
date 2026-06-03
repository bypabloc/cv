# Portfolio: container E2E unificado (Python 3.14 + playwright-python).
# Stays alive; tests triggered via `docker compose exec e2e python -m pytest`.
#
# DECISION DE IMAGEN BASE: python:3.14-slim (NO la oficial de Playwright).
#   La imagen oficial `mcr.microsoft.com/playwright/python:vX` trae los
#   browsers + deps de SO preinstalados, PERO esta basada en Python 3.13
#   (Microsoft aun no publica una variante 3.14, may 2026). El portfolio
#   esta pinneado a Python 3.14 (`requires-python = "==3.14.*"` en
#   devtools/pyproject.toml) y `devtools/.venv` se crea con `uv sync` que
#   EXIGE 3.14 -> usar la imagen oficial 3.13 rompe el `uv sync`. Por eso
#   partimos de python:3.14-slim e instalamos los browsers a mano con
#   `playwright install --with-deps chromium webkit` (trae chromium+webkit
#   + las deps de SO). El harness solo usa chromium + webkit (no firefox).

FROM python:3.14-slim

# uv: gestor de entornos del proyecto (lo usa devtools/run.py + el
# entrypoint para `uv sync`). Instalado al PATH global (/usr/local/bin).
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# libpq5 lo necesita psycopg[binary] (seed/cleanup Neon) en runtime.
RUN apt-get update -qq \
    && apt-get install -y -qq --no-install-recommends \
        libpq5 \
        ca-certificates \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia la definicion del entorno + el codigo. El bind mount del repo en
# /app (compose) sobreescribe esto en runtime; el COPY garantiza que la
# imagen es autocontenida (build del .venv + browsers en build time).
COPY devtools/pyproject.toml devtools/uv.lock /app/devtools/
COPY devtools/ /app/devtools/
COPY tests/ /app/tests/

# Crea devtools/.venv (Python 3.14) con las deps E2E (playwright, pytest,
# httpx, psycopg, boto3, cryptography). `--frozen` = bit-perfect vs uv.lock.
RUN uv sync --frozen --project /app/devtools

# Instala los browsers de playwright-python (chromium + webkit) + sus deps
# de SO. Se ejecuta con el python del .venv para que playwright resuelva la
# version instalada. Los browsers quedan en /root/.cache/ms-playwright.
RUN /app/devtools/.venv/bin/python -m playwright install --with-deps \
        chromium webkit

COPY docker/scripts/e2e-entrypoint.sh /usr/local/bin/e2e-entrypoint.sh
RUN chmod +x /usr/local/bin/e2e-entrypoint.sh

ENV PYTHONPATH=/app/tests

ENTRYPOINT ["/usr/local/bin/e2e-entrypoint.sh"]
CMD ["tail", "-f", "/dev/null"]
