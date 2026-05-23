# Fase 3 — Sync `.env` -> SSM en `deploy`

> Implementa el sync automático que `serverless deploy --stage=<env>`
> ejecuta antes de provisionar/actualizar el Lambda. Hermético: el valor
> nunca aparece en stdout, stderr, logs ni `ps`.

## Flujo del sync

```text
serverless deploy --stage=dev --lambda=contact_form
  -> [1] cargar Catalog desde resources/secrets/*.yaml
  -> [2] cargar .env de docker/env/server/.dev en memoria (sin imprimir)
  -> [3] para cada SecretSpec con `dev` en stages:
       3a) si source_env_var NO esta en el .env y required=true -> fail
       3b) si esta vacio y required=true -> fail
       3c) calcular hash SHA256 del valor
       3d) leer SSM /portfolio/dev/<name> con get-parameter (si existe)
       3e) si hash coincide con SSM actual -> skip (log "OK [SKIP] <path> match")
       3f) si difiere o no existe en SSM -> put-parameter (log "OK [PUSH] <path>")
  -> [4] continuar con provisioner.deploy() normal
```

## Reglas de hermetismo (no-leaking)

1. El `.env` se lee con `python-dotenv` o parser custom, valores quedan en
   un `dict[str, str]` local. NUNCA `print(env_dict)`, NUNCA loggear el
   dict completo.
2. `aws ssm put-parameter --value <valor>` filtra el valor a `ps aux`.
   Alternativa: pasar `--value file:///tmp/portfolio-secret-<rand>` con
   tempfile creado con `tempfile.NamedTemporaryFile(mode='w', delete=False)`
   + `os.chmod(tmp.name, 0o600)` + `tmp.write(value)` + cleanup en `finally`.
3. `aws ssm get-parameter --with-decryption` devuelve el valor en stdout.
   Capturar con `subprocess.run(capture_output=True)`, extraer el valor
   con `json.loads(result.stdout)['Parameter']['Value']`, comparar hash,
   y descartar el dict completo. NUNCA imprimir el resultado raw.
4. Toda exception que envuelva un valor debe filtrar el valor antes de
   propagarse: `try: ... except Exception as e: raise SecretsSyncError(
   f'fallo en {spec.name} stage={stage}') from None` (NOT `from e` si el
   `e` contiene el valor).
5. Logs estructurados con `logger.info('%s %s', tag, name)` — nunca
   `logger.info(f'{name}={value}')`.

## Comparación por hash (idempotencia)

```python
def _hash_value(value: str) -> str:
    """Devuelve SHA256 hex (full) del valor. Usado solo para comparar
    si el SSM esta sincronizado. Nunca se imprime mas que los primeros
    4 chars para debugging visual."""
    import hashlib
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def _needs_update(local_value: str, ssm_value: str | None) -> bool:
    """True si el local difiere del SSM (o SSM no existe)."""
    if ssm_value is None:
        return True
    return _hash_value(local_value) != _hash_value(ssm_value)
```

## Lectura segura del `.env`

```python
def _load_env_file_securely(path: Path) -> dict[str, str]:
    """Carga el .env en memoria sin imprimir valores.

    Usa python-dotenv en modo no-verbose. El dict resultante se pasa
    explicitamente al consumer, nunca se loggea su contenido.
    """
    from dotenv import dotenv_values
    if not path.exists():
        raise SecretsSyncError(
            f'.env del stage no existe: {path} '
            '(crear desde docker/env/server/.example)',
        )
    return dict(dotenv_values(path))
```

Alternativa sin dotenv (zero-dep): parser custom que respete el formato
`KEY=value` con `value` posiblemente entre comillas. python-dotenv ya
está disponible o se agrega como dep de devtools.

## Comando: `serverless deploy` con sync integrado

