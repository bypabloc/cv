# 06. Estrategia de testing — plan 02 MFA + WebAuthn

> Hereda el patron del plan 01 (`tests/unit/` + `tests/integration/`,
> docstring Given/When/Then, asserts EXACTOS, 1 archivo = 1 escenario).
> Aqui los tests nuevos son del scope MFA + WebAuthn + login extension.

## Tests unit `shared.auth` (nuevos)

Ya listados en [03-shared-auth-extension.md](03-shared-auth-extension.md):
17 archivos (TOTP, QR, WebAuthn, recovery codes, envelope encryption).

## Tests unit `shared/db/repositories/auth_mfa.py`

| Archivo | Escenario |
|---------|-----------|
| `test_list_mfa_methods_returns_active_only.py` | filtra `disabled_at IS NULL` |
| `test_upsert_totp_pending.py` | INSERT row con confirmed_at=NULL |
| `test_upsert_totp_re_setup_replaces.py` | si ya existe row TOTP, reusa (UPDATE) |
| `test_confirm_mfa_sets_timestamp.py` | UPDATE confirmed_at=now() |
| `test_disable_mfa_sets_disabled_at.py` | UPDATE disabled_at=now() |
| `test_set_preferred_unsets_others.py` | UPDATE preferred=false en otros, true en kind |
| `test_insert_recovery_codes_10.py` | INSERT 10 rows en una transaccion |
| `test_consume_recovery_code_marks_consumed.py` | UPDATE consumed_at=now() en el row matcheado |
| `test_consume_recovery_code_returns_false_if_consumed.py` | row con consumed_at IS NOT NULL -> False |
| `test_regenerate_recovery_codes_deletes_old.py` | DELETE viejos + INSERT 10 nuevos |
| `test_insert_webauthn_credential.py` | INSERT con credential_id UK |
| `test_update_sign_count.py` | UPDATE solo si new > old (condicional) |
| `test_delete_webauthn_credential_returns_true_if_found.py` | DELETE + return True |
| `test_delete_webauthn_credential_returns_false_if_other_user.py` | filtro WHERE user_id |

## Tests unit del Lambda `auth` (nuevos)

### `services/` (~25 archivos)

| Archivo | Escenario |
|---------|-----------|
| `test_mfa_method_service_get_active.py` | filtra disabled_at IS NULL |
| `test_mfa_method_service_upsert_totp_encrypts.py` | encrypt_envelope called con kms_key_id correcto |
| `test_mfa_method_service_confirm_sets_preferred_if_first.py` | si es el unico, preferred=true |
| `test_totp_service_decrypt_and_verify_ok.py` | decrypt_envelope + verify_totp_code -> True |
| `test_totp_service_decrypt_and_verify_wrong_code.py` | False |
| `test_totp_service_kms_decrypt_fails.py` | KMS raises -> service levanta `EnvelopeEncryptionError` |
| `test_webauthn_service_build_options_includes_existing.py` | exclude_credentials del user incluido |
| `test_webauthn_service_verify_register_persists.py` | INSERT row + retorna credential_id |
| `test_webauthn_service_verify_login_sign_count_progresses.py` | UPDATE sign_count si new > old |
| `test_webauthn_service_verify_login_clone_detected.py` | new <= old -> levanta WebauthnVerifyError |
| `test_challenge_service_put_with_ttl.py` | PutItem con expires_at = now+300 |
| `test_challenge_service_get_and_consume_atomic.py` | GetItem + DeleteItem; si race -> ConditionalCheckFailed |
| `test_challenge_service_expired_returns_none.py` | TTL ya expiro y DDB borro -> GetItem none |
| `test_recovery_codes_service_generate_persists_hashes.py` | INSERT 10 rows con hashes |
| `test_recovery_codes_service_consume_atomicity.py` | UPDATE condicional; si race -> False |

### `controllers/` (~30 archivos, 1 por escenario)

