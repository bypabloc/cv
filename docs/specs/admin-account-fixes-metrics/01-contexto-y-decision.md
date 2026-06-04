# 01 — Contexto, solución y criterios de aceptación

[← README](README.md) · [Siguiente: backend TOTP →](02-backend-totp.md)

## 1. Contexto / Problema

Tras usar el admin (`admin.portfolio.dev.the-full-stack.com`) desplegado
contra el backend serverless en dev, el usuario reportó ~11 issues. Cada uno
verificado en código + investigación:

1. **TOTP `confirm-totp` da `INVALID_TOTP_CODE`** con el OTP del QR. El
   setup genera/cifra el secret con KMS (`EncryptionContext={user_id,
   purpose:totp}`) y el confirm lo descifra con el MISMO context. El
   `otpauth_url` y `verify_totp_code` usan los defaults de pyotp (SHA1/6/30).
   Causa a confirmar en runtime: round-trip KMS o lectura del row pendiente.
2. **email-code** aparece en `/settings/security` aunque es el método de
   entrada (login). No debe ser configurable ahí.
3. **passkey** dice "no configurado" sin botón para registrar.
4. **change-password** exige "contraseña actual" aunque el user sea
   passwordless (`profile.get` NO devuelve `has_password`).
5. **`/settings/security` y `/sessions`** son páginas separadas; deben ser
   tabs de `/settings` (Perfil | Seguridad | Sesiones).
6. **"usuario" y "sesión actual" vacíos** en la vista de sesiones:
   `status.get` NO devuelve `current_session_id`.
7. **change-email** — verificar que valida por magic-link/code (ya lo hace:
   token single-use al nuevo email, 15 min; no es bug).
8. **"nombre para mostrar"** no deja tipear (campo no editable / reset que
   nunca corre con la data cargada).
9. **gráfica "Eventos en el tiempo" vacía** aunque la API devuelve points.
10. **retención 0%** confuso (no es bug; falta explicación).
11. **dropdown de rango** estilo Amazon CloudWatch (Relative/Absolute) +
    quitar el **polling** (15s) por un botón "Actualizar".

### Hallazgos de exploración (cerrados)

- `setup_totp.py` y `confirm_totp.py` usan el MISMO `TotpService._context`
  (`{user_id, purpose:totp}`). `otpauth_url` y `verify` usan defaults pyotp
  idénticos. La causa del INVALID_TOTP_CODE se confirma en runtime (fase 2)
  con un test round-trip real (moto KMS) + invoke en dev.
- `ProfileService.has_password()` (users) YA existe; solo falta exponerlo en
  `profile.get`.
- `status.get` NO devuelve `current_session_id`; el access JWT SÍ lleva
  `family_id` (siempre, vía `issue_access_jwt(..., family_id=...)`).
- analytics: el backend YA acepta `bucket=day|hour|week`, valida rango <=90d,
  pero `from`/`to` son `date` (medianoche UTC). Para sub-día hay que aceptar
  `datetime` + bucket `minute`.
- change-email: flujo correcto (token single-use al nuevo email). No es bug.
- `TimeseriesChart` está bien escrito; la gráfica vacía se diagnostica en
  runtime con el JSON real del usuario como fixture (fase 7).

## 2. Solución Propuesta

11 fixes en 1 PR, agrupados en 6 fases técnicas (3 backend + 3 admin).
Backend primero (las APIs que el admin consume), luego admin.

### Decisiones clave

Ver la tabla de decisiones D-1..D-11 en el [README](README.md). Resumen:

- **Decisión A (TOTP):** diagnosticar la causa raíz del INVALID_TOTP_CODE en
  runtime (test round-trip KMS + invoke dev). El fix depende del hallazgo;
  el candidato más probable es un mismatch en el round-trip del ciphertext
  (encoding del BYTEA al leer de Neon, o el `valid_window`). Se cubre con un
  test que cifra → persiste → lee → descifra → verifica con un code real.
- **Decisión B (users):** `profile.get` agrega `has_password`; `status.get`
  agrega `current_session_id` (del `family_id` del JWT).
- **Decisión C (analytics):** `from`/`to` aceptan `datetime` (ISO con hora);
  `bucket` acepta `minute` además de day/hour/week; el límite 90d pasa a
  contar por duración (timedelta), no solo días.
- **Decisión D (settings tabs):** 3 rutas reales con un layout de tabs
  compartido. `profile-form` arregla el reset/edición del display_name.
- **Decisión E (panel seguridad):** quita email-code de la lista, agrega
  botón "Registrar passkey", y el set-password condicional por has_password.
- **Decisión F (metrics):** arregla la gráfica, agrega tooltip a retención,
  reemplaza el selector por el dropdown CloudWatch (Relative/Absolute) y
  quita el polling por un botón "Actualizar".