```python
# devtools/serverless/lifecycle.py — pseudocodigo del cambio
def cmd_deploy(flags: dict[str, Any]) -> int:
    stage = flags['stage']
    lambda_target = flags['lambda']
    skip_sync = flags.get('skip_sync', False)

    if stage == 'local':
        # Local: no sync a SSM, valores van directo al runtime
        return _deploy_local(lambda_target, flags)

    if not skip_sync:
        result = sync_secrets_to_ssm(
            stage=stage,
            env_file=Path(f'docker/env/server/.{stage}'),
            catalog=Catalog.load(),
            aws_profile=flags.get('aws_profile'),
        )
        if result != 0:
            return result

    return _deploy_cloud(stage, lambda_target, flags)
```

## Mensajes de output (sin valores)

```text
$ serverless deploy --stage=dev --lambda=contact_form --aws-profile=tfs-dev

[secrets-sync] cargando catalogo (6 entradas)
[secrets-sync] cargando docker/env/server/.dev
[secrets-sync] turnstile-secret        [SKIP] /portfolio/dev/turnstile-secret hash=ab3f
[secrets-sync] neon-url                [PUSH] /portfolio/dev/neon-url
[secrets-sync] owner-email             [SKIP] /portfolio/owner-email hash=7e21
[secrets-sync] ses-from-address        [SKIP] /portfolio/ses-from-address hash=4d9c
[secrets-sync] ses-from-name           [PUSH] /portfolio/ses-from-name
[secrets-sync] turnstile-bypass-secret [SKIP] /portfolio/dev/turnstile-bypass-secret hash=18ae
[secrets-sync] OK 2 PUSH, 4 SKIP

[deploy] provisioner...
```

`hash=ab3f` son los primeros 4 chars del SHA256 — útiles para detectar
mismatch entre devs ("yo tengo hash ab3f, vos f81d"), inútiles para
recuperar el valor (entropía 16 bits).

## Archivos afectados

### Crear

- `devtools/serverless/secrets_sync.py` — módulo del sync (`sync_secrets_to_ssm`)
  - Verificar: tests + dry-run E2E
- `devtools/tests/serverless/test_secrets_sync.py` — suite TDD con boto3 stubber
  - Verificar: `pytest devtools/tests/serverless/test_secrets_sync.py -v`

### Modificar

- `devtools/serverless/lifecycle.py` — `cmd_deploy` llama `sync_secrets_to_ssm`
  antes de `provisioner.deploy`
  - Verificar: deploy a dev publica los secretos faltantes
- `devtools/serverless/flags.py` — agregar flag `--skip-sync` (bool, default false)
  para `deploy`
  - Verificar: `serverless deploy --help` lo muestra
- `devtools/serverless/help.py` — documentar `--skip-sync`

## Tests TDD

| Test | Cubre AC |
|------|----------|
| `test_sync_when_env_missing_required_key_fails` | AC-6 |
| `test_sync_when_value_matches_ssm_hash_skips_put` | AC-5 |
| `test_sync_when_value_differs_calls_put_parameter` | AC-4 |
| `test_sync_when_ssm_param_not_exists_calls_put_parameter` | AC-4 |
| `test_sync_when_value_in_env_never_appears_in_stdout` | AC-10 |
| `test_sync_when_value_in_env_never_appears_in_stderr` | AC-10 |
| `test_sync_when_value_in_env_never_appears_in_subprocess_args` | AC-10 |
| `test_sync_with_skip_sync_flag_no_aws_calls` | (negativo) |

## Verify-before-done

```bash
# Tests verdes
pytest devtools/tests/serverless/test_secrets_sync.py -v

# Test E2E controlado contra AWS real (manual, opcional)
echo "TURNSTILE_SECRET_KEY=test_dummy_value_123" >> /tmp/test.env
# ... correr sync apuntando a /tmp/test.env y verificar SSM
aws ssm get-parameter --name /portfolio/dev/turnstile-secret \
  --with-decryption --query 'Parameter.Value' --output text \
  --profile tfs-dev

# Hermetismo: no aparece el valor en logs
python -c "
import subprocess
result = subprocess.run(
    ['python', 'devtools/run.py', 'serverless', 'deploy',
     '--stage=dev', '--lambda=contact_form', '--dry-run'],
    capture_output=True, text=True,
)
assert 'test_dummy_value_123' not in result.stdout
assert 'test_dummy_value_123' not in result.stderr
print('OK no leak')
"
```
