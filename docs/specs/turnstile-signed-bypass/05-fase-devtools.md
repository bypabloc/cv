# 05 — Fase 4: devtools (keygen + firmante + helper)

[← 04 services](04-fase-services-cleanup.md) · [Siguiente: Fase 5 →](06-fase-secrets-docs.md)

> Lado cliente: generar los pares Ed25519, firmar tokens en `api_e2e`, y un
> helper para emitir un token a mano. La privada vive SOLO local (`dev-cli`).

## A — keygen Ed25519

Extender `devtools/rotate_secrets/turnstile.py` (o subcomando nuevo
`rotate_secrets turnstile-bypass-key`):

- `generate_keypair()` (de `shared.crypto.ed25519`) para dev y stage.
- Privada (b64) → `TURNSTILE_BYPASS_PRIVATE_KEY` en
  `docker/env/dev-cli/.{dev,stage}` (local-only).
- Pública (b64) → `TURNSTILE_BYPASS_PUBLIC_KEY` en
  `docker/env/server/.{dev,stage}` (para `sync_secrets`/`setup-ssm` → SSM).
- Flags: `--dry-run`, `--rotate`, `--envs=dev,stage`. NUNCA prod.
- NUNCA imprime la privada en stdout (hermético).

> `cryptography` ya es dep transitiva; agregarla a `devtools/pyproject.toml`
> si keygen importa el helper de `shared.crypto`. devtools corre en
> `devtools/.venv` (Python 3.14).

## B — firmante en `api_e2e`

`devtools/api_e2e/support.py`:

- Hoy: `headers['X-Turnstile-Bypass-Secret'] = bypass_secret`.
- Nuevo: leer `TURNSTILE_BYPASS_PRIVATE_KEY` del env activo (extraído con
  `grep -m1 '^TURNSTILE_BYPASS_PRIVATE_KEY=' docker/env/dev-cli/.<env>`,
  NUNCA cargar el `.env` completo), firmar token fresco (stage, exp=now+300),
  mandarlo en `headers['X-Turnstile-Bypass-Token']`.
- Firmar uno por request (o cachear y re-firmar al acercarse a `exp`).
- `flow_auth.py`/`flow_readonly.py`: ya pasan `bypass_secret` a `support`;
  renombrar el parámetro según cómo quede la firma.

## C — helper on-demand (curl)

Subcomando `api_e2e mint-bypass --env=dev` → imprime un token firmado válido
300 s (solo el token, para `curl -H 'X-Turnstile-Bypass-Token: <token>'`).
[AC-9]

## Verificación de la fase

```bash
python devtools/run.py rotate_secrets turnstile-bypass-key --envs=dev,stage --dry-run
python devtools/run.py api_e2e mint-bypass --env=dev
python devtools/run.py test_runner --module=devtools --type=unit
```

[← 04 services](04-fase-services-cleanup.md) · [Siguiente: Fase 5 →](06-fase-secrets-docs.md)
