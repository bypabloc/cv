# 02 — Criterios de Aceptacion (AC)

[<- README](README.md) | [Siguiente: fase B ->](03-fase-b-required-login.md)

> Fuente de verdad. Cada test referencia al menos un AC. Formato BDD
> (Given/When/Then). Agrupados por bloque.

## Bloque B — Metodo requerido estricto + login multi-factor

- **AC-B1**: Given la migration `00000005`, When se aplica (upgrade), Then
  `auth_mfa_methods` y `auth_webauthn_credentials` tienen columna `required`
  (boolean, default false, not null) y el `downgrade()` la elimina.
- **AC-B2**: Given `mfa.set-required {kind, required:true}` de un metodo activo,
  Then 204 y `auth_mfa_methods.required = true` para ese `(user, kind)`.
- **AC-B3**: Given `webauthn.set-required {credential_id, required:true}`, Then
  204 y `auth_webauthn_credentials.required = true` para esa passkey.
- **AC-B4**: Given `set-required` de un metodo desactivado o inexistente, Then
  404 `NOT_FOUND` (anti-enumeration), sin tocar nada.
- **AC-B5**: Given un user con DOS metodos `required` (ej. TOTP + passkey), When
  hace login (passwordless o password), Then el backend devuelve un temp step=2
  con `required_methods: ['totp','webauthn']` y EXIGE verificar ambos antes de
  emitir access+refresh.
- **AC-B6**: Given un user con metodos requeridos, When verifica solo UNO de los
  requeridos, Then NO se emiten tokens todavia (devuelve un temp con los
  requeridos pendientes); recien con todos verificados emite tokens.
- **AC-B7**: Given un user con metodos requeridos que perdio acceso, When usa un
  **recovery code** (`mfa.recovery-codes-consume`), Then se emiten tokens
  (fallback anti-lockout), saltando los requeridos.
- **AC-B8**: Given un user con metodos requeridos, When usa el **email-code de
  emergencia**, Then se emiten tokens (segundo fallback), saltando los
  requeridos. (El email-code de emergencia se marca para auditoria.)
- **AC-B9**: Given un user SIN metodos requeridos pero CON MFA configurado, When
  login, Then el comportamiento actual se preserva (propone los metodos, el user
  elige uno).
- **AC-B10**: Given `set-required {required:false}`, Then `required` vuelve a
  false; si era el unico requerido, el login deja de exigirlo.

## Bloque D — Fusion register -> login

- **AC-D1**: Given la operation `register` eliminada, Then `OPERATIONS` ya no la
  declara, `core/controllers/register/` no existe, y un request
  `operation=register` devuelve el error de operation desconocida del handler.
- **AC-D2**: Given `login.start` con un email que NO existe, When ejecuta, Then
  crea el user `pending`, genera code + magic-link, invoca `send_email`
  unificado UNA vez y devuelve `temp_token` (flow `login`, step 1) +
  `created: true`.
- **AC-D3**: Given `login.start` con un email que existe `active`, When ejecuta
  (passwordless), Then NO crea nada, re-emite code+magic-link y devuelve
  `temp_token` + `created: false` + los metodos disponibles.
- **AC-D4**: Given `login.verify-code` de un user `pending`, When el code es
  valido, Then el user pasa a `active` (cierra el registro) y se emiten
  access+refresh. (Detecta por status, no por flow.)
- **AC-D5**: Given `login.verify-magic-link` de un user `pending`, When el token
  es valido, Then el user pasa a `active` y se emiten tokens.
- **AC-D6**: Given `login.verify-code`/`verify-magic-link` de un user ya
  `active`, Then solo loguea (actualiza `last_login_at`), no re-activa.
- **AC-D7**: Given el flujo unificado, Then el `temp_token` SIEMPRE lleva
  `flow='login'` (el concepto `register` desaparece del token).
- **AC-D8**: Given los kinds de email `register-unified`, Then se consolidan en
  `login-unified` (un solo kind/template para el flujo de entrada). Los viejos
  `register-*` se eliminan del seed.
- **AC-D9**: Given el admin, Then NO existe la ruta `/register`, ni
  `register-form.tsx`, ni `use-register-*.ts`, ni `authClient.registerStart`.
  El api-client y la UI usan solo `login`.

## Bloque C — login.check-email (gated por password)

- **AC-C1**: Given `login.check-email {email}` con Turnstile valido y un email
  que existe `active`, Then 200 `{exists:true, has_password:<bool>}` — expone si
  tiene password configurado, pero NO la lista de metodos MFA.
- **AC-C2**: Given `login.check-email` con un email que NO existe, Then 200
  `{exists:false}` (la UI ofrece crear cuenta).
- **AC-C3**: Given `login.check-email` con un email `pending`, Then
  `{exists:true, pending:true, has_password:false}` (debe terminar de
  verificar; passwordless).
- **AC-C4**: Given `login.check-email` con un email `disabled`/`locked`/
  `deleted`, Then `{exists:true, unavailable:true}` (se expone que existe —
  trade-off aceptado — pero no se ofrecen metodos ni se revela el estado real).
- **AC-C5**: Given `login.check-email`, Then aplica Turnstile + rate-limit
  per-IP estricto ANTES de tocar Neon (mitigacion de enumeracion).
- **AC-C6**: Given `login.check-email`, Then NUNCA devuelve: la LISTA de metodos
  MFA, el password hash, el TOTP secret, los recovery codes, el credential_id de
  las passkeys, ni datos de otro user. Solo `exists` + `has_password` + flags.
