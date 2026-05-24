# github_sync

> Sincroniza `docker/env/client/.{env}` -> GitHub Environment Variables
> (dev/stage/prod). Hermetico: ningun valor aparece en stdout.

## Uso

```bash
# Dry-run: ver que cambiaria, sin tocar GH
python devtools/run.py github_sync --env=dev --dry-run

# Sync real
python devtools/run.py github_sync --env=dev

# Crear el GH Environment si no existe (idempotente)
python devtools/run.py github_sync --env=stage --create-env

# Subset de keys
python devtools/run.py github_sync --env=prod --keys=PUBLIC_API_ENDPOINT,BASE_DOMAIN
```

## Flags

| Flag | Default | Descripcion |
|---|---|---|
| `--env` | (requerido) | `dev` \| `stage` \| `prod` |
| `--dry-run` | false | Reporta SKIP/PUSH/CREATE/MISSING sin ejecutar set |
| `--keys` | (todas) | CSV de keys a sincronizar |
| `--create-env` | false | Si el GH Environment no existe, lo crea |

## Catalogo de keys

Las keys que se sincronizan estan en
[catalog.py](catalog.py) (`SYNCED_KEYS`):

| Key | Donde se consume |
|---|---|
| `BASE_DOMAIN` | `site-urls.ts` -> hostnames de los 6 sitios |
| `BASE_SCHEME` | `site-urls.ts` -> http/https |
| `APEX_DOMAIN` | `site-urls.ts` -> apex de `generic` en prod |
| `PUBLIC_API_ENDPOINT` | `TrackingPixel.astro` + `/contact` |
| `PUBLIC_TURNSTILE_SITEKEY` | `/contact` (1 widget por env) |

Las keys solo-locales se ignoran explicitamente (`IGNORED_KEYS`):
`PROXY_PORT`, `BASE_PORT`, `CI`, `TURNSTILE_SITE_KEY`, `TURNSTILE_ENABLED`.

## Reglas de seguridad

- **NUNCA** se imprime el valor de una key. Solo `[ACCION] KEY`.
- **NUNCA** se loguea el `.env` completo. El parser entrega un dict
  en memoria que se descarta tras procesar.
- **SIEMPRE** se compara local vs remoto via SHA256 truncado (8 chars)
  antes de hacer PUSH. Hash != valor.
- **SIEMPRE** las keys publican como GH Environment **Variables**
  (no Secrets) — son publicas por contrato (`PUBLIC_*` o config de
  build).

## Acciones

| Accion | Significado |
|---|---|
| `SKIP` | Valor remoto matchea el local |
| `PUSH` | Valor remoto difiere; se actualiza |
| `CREATE` | La variable no existe en GH; se crea |
| `MISSING` | La key esta vacia en el `.env` local; se omite |
| `DRY-RUN <X>` | Lo que `--dry-run` reportaria como `X` |

## Pre-requisitos

- `gh` CLI instalado y autenticado (`gh auth status`).
- El repo actual debe ser un remote de GitHub (`gh repo view`).
- El GH Environment `<env>` debe existir; o pasar `--create-env`.

## Cuando ejecutarlo

- Despues de rotar `PUBLIC_TURNSTILE_SITEKEY` (cambio del widget Cloudflare).
- Al onboardear un env nuevo (`--create-env` la primera vez).
- Al actualizar cualquier `docker/env/client/.{env}` con una key del catalogo.
- En CI/CD: NO automatizado por defecto — la fuente del valor sigue
  siendo `docker/env/client/` (gitignored), pero podria correr como
  workflow manual `gh workflow run` con permisos elevados.

## Tests

```bash
python devtools/run.py test_runner --module=devtools --type=unit
# O directamente:
devtools/.venv/bin/python -m pytest devtools/tests/unit/src/github_sync/
```

Los tests usan mocks de `gh_client.*` y NUNCA invocan `gh` real. Verifican:

- parser extrae solo keys del catalogo
- idempotencia (segundo run reporta SKIP)
- valor cambia -> PUSH una vez, valor NO aparece en stdout
- gh auth falla -> exit 1 con mensaje claro
- `.env` ausente -> exit 1 con mensaje claro
- `--keys` con key fuera del catalogo -> exit 1
