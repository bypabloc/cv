# 06. Estrategia de testing

> Sigue el "Estandar de testing" de `.claude/rules/lambda-controller.md`:
> dos niveles (`tests/unit/`, `tests/integration/`), un archivo por
> escenario, docstring Given/When/Then + cuerpo AAA, asserts EXACTOS.

## Niveles

### Unit (`tests/unit/`)

Aislado, sin red. Mockea SOLO E/S externa: SES, SSM, DynamoDB
(via `shared.aws.get_resource` -> patcheado), SQS publish (`boto3`
sqs client), Neon (sessionmaker patcheado). NO se mockean
`controllers`, `services`, `models`, `shared.auth.*`, `shared.rate_limit.*`
propios.

`conftest.py` raiz:
- Inyecta env vars (`JWT_ISSUER`, `JWT_AUDIENCE`, `MAGIC_LINK_BASE_URL`,
  `CORS_ALLOWED_ORIGINS`, etc.).
- Mockea `get_secret_by_name('jwt-secret', ...)` con un valor fijo
  para reproducibilidad (cualquier string >32 chars sirve).
- Mockea `boto3.client('dynamodb')`, `boto3.resource('dynamodb')`,
  `boto3.client('sqs')`, `boto3.client('sesv2')` con `botocore.stub`.
- Patches `shared.db.db_session` con un `Session` en memoria
  (SQLite-compatible si los modelos lo permiten, sino mocks).

### Integration (`tests/integration/`)

E2E con recursos reales en `local` (RIE + dynamodb-local + neon branch
de prueba). `conftest.py`:
- Cleanup `autouse`: borra el row de `auth_users` con email
  `test+<timestamp>@example.com` antes y despues.
- Fixtures de `_fixtures/`: crean users en distintos estados (pending,
  active, locked).
- NO mockea nada.

## Cobertura objetivo

- Coverage per-file >= 80% en `core/services/`, `core/controllers/`,
  `core/models/`.
- `shared/auth/` cubre 100% (modulo pequeno, criticidad alta).
- `core/handler.py` excluido del coverage threshold (es boilerplate
  con `http_handler`).

## Tabla de tests unit por archivo (1 archivo = 1 escenario)

### `shared.auth` (en `shared/tests/unit/shared/auth/`)

Ya listado en [03-shared-auth.md](03-shared-auth.md) — 17 archivos.

### `services/` del Lambda auth (`tests/unit/services/`)

| Archivo | Escenario |
|---------|-----------|
| `test_user_service_get_by_email_found.py` | email existente -> retorna AuthUser |
| `test_user_service_get_by_email_not_found.py` | email inexistente -> None |
| `test_user_service_create_pending_new.py` | crea row con status=pending |
| `test_user_service_create_pending_duplicate.py` | email duplicado -> IntegrityError handled (re-fetch) |
| `test_user_service_increment_failed_attempts.py` | incrementa contador, NO bloquea hasta 10 |
| `test_user_service_lock_user_after_10_failed.py` | locked_until = now+1h, status=locked |
| `test_user_service_reset_failed_attempts.py` | resetea a 0 + status active |
| `test_code_service_generate_and_persist.py` | genera, persiste en Neon + DDB, retorna (code, hash) |
| `test_code_service_verify_correct.py` | code correcto -> consume, retorna user_id |
| `test_code_service_verify_wrong_increments.py` | code incorrecto -> increment attempts |
| `test_code_service_verify_expired.py` | expired -> retorna None, NO consume |
| `test_code_service_verify_max_attempts_locks.py` | 5th wrong -> locks user |
| `test_magic_link_service_generate_persist.py` | genera token 32 bytes, persiste hash en Neon |
| `test_magic_link_service_verify_correct.py` | token correcto -> consume |
| `test_magic_link_service_verify_consumed.py` | ya consumido -> retorna None |
| `test_magic_link_service_verify_expired.py` | expirado -> None |
| `test_jwt_service_issue_temp.py` | claims correctas (flow, step, typ='temp') |
| `test_jwt_service_issue_access.py` | claims correctas (typ='access', email) |
| `test_jwt_service_issue_refresh_family.py` | family_id presente, uuidv7 |
| `test_jwt_service_verify_temp.py` | OK + retorna claims |
| `test_jwt_service_verify_blacklisted.py` | jti en blacklist -> JwtRevokedError |
| `test_jwt_service_blacklist_jti.py` | PutItem en DDB con TTL=exp |
| `test_jwt_service_blacklist_family.py` | Query GSI by_family_id -> blacklist todos |
| `test_blacklist_service_get_revoked.py` | jti revoked -> True |
| `test_blacklist_service_get_not_revoked.py` | jti no existe -> False |
| `test_email_dispatch_service_publish_magic_link.py` | SQS SendMessage con body correcto |
| `test_email_dispatch_service_publish_code.py` | idem para code |
| `test_audit_service_log_success.py` | INSERT INTO auth_audit_log success=true |
| `test_audit_service_log_failure.py` | success=false + error_code presente |
| `test_rate_limit_service_check_or_raise_under.py` | bajo limite -> retorna |
| `test_rate_limit_service_check_or_raise_over.py` | excedido -> levanta RateLimitExceededError |
| `test_flow_service_advance_step.py` | recibe claims temp, emite nuevo +1, blacklistea viejo |