- **AC-C7**: Given `login.check-email` sin Turnstile, Then 400/403 (igual que
  `login.start`).
- **AC-C8**: Given un user con password, When `verify-password` OK (NO
  `check-email`), Then el backend revela `required_methods`/`methods` para el
  step-up — la lista de metodos queda detras de un factor de autenticacion.

## Bloque A — security.overview + enable + set-required

- **AC-A1**: Given un user autenticado, When `security.overview`, Then 200 con
  `{methods: [...]}` con EXACTAMENTE 5 entradas: `type in {totp, email_code,
  webauthn, recovery_codes, password}`.
- **AC-A2**: Given un user SIN metodos, Then cada entrada tiene
  `configured:false`, `enabled:false`, `required:false`, `preferred:false` y
  `detail` vacio/cero.
- **AC-A3**: Given un user con TOTP activo+required, 1 passkey activa, 8 recovery
  restantes y password, Then `totp={configured,enabled,required:true,...}`,
  `webauthn.detail.credentials` 1 item con `nickname/created_at/last_used_at/
  required/enabled`, `recovery_codes.detail={total:10,remaining:8}`,
  `password={configured:true, detail:{last_change_at}}`.
- **AC-A4**: Given un user con TOTP soft-disabled, Then `totp.configured=true`
  pero `totp.enabled=false` (visible, no oculto).
- **AC-A5**: Given un request sin access JWT, When `security.overview`, Then 401.
- **AC-A6**: Given un user con TOTP soft-disabled, When `mfa.enable {kind:totp}`,
  Then 204 y `disabled_at -> NULL`, `confirmed_at` preservado.
- **AC-A7**: Given un `kind`/`credential_id` inexistente, When `enable`, Then
  404 `NOT_FOUND`.
- **AC-A8**: Given un metodo ya activo, When `enable`, Then 204 idempotente.
- **AC-A9**: Given una passkey soft-disabled, When `webauthn.enable
  {credential_id}`, Then 204 y `disabled_at -> NULL`.
- **AC-A10**: Given el ultimo metodo MFA activo, When `mfa.disable` (toggle-off),
  Then 409 `MUST_KEEP_ONE_MFA_METHOD` y `disabled_at` sigue NULL.
- **AC-A11**: Given `enable`/`set-required`, Then requieren access JWT; sin JWT
  -> 401.

## Bloque E — Frontend (panel + login + nav)

- **AC-E1**: Given el panel `/settings/security`, When carga, Then dispara UNA
  sola consulta (`security.overview`), no 4.
- **AC-E2**: Given el overview, Then el panel renderiza una fila por cada metodo
  con: `Switch` on/off (excepto password), control "requerido al loguear"
  (excepto password), `Badge` de estado y timestamps.
- **AC-E3**: Given una fila MFA activa con >1 metodo, When el user apaga el
  on/off, Then llama `disable`/`webauthn.disable`, invalida el overview, la fila
  pasa a "Desactivado".
- **AC-E4**: Given una fila MFA desactivada, When el user prende el on/off, Then
  llama `enable` y la fila pasa a "Activo".
- **AC-E5**: Given el ultimo metodo MFA activo, When intenta apagarlo, Then
  toast "Debes conservar al menos un metodo" y el Switch queda encendido (409).
- **AC-E6**: Given una fila MFA, When el user activa "requerido al loguear", Then
  el panel muestra una advertencia (guardar recovery codes) y llama
  `set-required {required:true}`.
- **AC-E7**: Given un metodo NO configurado, Then el panel muestra un CTA
  "Configurar" en vez de toggles.
- **AC-E8**: Given la fila password, Then muestra estado + last_change_at + boton
  "Cambiar contrasena", SIN toggles.
- **AC-E9**: Given el sidebar (desktop + mobile), Then existe nav-item
  "Seguridad" -> `/settings/security`.
- **AC-E10**: Given la pantalla de entrada `/login`, When el user ingresa su
  email, Then se llama `check-email`; si existe + `has_password` pide la
  password (y los metodos se revelan tras verificarla); si existe sin password
  va passwordless (magic-link + code); si no existe ofrece "crear cuenta". La
  lista de metodos MFA NUNCA se muestra antes de un factor de autenticacion.
- **AC-E11**: Given el admin tras la fusion, Then NO existe `/register` ni su UI;
  el unico punto de entrada es `/login`.
- **AC-E12**: Given la rule `auth-system.md`, Then se actualizo: el anti-
  enumeration deja de ser absoluto (documentando `check-email`), y la operation
  `register` se elimina de la rule (todo es `login`).

## E2E (post-deploy, Bloque Z)

- **AC-Z1**: En dev real, `check-email` de un email nuevo -> `{exists:false}`; de
  uno existente con password -> `{exists:true, has_password:true}` (sin la lista
  de metodos); la lista se revela solo tras `verify-password`.
- **AC-Z2**: `login.start` de un email nuevo crea el user y manda UN email con
  magic-link + code; el click al link -> 302 a callback; el code -> login OK.
- **AC-Z3**: Un user con TOTP `required` en dev: el login exige el TOTP; un
  recovery code lo saltea.
- **AC-Z4**: El panel `/settings/security` en dev real renderiza los 5 metodos
  con sus estados desde 1 sola consulta; el toggle on/off y el "requerido"
  persisten tras reload.

[<- README](README.md) | [Siguiente: fase B ->](03-fase-b-required-login.md)
