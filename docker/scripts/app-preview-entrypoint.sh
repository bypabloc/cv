#!/bin/sh
# Entrypoint para apps Astro en modo preview (build estático + serve).
#
# CORRE COMO ROOT al inicio para fixear permisos, luego cae a user app.

set -e

if [ -z "${APP_NAME:-}" ]; then
  echo "ERROR: APP_NAME no esta definido" >&2
  exit 1
fi

UID_RUN="${UID:-1000}"
GID_RUN="${GID:-1000}"

if [ "$(id -u)" = "0" ]; then
  echo "[entrypoint] Ajustando permisos como root..."
  chmod 777 /app  # tmp files de pnpm en /app/_tmp_*
  mkdir -p /app/node_modules
  chown ${UID_RUN}:${GID_RUN} /app/node_modules || true
  echo "[entrypoint] Bajando privilegios a uid=${UID_RUN} gid=${GID_RUN}"
  exec su-exec ${UID_RUN}:${GID_RUN} "$0" "$@"
fi

cd /app

echo "Installing monorepo dependencies (pnpm)..."
set +e
pnpm install --frozen-lockfile 2>&1
RC=$?
if [ "$RC" -ge 2 ]; then
  echo "[entrypoint] install fallo (rc=$RC), reintentando sin --frozen..."
  pnpm install 2>&1
  RC=$?
  if [ "$RC" -ge 2 ]; then
    echo "[entrypoint] pnpm install fallo definitivo (rc=$RC)" >&2
    exit "$RC"
  fi
fi
set -e

echo "Building apps/${APP_NAME}..."
pnpm --filter "@portfolio/${APP_NAME}" run build

echo "Starting Astro preview for apps/${APP_NAME}..."
exec pnpm --filter "@portfolio/${APP_NAME}" exec astro preview --host 0.0.0.0 --port 4321
