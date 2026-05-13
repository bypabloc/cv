#!/bin/sh
# Entrypoint compartido para el container `feature` (Playwright E2E).
#
# Container corre con `network_mode: host` (en local/test) o conectado
# a la network nginx (en CI). Para que Playwright pueda resolver
# subdominios `*.localhost`, los agregamos a /etc/hosts.

set -e

# Anadir resolucion de subdominios *.localhost (api, generic, hub, fintech, ...)
if ! grep -q 'hub.localhost' /etc/hosts 2>/dev/null; then
  echo "Adding *.localhost subdomain entries to /etc/hosts..."
  printf '\n127.0.0.1\thub.localhost\n' >> /etc/hosts
  printf '127.0.0.1\tfintech.localhost\n' >> /etc/hosts
  printf '127.0.0.1\tarchitect.localhost\n' >> /etc/hosts
  printf '127.0.0.1\tleader.localhost\n' >> /etc/hosts
  printf '127.0.0.1\tvibe.localhost\n' >> /etc/hosts
  printf '127.0.0.1\tservices.localhost\n' >> /etc/hosts
fi

cd /app/tests/feature

echo "Installing feature test dependencies..."
# --ignore-workspace evita que pnpm escale al monorepo raiz y haga un
# install vacio. tests/feature/ tiene su propio package.json aislado.
pnpm install --ignore-workspace --frozen-lockfile 2>/dev/null \
  || pnpm install --ignore-workspace

echo "Installing Playwright browsers (chromium + webkit)..."
./node_modules/.bin/playwright install chromium webkit

touch /tmp/.feature-ready
echo "Feature container ready."
exec "$@"
