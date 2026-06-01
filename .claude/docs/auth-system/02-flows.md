# Flujos de autenticacion

> Diagrama ASCII por flujo. Mas detalle en los controllers correspondientes.

## Register

```text
POST /auth {operation: register, action: start, data: {email, cf_turnstile_response}}
  | turnstile + rate-limit
  v
[user no existe?] -- si -- crear auth_users (status=pending)
  |                          generar code + magic_link_token
  | si existe + status=active -> 409 EMAIL_ALREADY_REGISTERED
  | si existe + status=pending -> re-emite (idempotente, AC-19)
  | si existe + status=disabled/locked -> 404 EMAIL_NOT_FOUND (AC-20)
  v
persistir Neon: auth_email_codes(code_hash, kind=register, attempts=0, expires_at)
                auth_magic_links(token_hash, kind=register, expires_at)
                auth_audit_log(event=register.start, success=true)
  |
publicar SQS: {kind: register-magic-link, ...} + {kind: register-code, ...}
  |
emitir temp JWT (flow=register, step=1, ttl=300)
  v
200 {temp_token, user_id, expires_in: 300}


--- Verificacion magic-link (GET, browser) ---

GET /auth?operation=register&action=verify-magic-link&token=<X>
  | turnstile NO (ya validamos en start)
  | rate-limit
  v
verificar token_hash en auth_magic_links (consumed_at IS NULL, exp > now)
  | si consumed -> 400 LINK_CONSUMED (AC-16)
  | si expired  -> 400 LINK_EXPIRED  (AC-17)
  v
marcar consumed + auth_users.status='active'
  |
emitir access + refresh (family_id nuevo)
  |
audit log
  v
302 Location: https://admin.portfolio.{env}.the-full-stack.com/callback
              #access=<JWT>&refresh=<JWT>&user_id=<X>&email=<Y>
              Cache-Control: no-store, no-cache, must-revalidate


--- Verificacion code (POST, dashboard) ---

POST /auth {operation: register, action: verify-code, data: {code, temp_token}}
  | verify temp JWT (typ=temp, flow=register, NOT blacklisted)
  | rate-limit
  v
buscar auth_email_codes (user_id del JWT, kind=register, consumed_at IS NULL)
  | si wrong -> increment attempts, 400 INVALID_CODE
  | si >=5 attempts -> auth_users.status='locked', 423 ACCOUNT_LOCKED (AC-11)
  | si expired -> 400 EXPIRED_CODE
  v
marcar consumed + status='active' + blacklist temp_token jti
  |
emitir access + refresh (family_id nuevo)
  v
200 {access_token, refresh_token, expires_in: 900, token_type: 'Bearer',
     user: {id, email, status}}
```

## Login

```text
POST /auth {operation: login, action: start, data: {email, cf_turnstile_response}}
  | turnstile + rate-limit
  v
buscar auth_users por email
  | si NO existe -> 404 EMAIL_NOT_FOUND + suggest_register: true (AC-5)
  | si disabled/locked -> 404 EMAIL_NOT_FOUND + suggest_register: false (AC-20)
  | si pending -> 409 PENDING_VERIFICATION
  v
generar code + magic_link + emitir temp JWT (flow=login)
publicar SQS
  v
200 {temp_token, methods: ['magic-link', 'email-code'], expires_in: 300}


--- verify-magic-link / verify-code: identicos a register pero con
flow='login'. Al exito: actualizar auth_users.last_login_at + reset
failed_attempts (AC-22). ---
```

## Verify (set-password / resend-code)

```text
POST /auth {operation: verify, action: set-password, data: {password, temp_token}}
  | verify temp JWT (typ=temp, NOT blacklisted)
  | rate-limit
  | password >= 12 chars
  v
hash_password(password, argon2id)
INSERT INTO auth_credentials (user_id, password_hash, algo='argon2id')
auth_users.password_set_at = now()
blacklist temp_token jti
  |
emitir nuevo temp con step+1 (si flujo continua) o access+refresh (si terminal)


POST /auth {operation: verify, action: resend-code, data: {temp_token}}
  | verify temp JWT
  | rate-limit RESEND (3/5min/IP) y throttle por user (60s desde el ultimo, AC-21)
  v
re-genera code + magic_link (invalida los anteriores con consumed_at=now)
publica SQS
emite nuevo temp_token (rolling)
```

## Session (refresh / logout)

```text
POST /auth {operation: session, action: refresh, data: {refresh_token}}
  | verify refresh JWT (typ=refresh)
  | NOT in blacklist
  v
[blacklisted?]
  | si  -> reuse detected: Query GSI by_family_id, blacklist TODA la familia
  |        401 TOKEN_REUSE_DETECTED + audit (AC-8)
  | no  v
blacklist refresh viejo (PutItem con reason='rotation', TTL=exp)
emitir nuevo access + nuevo refresh (mismo family_id)
audit log success
  v
200 {access_token, refresh_token, expires_in: 900}


POST /auth {operation: session, action: logout, data: {access_token, refresh_token?}}
  | verify access JWT
  v
blacklist jti_access con reason='logout'
si refresh_token presente: blacklist TODOS los jti de su family_id
  |
audit log
  v
204 (idempotente: si ya blacklisted, devuelve 204 sin error, AC-23)
```

## Magic-link via email (worker async)

```text
Lambda auth publica a SQS portfolio-auth-email-${stage}:
{
  kind: 'register-magic-link' | 'register-code' | 'login-magic-link' |
        'login-code' | 'password-reset',
  to: 'user@example.com',
  user_id, niche?, subject_id, data: {token | code, expires_in_min,
  verify_url?}, audit_event_id
}
  |
SQS trigger (batch_size=5) -> auth_email_worker
  | router por kind -> controller especifico
  v
template_service renderiza plantilla {es,en}/<kind>.{txt,html}
send_service llama shared.aws.send_email(from=ses_from_address,
                                          to=[email],
                                          subject, text, html)
audit_service inserta auth_audit_log event='email.sent.<kind>'
  |
si SES throttle -> levanta excepcion (SQS reintenta, max=3 -> DLQ)
si SES bounce permanente -> log + audit fail + return (no reintenta)
```