| Archivo | AC | Escenario |
|---------|-----|-----------|
| `test_mfa_setup_totp_ok.py` | AC-1 | 200 con secret_b32 + otpauth + svg |
| `test_mfa_setup_totp_no_auth.py` | — | sin Authorization -> 401 |
| `test_mfa_setup_totp_rate_limited.py` | — | 4ta request -> 429 |
| `test_mfa_confirm_totp_ok.py` | AC-2 | activa el row |
| `test_mfa_confirm_totp_wrong_code.py` | AC-3 | 400 + audit log |
| `test_mfa_confirm_totp_no_pending.py` | — | 404 NO_PENDING_TOTP |
| `test_mfa_set_preferred_ok.py` | AC-4 | UPDATE OK |
| `test_mfa_set_preferred_unknown_kind.py` | — | 400 |
| `test_mfa_disable_keeps_one.py` | AC-5 | 409 MUST_KEEP_ONE_METHOD |
| `test_mfa_disable_with_two.py` | AC-6 | OK |
| `test_mfa_list_returns_active.py` | — | 200 con metodos del user |
| `test_mfa_recovery_codes_generate_first.py` | AC-7 | 10 codes en response |
| `test_mfa_recovery_codes_regenerate.py` | AC-8 | viejos borrados |
| `test_mfa_recovery_codes_consume_ok.py` | AC-9 | access+refresh + consumed_at |
| `test_mfa_recovery_codes_consume_already.py` | AC-10 | 400 RECOVERY_CODE_CONSUMED |
| `test_webauthn_register_options_ok.py` | AC-11 | DDB challenge persistido |
| `test_webauthn_register_verify_ok.py` | AC-12 | INSERT credential + DELETE challenge |
| `test_webauthn_register_verify_challenge_expired.py` | — | 400 WEBAUTHN_CHALLENGE_NOT_FOUND |
| `test_webauthn_register_verify_attestation_invalid.py` | — | 400 WEBAUTHN_REGISTRATION_FAILED |
| `test_webauthn_login_options_ok.py` | AC-13 | allowCredentials populated |
| `test_webauthn_login_options_no_credentials.py` | — | 404 NO_WEBAUTHN_CREDENTIALS |
| `test_webauthn_login_verify_ok.py` | AC-14 | sign_count++, access+refresh |
| `test_webauthn_login_verify_clone.py` | AC-15 | 401 + disabled |
| `test_webauthn_list_credentials_ok.py` | AC-16 | ordenado por last_used_at DESC |
| `test_webauthn_delete_credential_ok.py` | — | DELETE + 204 |
| `test_webauthn_delete_credential_must_keep_one.py` | AC-17 | 409 |
| `test_webauthn_delete_credential_other_user.py` | AC-25 | 404 (no 403) |
| `test_login_start_with_password_ok.py` | AC-18 | temp JWT step=2 |
| `test_login_start_with_password_wrong.py` | AC-21 | 401 + failed_attempts++ |
| `test_login_start_with_password_no_mfa.py` | AC-20 | access+refresh directo |
| `test_login_verify_totp_ok.py` | AC-19 | access+refresh |
| `test_login_verify_totp_wrong.py` | — | 401 INVALID_TOTP_CODE |
| `test_login_verify_password_brute_force_locks.py` | — | 10 fails -> status=locked |

### `models/` (~10 archivos)

| Archivo | Escenario |
|---------|-----------|
| `test_mfa_confirm_totp_in_pattern_6_digits.py` | code != 6 digits -> ValidationError |
| `test_mfa_recovery_codes_consume_in_pattern.py` | code con O/0/I/1/L -> ValidationError |
| `test_webauthn_register_verify_in_response_dict.py` | response no dict -> ValidationError |
| `test_login_verify_password_in_min_length.py` | password < 12 -> ValidationError |
| `test_login_verify_totp_in_temp_token.py` | sin temp_token -> ValidationError |
| `test_mfa_set_preferred_in_kind_enum.py` | kind no en enum -> ValidationError |
| `test_webauthn_delete_credential_in_uuid.py` | credential_id no UUID -> ValidationError |

## Tests integration

| Archivo | Escenario |
|---------|-----------|
| `test_mfa_setup_totp_full_flow_e2e.py` | setup -> confirm -> login con TOTP (todo verde) |
| `test_mfa_recovery_codes_full_flow_e2e.py` | setup MFA -> generate recovery -> bypass MFA en login |
| `test_webauthn_register_full_flow_e2e.py` | register-options -> verify -> list -> delete |
| `test_webauthn_login_full_flow_e2e.py` | register -> login-options -> login-verify -> JWT |
| `test_login_with_password_and_mfa_e2e.py` | set-password -> setup-totp -> logout -> login con pass + TOTP |
| `test_disable_last_method_e2e.py` | disable solo metodo -> 409 |
| `test_migration_00000003_up_down_e2e.py` | AC-23 |
| `test_totp_secret_at_rest_encrypted_e2e.py` | AC-24 — query directa muestra ciphertext, no plain |

## Fixtures de WebAuthn

Los tests de WebAuthn requieren fixtures realistas del flujo del browser
(navigator.credentials.create / get). python-fido2 trae helpers para
generar fixtures con SoftWebauthnDevice. Crear:

```text
serverless/lambda/services/auth/tests/unit/controllers/webauthn/_fixtures.py
- _make_soft_authenticator()  -> dispositivo WebAuthn simulado
- _make_registration_response(user_id, challenge, rp_id, origin) -> dict
- _make_authentication_response(stored_credential, challenge, ...) -> dict
- _make_clone_response(...)  -> response con sign_count viejo
```

## Cobertura objetivo

- shared.auth (modulos nuevos): 95%+
- services/ (lambda auth nuevos): 85%+
- controllers/ (nuevos): 85%+
- models/ (nuevos): 100%

## Comandos

```bash
# unit
python devtools/run.py serverless tests --type=unit --lambda=auth
python devtools/run.py serverless tests --type=unit --shared

# coverage
python devtools/run.py serverless tests --type=coverage --lambda=auth

# integration (requiere recursos AWS dev)
python devtools/run.py serverless tests --type=integration --lambda=auth
```

## Reglas duras de testing (heredadas + nuevas)

- **SIEMPRE** WebAuthn fixtures usan SoftWebauthnDevice de python-fido2;
  no fixtures hardcoded de YubiKey reales (no reproducibles).
- **SIEMPRE** envelope encryption tests usan moto.mock_aws() para KMS
  (no AWS real en unit).
- **SIEMPRE** TOTP test que verifica el code usa `pyotp.TOTP(secret).now()`
  como source-of-truth, no codes hardcodeados.
- **NUNCA** test que dependa de un browser real para WebAuthn (E2E con
  Playwright queda para plan futuro de frontend).
