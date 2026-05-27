# Client env sync — politica del flujo

> Sincronizar `docker/env/client/.{env}` a GitHub Environment Variables
> (dev/stage/prod). NO editar GH Variables a mano; usar el script
> hermetico de devtools. Las keys del client son PUBLIC_* — Variables,
> nunca Secrets.
>
> **Rule hija de [secrets-strategy.md](secrets-strategy.md)** (umbrella
> que cubre las 3 categorias: client / server / dev-cli). Esta rule
> tiene el detalle del flujo client.

## Activacion

Aplica SIEMPRE que se trabaje con:

- Rotar `PUBLIC_TURNSTILE_SITEKEY` (cambio del widget Cloudflare).
- Agregar una `PUBLIC_*` nueva que el build deba consumir.
- Onboardear un env nuevo en GitHub (dev / stage / prod).
- Editar valores en `docker/env/client/.{dev,stage,prod}` que afecten el build.
- Inspeccionar/debuggear el deploy de las 6 apps a Cloudflare Pages.

## Reglas duras (SIEMPRE / NUNCA)

- **SIEMPRE** las keys del client se publican como GitHub Environment
  **Variables**, NUNCA Secrets. Son publicas (`PUBLIC_*` acaban en el
  bundle JS; `BASE_DOMAIN`/`APEX_DOMAIN`/`BASE_SCHEME` son config
  visible). Marcarlas como Secrets las mascarea en logs y estorba el
  debug.
- **SIEMPRE** la fuente del valor es `docker/env/client/.{env}` (local,
  gitignored). Cambios se hacen ahi primero; luego sync.
- **SIEMPRE** ejecutar `python devtools/run.py sync_secrets --env=<X> --category=client`
  desde el repo root. NUNCA `gh variable set` a mano (rompe la
  trazabilidad con el `.env` local).
- **SIEMPRE** correr `--dry-run` primero ante cualquier duda. El script
  reporta SKIP/PUSH/CREATE/MISSING sin imprimir valores.
- **NUNCA** copiar el contenido del `.env` al chat, a un mensaje de
  commit, ni a un workflow yaml. Ver [env-files.md](env-files.md).
- **NUNCA** hardcodear un sitekey/endpoint en el workflow yaml. Va via
  `${{ vars.* }}` del GH Environment.

## Comandos canonicos

```bash
# Dry-run (no toca GH)
python devtools/run.py sync_secrets --env=dev --category=client --dry-run

# Sync real
python devtools/run.py sync_secrets --env=dev --category=client

# Crear el GH Environment si no existe (primera vez por env)
python devtools/run.py sync_secrets --env=stage --category=client --create-env

# Subset (rotacion puntual de Turnstile)
python devtools/run.py sync_secrets --env=prod --category=client --keys=PUBLIC_TURNSTILE_SITEKEY
```

## Catalogo de keys sincronizadas

Definido en [devtools/sync_secrets/catalog.py](../../devtools/sync_secrets/catalog.py).
Solo las que afectan el build de las 6 apps:

| Key | Donde se consume |
|---|---|
| `BASE_DOMAIN` | `site-urls.ts` -> hostnames de los 6 sitios |
| `BASE_SCHEME` | `site-urls.ts` -> http/https |
| `APEX_DOMAIN` | `site-urls.ts` -> apex de `generic` en prod |
| `PUBLIC_API_ENDPOINT` | `TrackingPixel.astro` + `/contact` |
| `PUBLIC_TURNSTILE_SITEKEY` | `/contact` (1 widget por env) |

Las solo-locales se ignoran explicitamente: `PROXY_PORT`, `BASE_PORT`,
`CI`, `TURNSTILE_SITE_KEY` (duplicada), `TURNSTILE_ENABLED`.

## Rotacion de Turnstile sitekey

Cuando se regenera el widget Cloudflare:

1. Copiar el nuevo sitekey al `docker/env/client/.{env}` correspondiente
   (extraer la KEY puntual; nunca abrir el `.env` completo).
2. `python devtools/run.py sync_secrets --env=<X> --category=client --keys=PUBLIC_TURNSTILE_SITEKEY`.
3. Re-deployar las 6 apps del env: empujar a la branch (`dev`/`stage`/
   `main`) o `gh workflow run deploy-apps.yml --ref <branch>`.
4. El widget secret (server-side) se rota aparte via `serverless setup-ssm`
   — ver [serverless-secrets.md](serverless-secrets.md).

## Anti-patrones

| Anti-patron | Por que | Correccion |
|---|---|---|
| `gh variable set` a mano | Sin trazabilidad con `.env` local | `python devtools/run.py sync_secrets --category=client` |
| Marcar PUBLIC_* como GH Secret | Mascarea en logs, estorba debug | Usar GH Environment Variables |
| Hardcodear sitekey en `deploy-apps.yml` | Acopla con rotacion del widget | `${{ vars.PUBLIC_TURNSTILE_SITEKEY }}` |
| Commitear el `.env` | Categoria client es local | Esta en `.gitignore` |
| Editar valor en GH UI sin actualizar `.env` | Drift entre local y CI | Editar `.env` local primero, despues sync |

## Referencias

- [devtools/sync_secrets/README.md](../../devtools/sync_secrets/README.md)
- [.claude/rules/env-files.md](env-files.md) — NUNCA leer `.env`; extraer
  keys puntuales
- [.claude/rules/serverless-secrets.md](serverless-secrets.md) — el
  hermano server-side (SSM en vez de GH)
- [cloudflare/pages-config.md](../../cloudflare/pages-config.md) — tabla
  de vars por env y deploy flow
