# api_e2e — tests E2E reales contra el backend desplegado

> Corre los flujos completos (exito + un par de errores) de cada Lambda
> HTTP del portfolio contra un entorno de DEPLOY real (dev | stage,
> NUNCA prod) via HTTP, midiendo el tiempo de respuesta de cada endpoint.

## Que prueba

Los 5 Lambdas HTTP (`trigger.type=http`). El harness ejercita TODO el
dominio auth + el dashboard de cuenta (no solo login), incluyendo MFA,
magic-link GET, cambio de password/email, sesiones y admin:

| Lambda | Exito | Errores |
|--------|-------|---------|
| `cv` | las 10 actions read (GET, 2xx) | action invalida, sin operation |
| `contact_form` | `contact.create` 202 (via bypass Turnstile) | sin message, email invalido |
| `tracking_pixel` | `tracking.track` 202 | sin event_type_id, viewport invalido |
| `auth` | register (start -> verify-code -> refresh -> login.start -> set-password -> logout); **magic-link GET 302** al admin/callback + POST JSON; **login con password** directo + 2-step (verify-password); **MFA TOTP** (setup -> confirm -> login 2FA con verify-totp); **MFA email-code** (setup + list + set-preferred + disable); **recovery codes** (generate -> consume) | set-password ya seteada (400), email inexistente (404), magic-link token falso (JSON 400), password incorrecta (401), confirm/verify-totp code malo (400/401), recovery code reusado (400), tokens falsos (4xx/401), mfa/webauthn sin JWT (401) |
| `users` | profile.get/update, status.get/list-sessions; **change-password**; **status.revoke-session** (revoca otra sesion); **change-email** completo (change-email -> confirm-email-change -> verifica email en Neon); **admin.*** completo (list/get/disable/enable/force-logout/list-actions/delete con un admin promovido temporalmente en SSM); **delete-account** (verifica soft-delete en Neon) | change-password current incorrecta (401), admin no-admin (404), sin JWT (401), JWT falso (401) |

Los Lambdas direct (`send_email`, `tracking_writer`, `db`) NO son
invocables por HTTP — quedan fuera (los cubren sus unit tests).

### Como prueba MFA + magic-link sin email ni authenticator

- **TOTP**: `setup-totp` devuelve el `secret_b32` en claro; el harness
  genera el code de 6 digitos localmente con `api_e2e.totp` (RFC 6238
  stdlib, verificado contra `pyotp`) — sin necesidad de un authenticator.
- **magic-link / email-change**: el token plano NUNCA vuelve (solo viaja
  por email; en Neon va el hash SHA-256). El harness genera un plaintext
  conocido y reescribe el `token_hash` de la fila vigente
  (`auth_magic_links`), igual que el seed del code de verify.
- **admin**: el scope `admin.*` exige el email del caller en la whitelist
  SSM `/portfolio/{stage}/admin-emails`, cacheada por contenedor (TTL
  300s). El harness APPENDea un email sintetico al CSV, fuerza un cold
  start del Lambda `users` (env var efimera -> recicla el contenedor ->
  cache fresco) y al final RESTAURA el CSV exacto + borra la env var.
  NUNCA toca el admin real de la whitelist.

## Por que NO es parte de `test_runner`

`test_runner` corre en CI/pre-push con entornos Docker (local/dev/test).
`api_e2e` es distinto: **muta el entorno desplegado** (crea users,
contacts, tracking events), **lee secretos de SSM** y **siembra hashes en
Neon**. Por eso es un comando dedicado, opt-in, fuera de la bateria de CI.

## Uso

Requiere SSO activo del perfil: `aws sso login --profile tfs-dev`.

```bash
# Todos los Lambdas contra dev
python devtools/run.py api_e2e --env=dev --aws-profile=tfs-dev

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

- **Tiempos**: el cold start es POR-LAMBDA (lo paga solo el PRIMER invoke
  del contenedor). El reporte lo agrupa por Lambda: el bloque
  `COLD START POR LAMBDA` lista un cold por Lambda (la 1ra muestra de su
  primer caso) y la tabla `TIEMPOS POR CASO` muestra ese cold solo en el
  primer caso de cada Lambda (`-` en el resto, que ya corren calientes).
  El `warm` de un caso es el promedio de sus muestras calientes: del primer
  caso del Lambda son las muestras 2..N; del resto, TODAS sus muestras. El
  `GLOBAL` promedia el cold por Lambda (no por caso) y el warm por caso.
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
- **Turnstile bypass**: `dev` y `stage` evaluan `X-Turnstile-Bypass-Token`
  (token Ed25519 firmado). El harness firma el token localmente con la
  clave privada de `docker/env/dev-cli/.{env}` (la genera
  `bypass_token keygen`); el backend lo verifica con la clave PUBLICA de
  SSM. `prod` NUNCA acepta bypass. Si falta la clave privada local, los
  flujos de exito con Turnstile (contact/auth) se omiten; los casos de
  error siguen.

## Hermetico (secretos)

Ningun valor de secreto (bypass, Neon URL) se imprime jamas en
stdout/stderr. Se resuelven via boto3 en proceso y se pasan directo a
httpx/psycopg. Cumple `.claude/rules/env-files.md`.

## Estructura

```text
api_e2e/
├── main.py            # orquesta los flujos + cleanup + reporte
├── flags.py           # validacion de flags + describe()
├── config.py          # URLs/origins por env + IpRotator + emails sinteticos
├── support.py         # HttpClient (httpx + timing, GET no-redirect) + Response
├── runner.py          # Runner: corre N samples, clasifica PASS/FAIL
├── reporter.py        # CaseResult + tabla de tiempos + veredicto
├── environment.py     # SSM secrets + seed/cleanup Neon + admin promote + blacklist cleanup
├── totp.py            # generador TOTP RFC 6238 (stdlib, == pyotp)
├── _auth_support.py   # helpers compartidos auth (register active, field)
├── flow_readonly.py   # cv + contact_form + tracking_pixel
├── flow_auth.py       # register + login (passwordless/magic-link/password)
├── flow_auth_mfa.py   # MFA: TOTP, email-code, recovery codes
├── flow_users.py      # profile + status + change-email + delete-account
└── flow_admin.py      # admin.* con promote/restore de la whitelist SSM
```
