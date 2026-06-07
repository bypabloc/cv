# Flujos de autenticacion

> Diagrama ASCII por flujo. Mas detalle en los controllers correspondientes.

## Login (flujo de entrada unico — cubre alta y entrada)

> La operation `register` fue ELIMINADA. El alta de usuarios ocurre dentro
> del flujo `login`: `login.check-email` es el unico punto con Turnstile y
> emite el temp JWT precheck; `login.start` exige ese precheck y CREA el
> user `pending` si el email no existe (alta fusionada). El STATUS del user
> (no la operation que lo creo) determina la transicion `pending -> active`.

```text
--- Precheck (unico punto con Turnstile) ---

POST /auth {operation: login, action: check-email, data: {email, cf_turnstile_response}}
  | turnstile + rate-limit
  v
buscar auth_users por email
  | active/pending   -> 200 {exists, has_password, temp_token (precheck, flow=login step=0)}
  | exists:false     -> 200 {exists:false, temp_token (precheck con sub placeholder)}
  | disabled/locked  -> 200 {status: 'unavailable'} (sin temp_token — anti-enumeration)
  v
el temp_token precheck habilita continuar a login.start


--- Inicio (alta fusionada) ---

POST /auth {operation: login, action: start, data: {email, password?}}
  | Authorization: Bearer <temp precheck (flow=login step=0)>  -- sin Authorization -> 401 MISSING_PRECHECK
  | rate-limit (NO turnstile: ya se valido en check-email)
  v
buscar auth_users por email
  | si NO existe -> crear auth_users (status=pending), created: true (alta fusionada)
  | si pending   -> re-emite el email unificado, created: false (idempotente, AC-19)
  | si disabled/locked -> 404 EMAIL_NOT_FOUND + suggest_register: false (AC-20)
  | si active + password ausente -> flujo passwordless (magic-link + code)
  | si active + password presente -> step-up (ver 04-mfa.md)
  v
persistir Neon: auth_email_codes(code_hash, kind=login, attempts=0, expires_at)
                auth_magic_links(token_hash, kind=login, expires_at)
                auth_audit_log(event=login.start, success=true)
  |
invocar send_email async (InvocationType='Event'):
  {operation: email, action: send, data: {kind: login-unified, ...}}
  |
emitir temp JWT (flow=login, step=1, ttl=300)
  v
200 {temp_token, methods: ['magic-link', 'email-code'], created, expires_in: 300}


--- Verificacion magic-link (GET, browser) ---

GET /auth?operation=login&action=verify-magic-link&token=<X>
  | turnstile NO (ya validamos en check-email)
  | rate-limit
  v
verificar token_hash en auth_magic_links (consumed_at IS NULL, exp > now)
  | si consumed -> 400 LINK_CONSUMED (AC-16)
  | si expired  -> 400 LINK_EXPIRED  (AC-17)
  v
marcar consumed + auth_users.status='active' (cierra la transicion pending -> active)
  |
emitir access + refresh (family_id nuevo)
  |
audit log
  v
302 Location: https://admin.portfolio.{env}.the-full-stack.com/callback
              #access=<JWT>&refresh=<JWT>&user_id=<X>&email=<Y>
              Cache-Control: no-store, no-cache, must-revalidate


--- Verificacion code (POST, dashboard) ---

POST /auth {operation: login, action: verify-code, data: {code, temp_token}}
  | verify temp JWT (typ=temp, flow=login, NOT blacklisted)
  | rate-limit
  v
buscar auth_email_codes (user_id del JWT, kind=login, consumed_at IS NULL)
  | si wrong -> increment attempts, 400 INVALID_CODE
  | si >=5 attempts -> auth_users.status='locked', 423 ACCOUNT_LOCKED (AC-11)
  | si expired -> 400 EXPIRED_CODE
  v
marcar consumed + status='active' + blacklist temp_token jti
  |
emitir access + refresh (family_id nuevo)
  |
si el user ya estaba active: actualizar last_login_at + reset failed_attempts (AC-22)
  v
200 {access_token, refresh_token, expires_in: 900, token_type: 'Bearer',
     user: {id, email, status}}
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
  kind: 'login-unified' | 'login-magic-link' | 'login-code' |
        'password-reset',
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
