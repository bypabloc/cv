# Portfolio: local feature tests (Playwright + chromium + webkit)
# Stays alive; tests triggered via `docker compose exec feature pnpm test`.

FROM node:24-slim

RUN corepack enable && corepack prepare pnpm@11.0.9 --activate

# Playwright system deps for Chromium AND WebKit.
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Chromium deps
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
    libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
    libgbm1 libpango-1.0-0 libcairo2 libasound2 libatspi2.0-0 \
    # WebKit base
    libwoff1 libvpx7 libevent-2.1-7 libopus0 libgstreamer1.0-0 \
    libgstreamer-plugins-base1.0-0 libgstreamer-gl1.0-0 \
    libgstreamer-plugins-bad1.0-0 libflite1 libwebpdemux2 \
    libavif15 libharfbuzz-icu0 libwebpmux3 libenchant-2-2 \
    libsecret-1-0 libhyphen0 libmanette-0.2-0 libgles2 \
    gstreamer1.0-libav \
    # WebKit additional (libgtk-4 + accel/xml libs)
    libgtk-4-1 libgraphene-1.0-0 libatomic1 libxslt1.1 \
    # Common
    fonts-liberation fonts-noto-color-emoji fonts-unifont \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/tests/feature

COPY docker/scripts/feature-entrypoint.sh /usr/local/bin/feature-entrypoint.sh
RUN chmod +x /usr/local/bin/feature-entrypoint.sh

ENTRYPOINT ["/usr/local/bin/feature-entrypoint.sh"]
CMD ["tail", "-f", "/dev/null"]
