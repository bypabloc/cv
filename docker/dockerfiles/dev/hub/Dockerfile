# Portfolio: dev (remote) container for apps/hub
# Node 24 (Alpine) + pnpm 11.0.9. HMR via bind mount.
#
# Entrypoint corre como root, fixea permisos del volumen node_modules
# y luego baja privilegios a user `app` via su-exec antes de pnpm.

FROM node:24-alpine

RUN apk add --no-cache su-exec
RUN corepack enable

ARG UID=1000
ARG GID=1000

RUN deluser --remove-home node 2>/dev/null || true \
    && addgroup -g ${GID} app \
    && adduser -u ${UID} -G app -s /bin/sh -D app

WORKDIR /app

# Pre-activar pnpm como usuario app: corepack escribe cache en /home/app/.cache.
RUN mkdir -p /home/app/.cache /home/app/.local/share/pnpm \
    && chown -R app:app /home/app

USER app
RUN corepack prepare pnpm@11.0.9 --activate
USER root

COPY docker/scripts/app-dev-entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENV CI=true
ENV APP_NAME=hub

EXPOSE 4321

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
