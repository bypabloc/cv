#!/bin/sh
# Entrypoint compartido para el container `e2e` (E2E unificado Python 3.14).
#
# El container corre contra el backend DESPLEGADO (dev|stage): NO necesita
# resolver subdominios *.localhost ni el stack de apps. Solo necesita salida
# a internet (URLs publicas) + acceso a SSM/Neon (creds AWS montadas).
#
# A diferencia del viejo container `feature` (pnpm + Playwright TS), aqui el
# entorno Python ya esta listo: la imagen instalo devtools/.venv + los
# browsers de playwright-python en build time. El entrypoint solo deja el
# container vivo y crea el sentinel /tmp/.e2e-ready que e2e/container.py
# espera antes de correr pytest.

set -e

# Bind mount del repo en /app: re-sincroniza el .venv por si el lockfile
# cambio respecto al build (best-effort; no rompe el arranque si falla).
if command -v uv >/dev/null 2>&1 && [ -f /app/devtools/pyproject.toml ]; then
  echo "Sincronizando devtools/.venv (uv sync)..."
  uv sync --frozen --project /app/devtools >/dev/null 2>&1 \
    || echo "[WARN] uv sync fallo; usando el .venv del build."
fi

touch /tmp/.e2e-ready
echo "Container e2e listo."
exec "$@"
