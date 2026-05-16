# Docker - Portfolio

> Orquestación multi-ambiente para las 6 apps Astro del portfolio + nginx.

## Ambientes

| Ambiente | Puerto Nginx | Modo Astro | Uso |
| -------- | ------------ | ---------- | --- |
| local    | 9970         | `pnpm dev` (HMR) | Desarrollo con hot reload |
| dev      | 9971         | `pnpm dev` (HMR, code baked) | Desarrollo remoto |
| test     | 9972         | `pnpm build` + `preview` | E2E tests aislados |
| prod     | 9973         | `pnpm build` + `preview` | Build de producción |

## Mapping de subdominios (todos los ambientes)

| Subdominio          | App         | Equivalente en producción       |
| ------------------- | ----------- | ------------------------------- |
| `localhost`         | apps/generic   | the-full-stack.com           |
| `hub.localhost`     | apps/hub       | hub.the-full-stack.com       |
| `fintech.localhost` | apps/fintech   | fintech.the-full-stack.com   |
| `architect.localhost` | apps/architect | architect.the-full-stack.com |
| `leader.localhost`  | apps/leader    | leader.the-full-stack.com    |
| `vibe.localhost`    | apps/vibe      | vibe.the-full-stack.com      |
| `services.localhost` | indice HTML  | (solo local — lista servicios) |

## Estructura

```
docker/
├── dockerfiles/{env}/{app}/Dockerfile  # Dockerfile por ambiente y app
├── dockerfiles/{env}/feature/Dockerfile # Playwright shared (solo local/test)
├── docker-compose/{env}.yml             # Compose por ambiente
├── nginx/{env}.conf                     # Nginx config por ambiente
├── nginx/error-pages/                   # Páginas de error HTML
├── nginx/services-page/                 # Indice estático de servicios.localhost
├── env/{client,server,dev-cli}/          # Variables por categoria de sensibilidad
│   ├── .example                          # Template por categoria (versionado)
│   └── .{env}                            # Variables por ambiente (gitignored)
└── scripts/                             # Entrypoint scripts
```

### Variables de entorno por categoria

Las env vars se reparten en 3 categorias segun sensibilidad, una subcarpeta
por categoria en `docker/env/`:

- `client` — valores publicos: `PUBLIC_*`, puertos, dominios. Acaban en el
  bundle del browser. Sensibilidad: ninguna.
- `server` — config del backend serverless + secretos de runtime (`DB_URL`,
  secret keys). Sensibilidad: alta.
- `dev-cli` — credenciales del devtools CLI (AWS, Neon API key, Cloudflare
  token). Sensibilidad: alta.

Cada categoria tiene su `.example` versionado y sus `.{env}` gitignored. Los
secretos NO van crudos en los archivos: viven en AWS SSM Parameter Store
(ver `.claude/rules/neon-management.md` y `.claude/rules/security.md`).

## Inicio rápido

```bash
# 1. Copiar el .example de CADA categoria al ambiente deseado (ej. local).
#    Hay que copiar los 3 — uno por categoria.
cp docker/env/client/.example  docker/env/client/.local
cp docker/env/server/.example  docker/env/server/.local
cp docker/env/dev-cli/.example docker/env/dev-cli/.local

# 2. Build + start (local con HMR). Se pasan los 3 --env-file:
docker compose --project-name portfolio \
  -f docker/docker-compose/local.yml \
  --env-file docker/env/client/.local \
  --env-file docker/env/server/.local \
  --env-file docker/env/dev-cli/.local \
  up -d --build

#    O simplemente: pnpm run docker:up  (ya incluye los 3 --env-file)

# 3. Acceder
# Generic:    http://localhost:9970
# Hub:        http://hub.localhost:9970
# Fintech:    http://fintech.localhost:9970
# Architect:  http://architect.localhost:9970
# Leader:     http://leader.localhost:9970
# Vibe:       http://vibe.localhost:9970
# Servicios:  http://services.localhost:9970

# 4. Logs
docker compose -p portfolio -f docker/docker-compose/local.yml logs -f

# 5. Stop
docker compose -p portfolio -f docker/docker-compose/local.yml down
```

## Servicios

| Servicio   | Imagen        | Descripción |
| ---------- | ------------- | ----------- |
| nginx      | nginx:alpine  | Reverse proxy + subdominios |
| generic    | node:24-alpine | Astro 6 dev/preview server |
| hub        | node:24-alpine | Astro 6 dev/preview server |
| fintech    | node:24-alpine | Astro 6 dev/preview server |
| architect  | node:24-alpine | Astro 6 dev/preview server |
| leader     | node:24-alpine | Astro 6 dev/preview server |
| vibe       | node:24-alpine | Astro 6 dev/preview server |
| feature    | node:24-slim   | Playwright (solo profile feature) |

## Profiles

- **default** — nginx + las 6 apps Astro
- **feature** — agrega el container `feature` con Playwright (chromium + webkit)

Levantar feature tests:

```bash
docker compose -p portfolio -f docker/docker-compose/local.yml \
  --profile feature up -d --build
docker compose -p portfolio -f docker/docker-compose/local.yml \
  exec feature pnpm test
```

## Notas

- Node 24 (Alpine) + pnpm 11.0.9 (via corepack) en todos los containers
- Las 6 apps exponen puerto 4321 internamente. Solo nginx pública al host
- En **local** y **dev**: bind mount del codigo fuente -> HMR funciona
- En **test** y **prod**: `pnpm build` + `pnpm preview` (sin bind mount, sin HMR)
- `/etc/hosts` no requiere entradas: `*.localhost` resuelve a 127.0.0.1 por RFC