## 3. Criterios de Aceptación (AC)

### Backend — TOTP (fase 2)
- **AC-1**: Given un secret TOTP cifrado con KMS y persistido como BYTEA en
  `auth_mfa_methods`, When se lee el row pendiente y se descifra, Then el
  `secret_b32` recuperado es BIT-IDÉNTICO al original (round-trip exacto).
- **AC-2**: Given un user con TOTP pendiente y un code de 6 dígitos generado
  con el `secret_b32` del setup, When ejecuta `mfa.confirm-totp` con ese code
  (dentro del window), Then responde 204 y el método queda confirmado.

### Backend — analytics rango (fase 4)
- **AC-3**: Given `TimeseriesInput` (y `DateRange`), When el cliente envía
  `from`/`to` como datetime ISO con hora (`2026-06-03T18:00:00Z`), Then el
  backend respeta la hora (no redondea a medianoche).
- **AC-4**: Given `bucket=minute`, When ejecuta timeseries, Then agrupa por
  `date_trunc('minute', ...)` y devuelve un punto por minuto del rango.

### Backend — users (fase 3)
- **AC-5**: Given `profile.get`, Then la respuesta incluye `has_password:
  bool` (true si existe row en `auth_credentials`).
- **AC-6**: Given `status.get` con un access JWT que lleva `family_id`, Then
  la respuesta incluye `current_session_id` == ese `family_id`.
- **AC-7**: Given `status.get` con un JWT sin `family_id` (legacy), Then
  `current_session_id` es `null` (no rompe).

### Admin — settings tabs (fase 5)
- **AC-8**: Given `/settings`, `/settings/security`, `/settings/sessions`,
  Then las 3 rutas responden 200 y renderizan el mismo layout con un tab
  activo distinto (Perfil | Seguridad | Sesiones).
- **AC-9**: Given el sidebar, Then NO hay items separados a `/sessions` ni a
  `/settings/security`; "Configuración" lleva a `/settings` (los tabs cubren
  el resto). El item viejo `/sessions` se elimina o redirige a
  `/settings/sessions`.
- **AC-10**: Given la vista de sesiones (tab), When carga `status.get`, Then
  muestra `user_id`, `status` y `current_session_id` (no vacíos).
- **AC-11**: Given el tab Perfil con la data del user cargada, When el user
  tipea en "Nombre para mostrar", Then el input acepta el texto (editable) y
  el submit envía el valor.

### Admin — panel seguridad (fase 6)
- **AC-12**: Given el panel de seguridad, Then NO renderiza una fila/row para
  el método email-code (queda solo TOTP, passkey, recovery, password).
- **AC-13**: Given el panel con passkey "no configurado", Then muestra un
  botón "Registrar passkey" que dispara `navigator.credentials.create()` vía
  `webauthn.register-options` → `register-verify`.
- **AC-14**: Given un user con `has_password === false`, When abre "cambiar
  contraseña", Then el form NO pide "contraseña actual", el título es
  "Establecer contraseña" y al enviar llama `set-password` (no
  `change-password`).
- **AC-15**: Given "cambiar email", When el user envía un email nuevo, Then
  la UI informa que debe confirmar desde el NUEVO correo (magic-link), y el
  flujo `change-email` → `confirm-email-change` se documenta como verificado.

### Admin — metrics (fase 7)
- **AC-16**: Given el dashboard con `timeseries.points` poblado (datos
  reales: 8 puntos, counts 6..3875), When renderiza "Eventos en el tiempo",
  Then la gráfica dibuja la línea con los puntos (no "Sin datos" ni vacío).
- **AC-17**: Given la tarjeta de Retención, Then muestra un tooltip/leyenda
  que explica nuevos vs recurrentes y que 0% = ningún visitante previo volvió
  en el rango (sin mención a correos).
- **AC-18**: Given el selector de rango, Then replica el dropdown CloudWatch:
  pestañas Relative/Absolute, chips 5m/30m/1h/3h/12h/Custom, grid
  Minutes/Hours/Days/Weeks + Duration + Unit, y Absolute con 2 calendarios +
  Start/End date+time + Apply.
- **AC-19**: Given un preset Relative "1h", When se aplica, Then la page pide
  al backend `from`/`to` como datetime (ahora-1h .. ahora) con `bucket`
  acorde (minute/hour) y la gráfica refleja ese rango.
- **AC-20**: Given la page /metrics, Then NO hace polling (sin
  `refetchInterval`); un botón "Actualizar" invalida y recarga todas las
  queries de analytics (incl. active-now).

[← README](README.md) · [Siguiente: backend TOTP →](02-backend-totp.md)
