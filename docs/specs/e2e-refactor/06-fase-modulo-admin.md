# 06 — Fase D: `tests/admin/` (browser, flujos completos)

[<- 05 modulo api](05-fase-modulo-api.md) | [Siguiente: 07 modulo app ->](07-fase-modulo-app.md)

> Porta los 7 specs `tests/feature/admin/*.spec.ts` a playwright-python en
> `tests/admin/`, contra `admin.portfolio.{env}.the-full-stack.com`
> desplegado. El usuario pidio "levantar todos los flujos, hacer click a
> todo lo necesario, llenar formularios, loguear, desloguear, terminar
> flujos enteros". Auth REAL: bypass Turnstile + seed Neon (AC-2). Requiere
> el container `e2e` (browser).

## D.1 — Estrategia de auth REAL end-to-end

Los specs TS actuales eran SMOKE (la mayoria solo validaban redirect/SPA
fallback; solo 01/02 tocaban el backend). El pedido EXPANDE el alcance a
flujos completos. Cada flujo del admin se ejercita en el browser usando la
maquinaria de `tests/shared`:

```text
register completo:
  1. install_bypass(page, bypass_token)
  2. goto(admin/register), fill(email sintetico), click(submit)
  3. backend register.start 200 -> navega a /verify?flow=register
  4. seed_code() en Neon (shared.db) para el code de 6 chars
  5. fill(code), submit -> tokens -> redirect al shell autenticado
  6. assert: esta logueado (URL del shell, no /login)

login con magic-link (UI real):
  1. login.start (form) -> el backend manda el magic link (no llega email)
  2. el harness reconstruye la URL del callback con un token seedeado
     (seed_magic_link) y navega a /callback#access=...&refresh=...
  3. assert: redirige al shell autenticado

logout:
  1. estando logueado, click en logout
  2. assert: redirige a /login + tokens limpiados de localStorage

settings update:
  1. logueado, goto(/settings), fill(display_name), submit
  2. assert: toast de exito + display_name persiste (reload)

sessions-mgmt revoke:
  1. logueado con 2 sesiones (segunda via API), goto(/sessions),
     click revoke en la OTRA sesion
  2. assert: la sesion revocada desaparece (NO revoke de la actual)

MFA TOTP (opcional, fase final):
  1. logueado, setup-totp -> secret_b32 (UI lo muestra como QR)
  2. el harness genera el code con shared.totp, confirm
  3. logout + login -> pide 2FA -> code TOTP -> logueado
```

## D.2 — Archivos

| Archivo | Porta de | Alcance ampliado |
|---------|----------|------------------|
| `tests/admin/conftest.py` | fixtures index.ts | `browser`, `page`, `bypass`, `environment`, `logged_in_page` (fixture que loguea un user via flujo real) |
| `tests/admin/test_login_magic_link.py` | 01-login | login UI + magic-link real (seed) + email no registrado 404 |
| `tests/admin/test_register_verify.py` | 02-register | register UI + verify-code real (seed) + navegacion a /verify |
| `tests/admin/test_callback_fragment.py` | 03-callback | callback sin fragment / fragment invalido -> /login (client-side) |
| `tests/admin/test_auth_guard.py` | 04-auth-guard | /settings,/sessions,/users sin sesion -> /login?next= |
| `tests/admin/test_logout.py` | 05-logout | logout UI real + multi-tab (2 contexts) + SPA fallback |
| `tests/admin/test_settings_profile.py` | 06-settings | smoke route + update display_name REAL (logged_in_page) |
| `tests/admin/test_sessions_revoke.py` | 07-sessions | smoke route + revoke de otra sesion REAL (logged_in_page) |
| `tests/admin/test_mfa.py` | (nuevo) | setup TOTP + login 2FA real (puede ir en fase posterior) |

## D.3 — Selectores (del inventario)

Conservar los `data-testid` existentes (el admin Next.js no cambia):
`login-email`, `login-submit`, `register-email`, `register-submit`, roles
`heading`/`alert`/`button`. El `testIdAttribute` de playwright-python se
configura a `data-testid` (equivalente al config TS).

## D.4 — WebKit skip / CORS

Los specs TS saltaban WebKit headless por CORS preflight cross-origin en el
container. En playwright-python contra dev/stage (URLs reales con CORS
correcto del backend), reevaluar: si el CORS del backend dev acepta el
origin del admin, WebKit deberia funcionar. Si no, replicar el skip por
browser. Default: correr **chromium** (como prioriza el TS); webkit opcional.

## D.5 — Multi-tab logout (05)

`page.context().new_page()` o un segundo `browser_context` para simular dos
tabs; el logout en una via BroadcastChannel/`storage` event debe propagar.
Si es fragil contra desplegado, degradar a verificar el `storage` event
directamente (como el TS, que delega el detalle a unit tests).

## D.6 — Auth duro (AC-6)

`--module=admin` exige SSO + clave bypass (los flujos reales no funcionan
sin ellos). Sin credenciales -> exit error (NO skip). La validacion vive en
`e2e/main.py` (fase B).

## Verificacion de la fase D

```bash
python devtools/run.py e2e --module=admin --env=dev --aws-profile=tfs-dev
# debug local con browser visible:
python devtools/run.py e2e --module=admin --env=dev --headed --aws-profile=tfs-dev
```

## Done de la fase D

- [ ] Los 7 specs admin portados a playwright-python.
- [ ] Flujos REALES end-to-end: register, login (form+magic-link),
      logout, settings update, sessions revoke (no solo smoke).
- [ ] MFA TOTP cubierto (al menos setup + login 2FA) — o diferido y anotado.
- [ ] `e2e --module=admin --env=dev` exit 0 con PASS.
- [ ] Datos sinteticos creados se limpian (cleanup).
- [ ] Falla duro sin SSO/clave (AC-6).

[<- 05 modulo api](05-fase-modulo-api.md) | [Siguiente: 07 modulo app ->](07-fase-modulo-app.md)
