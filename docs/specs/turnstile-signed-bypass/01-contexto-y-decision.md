# 01 — Contexto y decisión

[← README](README.md) · [Siguiente: Fase 1 →](02-fase-shared-crypto.md)

## 1. Contexto / Problema

El backend serverless usa un **bypass de Turnstile** para que los tests E2E
(y dev local) puedan ejercitar endpoints protegidos por CAPTCHA
(`contact.create`, `auth.register.start`, `auth.login.start`) sin un widget
real.

Hoy (`serverless/lambda/shared/http/turnstile.py`):

- El cliente manda el header `X-Turnstile-Bypass-Secret: <secreto>`.
- `http_dispatch` lo inyecta en `data._meta.bypass_secret`.
- `verify_turnstile_token`, si `cf_response` viene vacío y `STAGE in
  {dev,local}`, compara el header contra un secreto de SSM
  (`/portfolio/<stage>/turnstile-bypass-secret`).
- Si coincide → CAPTCHA considerado válido.

### Hallazgos de exploración

- Es un **secreto fijo compartido**: el mismo valor viaja en cada request y
  vive idéntico en SSM y en el cliente. Si se filtra sirve para siempre.
- La comparación usa `!=` (no constant-time) — timing leak menor.
- Lo consumen: `contact_form` y `auth`. `tracking_pixel` y `cv` declaran
  `bypass_secret` en `_meta` pero **no validan Turnstile** → campo muerto.

## 2. Solución propuesta

Reemplazar el secreto fijo por un **token efímero firmado con Ed25519**.

- El **firmante** (runner E2E / dev) tiene la clave **privada** y emite un
  token corto: `payload = {v:1, iat, exp, jti, stage}`, `token =
  b64url(payload_json).b64url(Ed25519_sign(payload_b64))`.
- El **verificador** (Lambda) tiene SOLO la clave **pública** (SSM, String).
  Valida: firma correcta + `now < exp` + `payload.stage == STAGE`.

### Decisiones clave

- **Ed25519 (no HMAC)** — la nube no puede forjar (solo pública).
- **`shared.crypto` nuevo** — no arrastra `cryptography` a `tracking_pixel`/`cv`.
- **Import lazy de `cryptography`** — prod no paga cold start.
- **Corte limpio** — sin doble-path; se borra el secreto viejo y su SSM param.
- **Stateless (solo `exp`)** — sin store de nonce; 300 s de ventana.

## 3. Criterios de aceptación (AC)

- **AC-1**: Given `STAGE=prod`, When llega `X-Turnstile-Bypass-Token` con
  `cf_response` vacío, Then `CAPTCHA_INVALID` (bypass NUNCA en prod).
- **AC-2**: Given `STAGE=dev` y token Ed25519 válido, When llega a
  `contact.create`/`register.start`/`login.start` con `cf_response` vacío,
  Then se acepta (`bypassed=true`).
- **AC-3**: Given firma inválida, When llega en dev, Then `CAPTCHA_INVALID` +
  log SIN el token.
- **AC-4**: Given `exp < now`, When llega en dev, Then se rechaza.
- **AC-5**: Given `payload.stage != STAGE`, When llega, Then se rechaza.
- **AC-6**: Given el env/SSM del Lambda (solo pública), When un atacante lo
  lee, Then no puede construir un token aceptado.
- **AC-7**: Given el keygen para dev y stage, When se ejecuta, Then genera 2
  pares Ed25519, escribe la privada (b64) en `docker/env/dev-cli/.{dev,stage}`
  y la pública para SSM, sin imprimir la privada en stdout.
- **AC-8**: Given `api_e2e` con la privada local, When firma un token, Then
  `flow_auth` y `flow_readonly` pasan el CAPTCHA por bypass.
- **AC-9**: Given el helper de emisión on-demand, When se invoca, Then imprime
  un token firmado válido 300 s (uso en `curl`).
- **AC-10**: Given `tracking_pixel` y `cv`, When se inspecciona su `_meta`,
  Then ya no declaran `bypass_secret`/`bypass_token`.
- **AC-11**: Given el código tras el corte, When se busca
  `turnstile-bypass-secret`/`TURNSTILE_BYPASS_SECRET`/la comparación de
  secreto fijo, Then no hay referencias.
- **AC-12**: Given `lint-deps` y el packaging, Then `tracking_pixel`/`cv` NO
  vendorizan `cryptography` (solo `contact_form` + `auth`).
- **AC-13**: Given el verificador, When compara valores sensibles, Then usa
  comparación constant-time (no `!=` sobre secretos).

## 4. Diagrama de flujo (antes / después)

### Antes

```text
cliente --X-Turnstile-Bypass-Secret: SECRETO--> http_dispatch
  -> _meta.bypass_secret -> verify_turnstile_token(cf='', bypass_secret)
       if STAGE in {dev,local} and bypass_secret == SSM_SECRET:  -> OK
```

### Después

```text
firmante (E2E/dev, clave PRIVADA) --firma--> token = payload.sig
cliente --X-Turnstile-Bypass-Token: TOKEN--> http_dispatch
  -> _meta.bypass_token -> verify_captcha_or_bypass(cf='', bypass_token)
       if STAGE in {dev,local}:
         pub = SSM_PUBLIC_KEY (solo pública)
         Ed25519.verify(pub, sig, payload)  +  now < exp (300s)
         and payload.stage == STAGE
           -> OK (bypassed)
       else: -> CAPTCHA real (Cloudflare siteverify)
```

## 5. Diagrama ER

N/A — no hay cambios en base de datos (el bypass es stateless).

## 6. Tests requeridos

### 6.A TDD flows (lógica nueva en `shared.crypto`)

- WHEN firma payload `{stage:'dev',exp:now+300}` con privada y verifica con
  pública THEN `verify_bypass_token` ok [AC-2]
- WHEN se altera 1 byte de la firma THEN verify falla [AC-3]
- WHEN `exp < now` THEN verify falla [AC-4]
- WHEN `payload.stage != STAGE` THEN verify falla [AC-5]
- WHEN token malformado (sin `.`, b64 inválido) THEN verify falla controlado [AC-3]

### 6.B Unit tests

- Mirror en `shared/tests/unit/shared/crypto/`.
- Mirror en `contact_form`/`auth` (orquestador: prod rechaza [AC-1], dev
  acepta token válido [AC-2]).
- `tracking_pixel`/`cv` ajustados a `_meta` sin `bypass_*` [AC-10].
- Asserts EXACTOS. Coverage >=80% per-file.

### 6.C Typecheck

- Gate Python: `ruff` + tests. Frontend no se toca.

### 6.D E2E (real, vía `devtools/api_e2e`)

- `flow_auth` + `flow_readonly` contra dev con token firmado local [AC-8].

[← README](README.md) · [Siguiente: Fase 1 →](02-fase-shared-crypto.md)
