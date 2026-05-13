#!/bin/sh
# Entrypoint para apps Astro en modo dev (HMR).
#
# CORRE COMO ROOT al inicio:
#   1. Fixea permisos del named volume node_modules (root-owned al primer mount)
#   2. Hace el directorio /app escribible por uid app (para tmp files de pnpm)
#   3. Baja privilegios al user `app` (UID 1000 por default)
#   4. Ejecuta pnpm install + dev server como `app`
#
# Variables esperadas:
#   APP_NAME — hub, generic, fintech, architect, leader, vibe
#   UID/GID  — uid/gid del usuario host (default 1000:1000)

set -e

if [ -z "${APP_NAME:-}" ]; then
  echo "ERROR: APP_NAME no esta definido" >&2
  exit 1
fi

UID_RUN="${UID:-1000}"
GID_RUN="${GID:-1000}"

# Fix permisos del bind mount y named volumes.
# /app                -> bind mount del repo (puede ser root-owned en CI)
# /app/node_modules   -> named volume vacío (root-owned al primer mount)
#
# IMPORTANTE: chown solo de /app (depth 0) y /app/node_modules. NO recursivo
# en el bind mount porque (a) es caro y (b) lo del host se ve afectado en
# desarrollo local. pnpm escribe sus _tmp_<n>_<hash> en la raíz del workdir
# (/app/), por eso necesita /app con write para uid app.
if [ "$(id -u)" = "0" ]; then
  echo "[entrypoint] Ajustando permisos como root..."
  chmod 777 /app  # tmp files de pnpm en /app/_tmp_*
  mkdir -p /app/node_modules
  chown ${UID_RUN}:${GID_RUN} /app/node_modules || true
  echo "[entrypoint] Bajando privilegios a uid=${UID_RUN} gid=${GID_RUN}"
  exec su-exec ${UID_RUN}:${GID_RUN} "$0" "$@"
fi

cd /app

# pnpm 11 exit code 1 si hay build scripts ignorados, aunque allowBuilds este
# bien. Toleramos ese caso especifico (return code 0 si install completo).
echo "Installing monorepo dependencies (pnpm)..."
set +e
pnpm install --frozen-lockfile 2>&1
RC_FROZEN=$?
if [ "$RC_FROZEN" -ne 0 ]; then
  echo "[entrypoint] install --frozen-lockfile fallo (rc=$RC_FROZEN), intentando sin --frozen..."
  pnpm install 2>&1
  RC_FALLBACK=$?
  # rc=1 con ERR_PNPM_IGNORED_BUILDS es tolerable; rc 2+ es real error.
  if [ "$RC_FALLBACK" -ge 2 ]; then
    echo "[entrypoint] pnpm install fallo definitivo (rc=$RC_FALLBACK)" >&2
    exit "$RC_FALLBACK"
  fi
fi
set -e

# Verificar que node_modules tenga las deps necesarias.
if [ ! -d "/app/node_modules/astro" ] && [ ! -d "/app/apps/${APP_NAME}/node_modules" ]; then
  echo "[entrypoint] Reintentando install (sin astro detectado)..."
  pnpm install || true
fi

echo "Starting Astro dev server for apps/${APP_NAME}..."
exec pnpm --filter "@portfolio/${APP_NAME}" run dev --host 0.0.0.0 --port 4321