### `controllers/` del Lambda auth (`tests/unit/controllers/`)

| Archivo | Escenario | AC |
|---------|-----------|-----|
| `test_register_start_new_email_ok.py` | email nuevo + Turnstile valido -> 201 + temp_token | AC-1 |
| `test_register_start_email_active_409.py` | email ya active -> 409 EMAIL_ALREADY_REGISTERED | AC-2 |
| `test_register_start_turnstile_invalid_403.py` | Turnstile fail -> 403 antes de tocar Neon | AC-12 |
| `test_register_start_rate_limited_429.py` | 4ta request en 1h -> 429 | AC-13 |
| `test_register_verify_magic_link_ok.py` | token valido -> 200 con access+refresh | AC-3 |
| `test_register_verify_magic_link_consumed.py` | ya consumido -> 400 LINK_CONSUMED | AC-16 |
| `test_register_verify_magic_link_expired.py` | expirado -> 400 LINK_EXPIRED | AC-17 |
| `test_register_verify_code_ok.py` | code correcto + temp_token valido -> 200 con access+refresh | AC-4 |
| `test_register_verify_code_wrong_increments.py` | code wrong -> 400 + attempts incremented | AC-11 |
| `test_register_verify_code_locks_after_5_fail.py` | 5to fail -> 423 ACCOUNT_LOCKED | AC-11 |
| `test_register_verify_code_temp_token_expired.py` | temp_token exp pasado -> 401 | AC-18 |
| `test_register_verify_code_temp_token_blacklisted.py` | replay del viejo -> 401 TOKEN_BLACKLISTED | AC-10 |
| `test_register_start_email_pending_reemits.py` | pending -> re-emite magic + code (idempotente) | AC-19 |
| `test_register_start_email_disabled_404.py` | disabled -> 404 EMAIL_NOT_FOUND (anti-enumeration) | AC-20 |
| `test_login_start_email_not_found_404.py` | email no existe -> 404 + suggest_register | AC-5 |
| `test_login_start_email_active_no_password.py` | active sin password -> 200 + methods=[magic-link, email-code] | AC-6 |
| `test_login_start_email_locked_404.py` | locked -> 404 EMAIL_NOT_FOUND (anti-enumeration) | AC-20 |
| `test_login_start_email_disabled_404.py` | disabled -> 404 EMAIL_NOT_FOUND (anti-enumeration) | AC-20 |
| `test_login_start_email_pending_409.py` | pending -> 409 PENDING_VERIFICATION (debe completar register) | AC-6 |
| `test_login_verify_magic_link_ok_updates_last_login.py` | login flow magic-link OK -> access+refresh + `last_login_at` updated + `failed_attempts=0` | AC-22 |
| `test_login_verify_code_ok_updates_last_login.py` | login flow code OK -> idem | AC-22 |
| `test_verify_set_password_ok.py` | password seteada en auth_credentials | AC-4 |
| `test_verify_set_password_too_short.py` | < 12 chars -> 400 | AC-4 |
| `test_verify_resend_code_ok.py` | nuevo code + sqs publish | AC-19 |
| `test_verify_resend_code_throttled.py` | menos de 60s desde el ultimo -> 429 RESEND_THROTTLED | AC-21 |
| `test_session_refresh_ok.py` | refresh valido -> nuevo access+refresh, viejo blacklisted | AC-7 |
| `test_session_refresh_reuse_detected.py` | refresh ya consumed -> 401 + revoca family | AC-8 |
| `test_session_refresh_invalid_signature.py` | signature wrong -> 401 | AC-10 |
| `test_session_logout_access_ok.py` | access valido -> 204 + blacklist | AC-9 |
| `test_session_logout_access_and_refresh.py` | ambos -> 204 + blacklist ambos + family | AC-9 |
| `test_session_logout_already_blacklisted.py` | jti ya blacklisted -> 204 (idempotente) | AC-23 |

### `models/` (`tests/unit/models/`)

| Archivo | Escenario |
|---------|-----------|
| `test_register_start_in_email_required.py` | sin email -> ValidationError |
| `test_register_start_in_email_invalid.py` | email mal formado -> ValidationError |
| `test_register_start_in_turnstile_required.py` | sin cf_turnstile_response -> ValidationError |
| `test_register_verify_code_in_pattern.py` | code con O/0/I/1/L -> ValidationError |
| `test_register_verify_code_in_length.py` | code != 8 -> ValidationError |
| `test_session_refresh_in_short_token.py` | refresh_token < 20 chars -> ValidationError |
| `test_meta_injection.py` | `_meta` se mapea a `meta` campo |

