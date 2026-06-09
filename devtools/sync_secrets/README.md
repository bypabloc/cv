# sync_secrets

> Comando unificado de sincronizacion de las 3 categorias de secretos
> del portfolio. Hermetico: ningun valor en stdout.

## Categorias y destinos

| Categoria | Origen | Destino | Naturaleza |
|---|---|---|---|
| **client** | `docker/env/client/.{env}` | GitHub Environment Variables | publico (PUBLIC_*) — bundle browser |
| **server** | `docker/env/server/.{env}` | AWS SSM (SecureString + KMS) | secreto real — lo lee la Lambda en runtime |
| **dev-cli** | `docker/env/dev-cli/.{env}` | **LOCAL-ONLY** (no sync) | IAM keys del dev local para devtools |

## Uso

```bash
# Sincronizar TODAS las categorias para un env
python devtools/run.py sync_secrets --env=dev --aws-profile=tfs-dev

# Solo una categoria
python devtools/run.py sync_secrets --env=dev --category=client
python devtools/run.py sync_secrets --env=dev --category=server --aws-profile=tfs-dev
python devtools/run.py sync_secrets --env=dev --category=dev-cli

# Dry-run (preview, no toca nada remoto)
python devtools/run.py sync_secrets --env=dev --dry-run --aws-profile=tfs-dev

# Subset de keys (rotacion puntual)
python devtools/run.py sync_secrets --env=prod --category=client \
  --keys=PUBLIC_TURNSTILE_SITEKEY

# Crear GH Environment si no existe (primera vez por env)
python devtools/run.py sync_secrets --env=dev --category=client --create-env
```

## Flags

| Flag | Default | Descripcion |
|---|---|---|
| `--env` | (requerido) | `local` \| `dev` \| `prod` |
| `--category` | `all` | `all` \| `client` \| `server` \| `dev-cli` |
| `--dry-run` | `false` | Reporta sin ejecutar |
| `--keys` | (todas) | CSV de keys a sincronizar (filtra el catalogo activo) |
| `--create-env` | `false` | Crea GH Environment si no existe (solo client) |
| `--aws-profile` | (vacio) | AWS profile (server target). Ej: `tfs-dev` |

## Acciones reportadas

| Accion | Significado | Categoria |
|---|---|---|
| `SKIP` | Valor remoto matchea el local | client, server |
| `PUSH` | Valor remoto difiere; se actualiza | client, server |
| `CREATE` | La variable/parametro no existe; se crea | client |
| `MISSING` | La key esta vacia o ausente | todas |
| `LOCAL-ONLY` | Validado localmente, no se sincroniza | dev-cli |
| `DRY-RUN <X>` | Lo que `--dry-run` reportaria como `X` | client, server |

## Catalogo

- **client**: `devtools/sync_secrets/catalog.py` (`CLIENT_SYNCED_KEYS`)
- **server**: `serverless/lambda/resources/secrets/*.yaml` (fuente de verdad
  declarativa por entrada)
- **dev-cli**: `devtools/sync_secrets/catalog.py` (`DEVCLI_EXPECTED_KEYS`,
  `DEVCLI_OPTIONAL_KEYS`)

## Reglas de seguridad

- **NUNCA** se imprime el valor de una key. Solo `[ACCION] KEY`.
- **NUNCA** se loguea el `.env` completo. El parser entrega un dict
  en memoria que se descarta tras procesar.
- **SIEMPRE** se compara local vs remoto via SHA256 truncado (8 chars)
  antes de hacer PUSH. Hash != valor.
- **SIEMPRE** las keys client publican como GH Environment **Variables**
  (no Secrets). Son publicas por contrato.
- **SIEMPRE** las keys server publican como SSM `SecureString` + KMS.
- **SIEMPRE** las keys dev-cli NO salen del laptop del dev. CI usa OIDC.

## Pre-requisitos

- `gh` CLI autenticado (`gh auth status`) — para target client.
- `aws` CLI autenticado al perfil indicado (`aws sso login --profile <X>`)
  — para target server.
- El GH Environment `<env>` debe existir (o pasar `--create-env`).

## Cuando ejecutarlo

- **Rotacion**: tras cambiar un valor en `docker/env/<cat>/.{env}`.
- **Onboarding env**: primera vez que se despliega a un env nuevo.
- **Auditoria**: con `--dry-run` para detectar drift entre local y remoto.

## Granularidad alternativa

`sync_secrets` es el comando unificado. Si necesitas operar solo el
backend de servidor (caso comun), `serverless sync-secrets --stage=<X>`
sigue siendo accesible y hace lo mismo internamente.
