#!/bin/sh
# Entrypoint para el admin (Next.js SPA) en modo dev (HMR).
#
# CORRE COMO ROOT al inicio:
#   1. Fixea permisos del named volume node_modules (root-owned al primer mount)
#   2. Hace el directorio /app escribible por uid app (para tmp files de pnpm)
#   3. Baja privilegios al user `app` (UID 1000 por default)
#   4. Ejecuta pnpm install + next dev como `app`
#
# A diferencia de las apps Astro (puerto 4321, astro dev), el admin corre
# `next dev` en el puerto 3000 y vive en /app/admin (no bajo apps/).
#
# Variables esperadas:
#   UID/GID  — uid/gid del usuario host (default 1000:1000)

set -e

UID_RUN="${UID:-1000}"
GID_RUN="${GID:-1000}"

# Fix permisos del bind mount y named volumes (ver app-dev-entrypoint.sh).
# pnpm escribe sus _tmp_<n>_<hash> en la raiz del workdir (/app/), por eso
# necesita /app con write para uid app.
if [ "$(id -u)" = "0" ]; then
  echo "[admin-entrypoint] Ajustando permisos como root..."
  chmod 777 /app  # tmp files de pnpm en /app/_tmp_*
  mkdir -p /app/node_modules
  chown ${UID_RUN}:${GID_RUN} /app/node_modules || true
  echo "[admin-entrypoint] Bajando privilegios a uid=${UID_RUN} gid=${GID_RUN}"
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
  echo "[admin-entrypoint] install --frozen-lockfile fallo (rc=$RC_FROZEN), intentando sin --frozen..."
  pnpm install 2>&1
  RC_FALLBACK=$?
  # rc=1 con ERR_PNPM_IGNORED_BUILDS es tolerable; rc 2+ es real error.
  if [ "$RC_FALLBACK" -ge 2 ]; then
    echo "[admin-entrypoint] pnpm install fallo definitivo (rc=$RC_FALLBACK)" >&2
    exit "$RC_FALLBACK"
  fi
fi
set -e

echo "Starting Next.js dev server for admin..."
exec pnpm --filter "@portfolio/admin" run dev --hostname 0.0.0.0 --port 3000
