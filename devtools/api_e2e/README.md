# api_e2e — tests E2E reales contra el backend desplegado

> Corre los flujos completos (exito + un par de errores) de cada Lambda
> HTTP del portfolio contra un entorno de DEPLOY real (dev | stage,
> NUNCA prod) via HTTP, midiendo el tiempo de respuesta de cada endpoint.

## Que prueba

Los 5 Lambdas HTTP (`trigger.type=http`):

| Lambda | Exito | Errores |
|--------|-------|---------|
| `cv` | las 10 actions read (GET, 2xx) | action invalida, sin operation |
| `contact_form` | `contact.create` 202 (via bypass Turnstile) | sin message, email invalido |
| `tracking_pixel` | `tracking.track` 202 | sin event_type_id, viewport invalido |
| `auth` | register.start -> verify-code -> refresh -> login.start -> logout | set-password ya seteada (400), email inexistente (404), tokens falsos (4xx/401) |
| `users` | profile.get/update, status.get/list-sessions | admin no-admin (404), sin JWT (401), JWT falso (401) |

Los 3 workers (`*_worker`, SQS) y `db` (direct) NO son invocables por
HTTP — quedan fuera (los cubren sus unit tests).

## Por que NO es parte de `test_runner`

`test_runner` corre en CI/pre-push con entornos Docker (local/dev/test).
`api_e2e` es distinto: **muta el entorno desplegado** (crea users,
contacts, tracking events), **lee secretos de SSM** y **siembra hashes en
Neon**. Por eso es un comando dedicado, opt-in, fuera de la bateria de CI.

## Uso

```bash
# Todos los Lambdas contra dev (requiere SSO activo del perfil)
AWS_PROFILE=tfs-dev python devtools/run.py api_e2e --env=dev --aws-profile=tfs-dev

# Un solo Lambda
python devtools/run.py api_e2e --env=dev --lambda=auth --aws-profile=tfs-dev

# Mas muestras por endpoint read-safe (default 5)
python devtools/run.py api_e2e --env=dev --samples=10 --aws-profile=tfs-dev

# Conservar los datos sinteticos creados (no limpiar Neon)
python devtools/run.py api_e2e --env=dev --keep-data --aws-profile=tfs-dev
```

## Flags

| Flag | Default | Descripcion |
|------|---------|-------------|
| `--env` | `dev` | Entorno de deploy: `dev` o `stage` (NUNCA prod) |
| `--lambda` | (todos) | `cv` / `contact_form` / `tracking_pixel` / `auth` / `users` |
| `--samples` | `5` | Muestras por endpoint read-safe (los pasos mutantes usan menos) |
| `--aws-profile` | (shell) | Perfil AWS CLI para SSM/Neon (ej. `tfs-dev`) |
| `--keep-data` | `false` | No limpiar los datos sinteticos creados |

## Como funciona (detalles)

- **Tiempos**: cada caso se invoca N veces; el reporte separa `cold`
  (1ra muestra) de `warm` (promedio 2..N) y da un promedio global.
- **Datos sinteticos + cleanup**: emails `success+api-e2e-<run>-<slot>@
  simulator.amazonses.com` (SES mailbox simulator: globalmente
  entregable, sin entrega real). Al final borra users/contacts/tracking
  creados en Neon (salvo `--keep-data`).
- **IP rotada**: 1 IP de TEST-NET (RFC 5737) por request para no agotar
  el rate-limit ni auto-blacklistear una IP real.
- **Seed de Neon (auth)**: el code de verify NO vuelve en la respuesta
  (solo el hash SHA-256 va a Neon). El harness genera un plaintext
  conocido, UPDATEa el `code_hash` de la fila vigente y envia el
  plaintext. Connection string resuelta de SSM en proceso (hermetico).
- **Turnstile bypass**: solo `dev` evalua `X-Turnstile-Bypass-Secret`
  (de SSM). En `stage` el bypass es inerte -> los flujos de exito con
  Turnstile (contact/auth) se omiten; los casos de error siguen.

## Hermetico (secretos)

Ningun valor de secreto (bypass, Neon URL) se imprime jamas en
stdout/stderr. Se resuelven via boto3 en proceso y se pasan directo a
httpx/psycopg. Cumple `.claude/rules/env-files.md`.

## Estructura

```text
api_e2e/
├── main.py          # orquesta los flujos + cleanup + reporte
├── flags.py         # validacion de flags + describe()
├── config.py        # URLs/origins por env + IpRotator + emails sinteticos
├── support.py       # HttpClient (httpx + timing) + Response
├── runner.py        # Runner: corre N samples, clasifica PASS/FAIL
├── reporter.py      # CaseResult + tabla de tiempos + veredicto
├── environment.py   # SSM secrets + seed/cleanup en Neon (boto3 + psycopg)
├── flow_readonly.py # cv + contact_form + tracking_pixel
├── flow_auth.py     # flujo auth completo + errores
└── flow_users.py    # profile + status + admin
```
