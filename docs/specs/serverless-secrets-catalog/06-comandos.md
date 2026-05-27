# Fase 5 — Comandos: `secrets-status`, `setup-ssm`, `sync-secrets`

> Adapta los comandos existentes al catálogo y agrega comandos de
> observabilidad (`secrets-status`) y sync explícito (`sync-secrets`).

## `serverless setup-ssm` (modificado)

Antes:

```bash
serverless setup-ssm --name=/portfolio/dev/turnstile-secret
# Si no esta en _SSM_PARAMETERS hardcodeado, warning
```

Después:

```bash
# Nombre corto + stage (recomendado, expansion automatica)
serverless setup-ssm --name=turnstile-secret --stage=dev

# Path completo (compatibilidad)
serverless setup-ssm --name=/portfolio/dev/turnstile-secret

# Ambos formatos validados contra el catalogo
```

Validaciones nuevas:

- Si `--name` es nombre corto, expandir contra el catálogo.
- Si `--name` es path completo, parsearlo y verificar que matchee algún
  `spec.path_for(<stage>)` del catálogo. Si no, fallar con sugerencia.
- `ssm_type` y `kms_key_alias` se toman del catálogo (no del flag).

El comando sigue leyendo el valor por stdin (`getpass`) y NO desde el
`.env`. Es para casos puntuales (rotación manual, recovery).

## `serverless sync-secrets` (nuevo)

```bash
serverless sync-secrets --stage=dev --aws-profile=tfs-dev
# Sincroniza TODO el catalogo del stage. Es lo mismo que el sync automatico
# de `deploy`, pero ejecutado standalone.

serverless sync-secrets --stage=dev --dry-run
# Muestra que haria sin tocar SSM. Lista por entrada: [SKIP|PUSH|MISSING].

serverless sync-secrets --stage=dev --only=turnstile-secret,neon-url
# Sincroniza solo los listados.
```

Implementación: alias delgado de `secrets_sync.sync_secrets_to_ssm`.

## `serverless secrets-status` (nuevo)

```bash
serverless secrets-status --stage=dev --aws-profile=tfs-dev

# Output esperado (sin valores):
#
# Catalogo: 6 entradas, stage=dev
#
# Entrada                  .env       SSM       Match  Hash(local)
# ─────────────────────────────────────────────────────────────────
# turnstile-secret         present    present   yes    ab3f
# turnstile-bypass-secret  present    present   yes    18ae
# neon-url                 present    present   no     f81d (SSM=ab3f)
# owner-email              present    present   yes    7e21
# ses-from-address         present    present   yes    4d9c
# ses-from-name            present    absent    -      e5b2
#
# Resumen: 4 sync, 1 mismatch, 1 missing en SSM
# (sin imprimir valores)
```

Flags:

- `--stage=<env>` requerido
- `--aws-profile=<perfil>` para los `aws ssm get-parameter`
- `--format=table|json` (default table)
- `--only=<names>` para filtrar

Útil para:

- Auditar el estado antes de un deploy.
- Detectar drift (alguien cambió el valor en la consola web sin actualizar
  el `.env`).
- Diagnosticar bugs ("la lambda tira `invalid-input-secret` → secrets-status
  dice mismatch → resolver").

## `serverless rotate-secret` (modificado)

Antes lee de stdin + `--confirm`. Después permite también:

```bash
# Rota usando el valor actual del .env (sync forzado)
serverless rotate-secret --name=turnstile-secret --stage=dev \
  --from-env --confirm

# Rota a un nuevo valor pedido por stdin (manual)
serverless rotate-secret --name=turnstile-secret --stage=dev --confirm
```

## `serverless validate-catalog` (nuevo)

```bash
serverless validate-catalog
# Carga Catalog.load(), valida el schema de los 6 YAML.
# Falla si algun YAML esta mal formado.
# Usado por el pre-commit hook (Fase 7).
```

## Archivos afectados

### Crear

- `devtools/serverless/secrets_commands.py` — los 5 comandos
  (setup_ssm, sync_secrets, secrets_status, rotate_secret, validate_catalog)
  - Verificar: tests + invocación CLI manual
- `devtools/tests/serverless/test_secrets_commands.py` — suite
  - Verificar: `pytest devtools/tests/serverless/test_secrets_commands.py`

### Modificar

- `devtools/serverless/main.py` — registrar los nuevos subcomandos
  - Verificar: `serverless --help` los lista
- `devtools/serverless/flags.py` — flags `--stage`, `--only`, `--from-env`,
  `--dry-run` validados
  - Verificar: invocación con flags inválidos falla con mensaje claro
- `devtools/serverless/help.py` — documentar los nuevos comandos
- `devtools/serverless/secrets.py` — `cmd_setup_ssm` consume el catálogo
  - Verificar: `serverless setup-ssm --name=turnstile-secret --stage=dev`
    expande el path correctamente

### Eliminar

- `devtools/serverless/secrets.py:_SSM_PARAMETERS` (líneas 29-54)
  - Verificar: el código que lo consumía ahora usa `Catalog`
- `devtools/serverless/provisioner.py:_SECRETS` (líneas 84-105)
  - Verificar: los tests de provisioner siguen verdes

## Tests TDD

| Test | Cubre AC |
|------|----------|
| `test_setup_ssm_with_short_name_and_stage_expands_path` | AC-9 |
| `test_setup_ssm_with_unknown_short_name_fails_with_suggestion` | AC-2 |
| `test_secrets_status_output_does_not_contain_values` | AC-8, AC-10 |
| `test_secrets_status_table_columns` | AC-8 |
| `test_sync_secrets_dry_run_no_aws_writes` | (negativo) |
| `test_validate_catalog_when_yaml_invalid_fails` | AC-2 |
| `test_rotate_secret_with_from_env_uses_dotenv_value` | (nuevo) |

## Verify-before-done

```bash
# Tests
pytest devtools/tests/serverless/test_secrets_commands.py -v

# Listado del help
python devtools/run.py serverless --help | grep -E '(setup-ssm|sync-secrets|secrets-status|rotate-secret|validate-catalog)'

# secrets-status contra dev real
python devtools/run.py serverless secrets-status --stage=dev --aws-profile=tfs-dev

# validate-catalog
python devtools/run.py serverless validate-catalog
```