### `tests/unit/` raiz

| Archivo | Escenario |
|---------|-----------|
| `test_handler_routes_register_start.py` | event -> http_handler -> controller correcto |
| `test_handler_invalid_operation_404.py` | operation desconocido -> 404 |
| `test_handler_invalid_action_404.py` | action no en OPERATIONS -> 404 |
| `test_event_model_register_actions.py` | EVENT_MODEL acepta los 3 actions de register |

## Tests unit del Lambda `auth_email_worker`

Path: `serverless/lambda/services/auth_email_worker/tests/unit/`

| Archivo | Escenario | AC |
|---------|-----------|-----|
| `test_worker_handles_magic_link.py` | recibe mensaje -> renderiza template -> send_email called con args correctos | AC-14 |
| `test_worker_handles_code.py` | mismo para email-code |  |
| `test_worker_handles_password_reset.py` | mismo |  |
| `test_worker_ses_error_retries.py` | SES throttle -> levanta excepcion (SQS reintenta) |  |
| `test_worker_ses_permanent_failure.py` | bounce permanente -> log + audit + return (no reintenta) |  |
| `test_worker_invalid_kind_dlq.py` | kind desconocido -> error -> termina en DLQ |  |
| `test_worker_template_rendering_es.py` | locale=es -> contenido en espanol |  |
| `test_worker_template_rendering_en.py` | locale=en -> contenido en ingles |  |

## Tests integration (`tests/integration/`)

Solo escenarios E2E criticos. Cada uno levanta dependencias locales
(dynamodb-local + Neon branch + LocalStack-style SQS via moto si se
quiere offline; alternativa: dev real con stage=local apuntando a AWS
de pruebas).

| Archivo | Escenario |
|---------|-----------|
| `test_register_full_flow_e2e.py` | start -> verify-code -> set-password -> session.refresh -> logout (todo verde) |
| `test_register_then_login_e2e.py` | tras register, login.start devuelve methods. login.verify-code -> JWT |
| `test_login_unknown_email_returns_suggest_register_e2e.py` | login.start con email aleatorio -> 404 |
| `test_token_reuse_detection_e2e.py` | usar refresh dos veces -> 2da llamada revoca toda la familia |
| `test_account_lock_after_5_fails_e2e.py` | 5 verify-code wrong -> status=locked |
| `test_email_worker_publishes_to_ses_e2e.py` | publica mensaje a auth-email-queue -> el worker lo procesa y envia a SES sandbox (verifica MessageId no vacio) |
| `test_migration_up_and_down_e2e.py` | aplica 00000002 + downgrade + upgrade idempotente | AC-15 |

## Stub config (env vars por test)

```ini
JWT_ISSUER=portfolio-auth-test
JWT_AUDIENCE=portfolio-test
JWT_SECRET=<test-placeholder-min-32-bytes>
MAGIC_LINK_BASE_URL=http://localhost:9999/auth
CORS_ALLOWED_ORIGINS=http://localhost:9999
TURNSTILE_BYPASS_SECRET=<test-bypass-placeholder>
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/test
SSM_JWT_BLACKLIST_TABLE_PATH=/portfolio/test/dynamodb/jwt-blacklist/name
SSM_AUTH_EMAIL_QUEUE_URL_PATH=/portfolio/test/sqs/auth-email/url
```

Los placeholders `<...>` se sustituyen por valores aleatorios generados
con `secrets.token_urlsafe(32)` al inicio de cada test run via
`conftest.py` (no se hardcodean).

## Reglas duras de testing

- **SIEMPRE** asserts exactos: `assert response['statusCode'] == 200`
  NO `assert response['statusCode'] >= 200`.
- **SIEMPRE** Given/When/Then en el docstring del test.
- **SIEMPRE** 1 archivo = 1 funcion `test_*` = 1 escenario.
- **SIEMPRE** los builders compartidos viven en `_helpers.py` /
  `_fixtures/` con prefijo `_` (no recolectados por pytest).
- **NUNCA** mockear `controllers/`, `services/` o `models/` propios.
- **NUNCA** assert sobre el contenido del email (la plantilla cambia;
  testear que `send_email` fue llamado con `to=[expected]` es
  suficiente).
- **NUNCA** test que dependa de un email real (incluso en
  integration). Usar SES sandbox + email `success@simulator.amazonses.com`.

## Comandos

```bash
# unit
python devtools/run.py serverless tests --type=unit --lambda=auth
python devtools/run.py serverless tests --type=unit --lambda=auth_email_worker
python devtools/run.py serverless tests --type=unit --shared

# coverage
python devtools/run.py serverless tests --type=coverage --lambda=auth

# integration (requiere recursos)
python devtools/run.py serverless tests --type=integration --lambda=auth
```
