#!/bin/sh
# Entrypoint para el admin (Next.js SPA) en modo preview (build estatico +
# serve del directorio out/).
#
# CORRE COMO ROOT al inicio para fixear permisos, luego cae a user app.
#
# A diferencia de las apps Astro (astro build + astro preview, puerto 4321),
# el admin hace `next build` (NODE_ENV=production, output: 'export' -> out/)
# y sirve el estatico con `serve out -p 3000`.

set -e

UID_RUN="${UID:-1000}"
GID_RUN="${GID:-1000}"

if [ "$(id -u)" = "0" ]; then
  echo "[admin-entrypoint] Ajustando permisos como root..."
  chmod 777 /app  # tmp files de pnpm en /app/_tmp_*
  mkdir -p /app/node_modules
  chown ${UID_RUN}:${GID_RUN} /app/node_modules || true
  echo "[admin-entrypoint] Bajando privilegios a uid=${UID_RUN} gid=${GID_RUN}"
  exec su-exec ${UID_RUN}:${GID_RUN} "$0" "$@"
fi

cd /app

echo "Installing monorepo dependencies (pnpm)..."
set +e
pnpm install --frozen-lockfile 2>&1
RC=$?
if [ "$RC" -ge 2 ]; then
  echo "[admin-entrypoint] install fallo (rc=$RC), reintentando sin --frozen..."
  pnpm install 2>&1
  RC=$?
  if [ "$RC" -ge 2 ]; then
    echo "[admin-entrypoint] pnpm install fallo definitivo (rc=$RC)" >&2
    exit "$RC"
  fi
fi
set -e

echo "Building admin (next build, output export)..."
pnpm --filter "@portfolio/admin" run build

echo "Starting static preview for admin (serve out/)..."
exec pnpm --filter "@portfolio/admin" run preview
