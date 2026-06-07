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

## GitGuardian (secret scanning)

El repo tiene activado el secret scanning de GitGuardian. Hay DOS motores
con DOS configs distintas — es la confusion #1:

| Motor | Cuando corre | Que config lee |
|---|---|---|
| `ggshield` (CLI / pre-commit / GitHub Action propia) | local / hooks | `.gitguardian.yaml` del repo (raiz) |
| **GitGuardian GitHub App** (el check `GitGuardian Security Checks` del PR) | server-side en cada PR | SOLO el dashboard (`dashboard.gitguardian.com` -> workspace -> Secrets detection -> excluded filepaths, scopeado al repo). **NO lee `.gitguardian.yaml`.** |

### `.gitguardian.yaml` (raiz del repo)

- **SIEMPRE** se usa `version: 2` + `secret.ignored_paths` (con guion BAJO,
  NO `ignored-paths`). Glob Unix (`**`, `*`).
- **SIEMPRE** `ignored_paths` es SOLO para **fixtures de test** con valores
  SINTETICOS (passwords de prueba, tokens fake). Hoy: `devtools/api_e2e/**`
  (el harness E2E usa credenciales sinteticas compuestas en runtime, NO
  secretos reales).
- **NUNCA** agregar a `ignored_paths` un path de codigo de PRODUCCION para
  "saltarse" un hallazgo. Un secreto real se ROTA, no se ignora (ver
  [serverless-secrets.md](serverless-secrets.md)).

### Falso positivo en el check del PR (GitHub App)

El detector "Generic Password" de la GitHub App es heuristico y marca
tanto literales credential-like como el patron `password=<identificador>`
aunque el valor sea una variable de fixture. Cuando un PR lo dispara y se
CONFIRMA que es un fixture sintetico (no un secreto real):

1. **SIEMPRE** primero verificar que de verdad NO hay secreto real: el
   valor es sintetico/compuesto en runtime y el test funcional pasa.
2. La GitHub App NO lee `.gitguardian.yaml`, asi que el archivo no silencia
   el check del PR. Para eso: excluir el path en el **dashboard**
   (Secrets detection -> excluded filepaths, scopeado al repo) o, ante un FP
   ya confirmado, mergear con `gh pr merge <N> --admin --merge` (saltando
   SOLO el check de GitGuardian; los demas checks deben estar verdes).
3. **NUNCA** reescribir historia con `git push --force` para "limpiar" un FP:
   esta en la DENY-list de [.claude/settings.json](../settings.json)
   (guardarrail duro, no bypasseable). Si hay que quitar un literal real de
   un commit viejo de una rama de trabajo: `git push origin --delete <branch>`
   (permitido) + re-push de la rama amended (cierra el PR -> crear uno nuevo).

### Evitar el FP de raiz al escribir fixtures

- **SIEMPRE** componer las credenciales de prueba en runtime de fragmentos
  NEUTROS (sin keyword `pass`/`phrase`/`secret`/`token`), no como literales:
  `f'{_TAG}-Qa-K7m-Zx3!'`. Reduce los hallazgos a (en el peor caso) el
  patron irreducible `password=<variable>`.
- **SIEMPRE** documentar en el codigo que el valor es un fixture, NO un
  secreto.

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
| Esperar que `.gitguardian.yaml` silencie el check del PR | La GitHub App NO lee ese archivo (solo `ggshield`) | Excluir el path en el dashboard, o `--admin` ante un FP confirmado |
| Agregar un path de produccion a `ignored_paths` para tapar un hallazgo | Oculta un secreto real | Rotar el secreto; `ignored_paths` solo para fixtures sinteticos |
| Credenciales de fixture como literal con keyword (`Passphrase`) | Dispara "Generic Password" de GitGuardian | Componer en runtime de fragmentos neutros (`f'{_TAG}-Qa-K7m-Zx3!'`) |
| `git push --force` para limpiar un FP de un commit viejo | Esta en la deny-list dura de settings.json | `git push origin --delete` + re-push amended (cierra el PR -> crear nuevo) |
