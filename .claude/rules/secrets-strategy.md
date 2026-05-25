# Secrets strategy — portfolio (umbrella)

> Politica unificada de gestion de secretos del portfolio. Cubre las 3
> categorias (`client`, `server`, `dev-cli`) y el comando unificado de
> sincronizacion. Esta rule es la entrada: las rules hijas tienen el
> detalle por categoria.

## Activacion

Aplica SIEMPRE que se trabaje con:

- Cualquier archivo en `docker/env/{client,server,dev-cli}/`
- Rotar un secreto / sitekey / API key
- Onboardear un env nuevo (dev/stage/prod) en GH o AWS
- Auditar drift entre `.env` local y los destinos remotos
- Agregar una variable nueva al build/lambda/devtools
- El comando `python devtools/run.py sync_secrets ...`
- Cualquier referencia en CI/CD a `vars.*` o `secrets.*` de GH
- AWS SSM Parameter Store (`/portfolio/*`)
- KMS key `alias/portfolio-lambdas`

## Las 3 categorias (resumen)

| Categoria | Origen | Destino | Tipo en destino | Naturaleza |
|---|---|---|---|---|
| **client** | `docker/env/client/.{env}` | GitHub Environment Variables | Variables (NO Secrets) | publico (PUBLIC_* en bundle browser, URL builders) |
| **server** | `docker/env/server/.{env}` | AWS SSM Parameter Store (us-east-1) | SecureString + KMS `alias/portfolio-lambdas` | secreto real (Turnstile secret, Neon URL, etc.) |
| **dev-cli** | `docker/env/dev-cli/.{env}` | **LOCAL-ONLY (no sync)** | — | IAM keys + API tokens personales del dev para devtools |

## Comando unificado

```bash
# Sincronizar TODAS las categorias para un env
python devtools/run.py sync_secrets --env=dev --aws-profile=tfs-dev

# Una sola categoria
python devtools/run.py sync_secrets --env=dev --category=client
python devtools/run.py sync_secrets --env=dev --category=server --aws-profile=tfs-dev
python devtools/run.py sync_secrets --env=dev --category=dev-cli

# Dry-run (auditoria sin tocar nada)
python devtools/run.py sync_secrets --env=dev --dry-run --aws-profile=tfs-dev

# Rotacion puntual de un valor
python devtools/run.py sync_secrets --env=prod --keys=PUBLIC_TURNSTILE_SITEKEY \
  --category=client

# Crear GH Environment (primera vez por env)
python devtools/run.py sync_secrets --env=stage --category=client --create-env
```

Acciones reportadas: `SKIP` (match) / `PUSH` (update) / `CREATE` (nuevo) /
`MISSING` (vacio en local) / `LOCAL-ONLY` (dev-cli, no sincroniza) /
`ERROR`. Hermetico: ningun valor en stdout, solo hashes SHA256 truncados
(8 chars) para diagnostico.

Granular: `serverless sync-secrets --stage=<X>` sigue accesible para
operar solo el server. `sync_secrets` lo invoca internamente.

## Reglas duras (SIEMPRE / NUNCA)

- **SIEMPRE** la fuente de verdad del valor es `docker/env/<cat>/.{env}`
  (gitignored). Cambios se hacen ahi primero; luego sync.
- **SIEMPRE** usar `sync_secrets` para publicar. NUNCA `gh variable set`
  o `aws ssm put-parameter` a mano (rompe la trazabilidad con el `.env`).
- **SIEMPRE** correr `--dry-run` ante cualquier duda.
- **SIEMPRE** las keys client van como GH Variables (no Secrets) — son
  publicas por contrato.
- **SIEMPRE** las keys server van como SSM `SecureString` + KMS.
- **SIEMPRE** las keys dev-cli quedan en el laptop del dev. CI usa OIDC.
- **NUNCA** leer `.env` con Read tool / `cat` / `source` (ver
  [env-files.md](env-files.md)). Extraer keys puntuales con
  `grep -m1 ^KEY=` cuando sea necesario.
- **NUNCA** marcar PUBLIC_* como GitHub Secret — distorsiona la semantica
  y rompe el debug del deploy.
- **NUNCA** hardcodear un sitekey/endpoint en el workflow yaml o en
  codigo de apps. Va via env vars sincronizadas.
- **NUNCA** sincronizar dev-cli a remoto — son credenciales personales.

## Matriz de decisiones (donde va una key nueva)

| ¿La consume? | ¿Es publica? | Categoria | Destino |
|---|---|---|---|
| El bundle del browser (Astro) | si (PUBLIC_*) | client | GH Variables |
| Una Lambda en runtime | NO (secreto) | server | SSM SecureString + KMS |
| Una Lambda en runtime | si (URL/config) | server | SSM String (no KMS) |
| devtools local (`aws`, `gh`, `neon`) | NO (token del dev) | dev-cli | local-only |
| GitHub Actions runner (OIDC + workflow needs) | varia | server o `gh secret`/`gh variable` directo | depende |

## Cuando ejecutarlo

- **Rotacion**: tras cambiar un valor en cualquier `docker/env/<cat>/.{env}`.
- **Onboarding env**: `--create-env` la primera vez con un env nuevo.
- **Pre-deploy**: si dudas si el remoto esta al dia (dry-run).
- **Post-incident**: si se compromete una key (rotar local + sync).

## Pre-requisitos por categoria

| Categoria | Requisitos |
|---|---|
| client | `gh auth status` ok |
| server | `aws sso login --profile <X>` ok + KMS key existente |
| dev-cli | el `.env` local existe (validacion no-op) |

## Referencias hijas

Para detalle por categoria:

- [client-env-sync.md](client-env-sync.md) — flujo client + ejemplo de
  rotacion de Turnstile sitekey
- [serverless-secrets.md](serverless-secrets.md) — inventario SSM,
  KMS key, IAM scopes por Lambda
- [env-files.md](env-files.md) — politica de NO leer `.env` con Read tool
- [security.md](security.md) — politica general de secretos del repo
- [devtools/sync_secrets/README.md](../../devtools/sync_secrets/README.md)
  — referencia tecnica del comando (flags, catalogos, acciones)

## Anti-patrones

| Anti-patron | Por que | Correccion |
|---|---|---|
| `gh variable set` a mano | Sin trazabilidad con `.env` local | `sync_secrets --category=client` |
| `aws ssm put-parameter` a mano | Mismo problema; sin hash check | `sync_secrets --category=server` |
| Sincronizar dev-cli a GH Secrets | CI usa OIDC; son creds del dev | `--category=dev-cli` reporta LOCAL-ONLY |
| Hardcodear sitekey/endpoint en yaml | Acopla con rotacion | `${{ vars.* }}` del GH Environment |
| Marcar PUBLIC_* como GH Secret | Mascarea en logs, estorba debug | GH Variables |
| Commitear el `.env` | Categoria personal | Esta en `.gitignore` |
| Editar GH/SSM sin actualizar `.env` | Drift entre local y CI | Editar `.env` local primero, despues sync |
| Leer el `.env` completo con Read/cat/source | Vuelca secretos al contexto | `grep -m1 ^KEY=` puntual |
