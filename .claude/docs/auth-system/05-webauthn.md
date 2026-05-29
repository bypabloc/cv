# WebAuthn / Passkeys

> [< README](README.md) | [< 04-mfa](04-mfa.md)
>
> Extension del plan 02-auth-mfa al Lambda `auth`. Cubre la operation
> `webauthn` (6 actions), los challenges efimeros en DynamoDB, el RP_ID
> por env, el clone detection por sign_count y el portador `shared.auth`
> de `python-fido2` 1.2.

## Ceremony WebAuthn

Passkeys via `python-fido2` 1.2 (Yubico). El subpackage `shared.auth`
es el portador unico de `fido2`; encapsula `Fido2Server` en
`shared/auth/webauthn.py`. El ceremony tiene 2 fases x 2 pasos:

```text
REGISTER  webauthn.register-options  -> {challenge_id, options}  (DDB put state)
          navigator.credentials.create({publicKey: options.publicKey})
          webauthn.register-verify   -> valida attestation, persiste credential

LOGIN     webauthn.login-options     -> {challenge_id, options}  (DDB put state)
          navigator.credentials.get({publicKey: options.publicKey})
          webauthn.login-verify      -> valida assertion, emite access+refresh
```

`build_register_options` / `build_login_options` retornan
`(options_json, state)`. `options_json` es un dict JSON browser-ready
(`_to_json` convierte recursivamente bytes -> base64url y enums -> value);
`state` es el dict JSON-serializable que devuelve fido2
(`{'challenge': '<b64url>', 'user_verification': '<value>'}`).

- `attestation='none'` (sin verificacion de attestation del fabricante).
- `verify_origin=lambda origin: origin in expected_origins` (allowlist).
- `user_id` se pasa como `UUID(...).bytes` al server fido2.
- Register excluye los credentials existentes del user para no registrar
  2 veces el mismo authenticator.

## Challenges efimeros en DynamoDB (decision 5)

Los challenges NO viven en Neon — son efimeros (1 por intento). Van a
`portfolio-webauthn-challenges-${stage}`:

- PK `challenge_id` (UUIDv7 string). Atributos: `user_id`, `kind`
  (`register|login`), `state` (`json.dumps` del state fido2),
  `created_at`, `expires_at`.
- `ttl_attribute: expires_at` = now + 5 min: AWS borra los expirados sin
  WCU.
- **Single-use**: `ChallengeService.get_and_consume` hace `GetItem` +
  `DeleteItem` (el row se borra tras leerlo, exitoso o no). Si no existe /
  expiro -> `WEBAUTHN_CHALLENGE_NOT_FOUND`.
- Recurso: `serverless/lambda/resources/dynamodb/webauthn-challenges.yaml`.

## RP_ID por env (decision 4/5, AC-26)

WebAuthn exige que el RP_ID sea sufijo del origin. El `WEBAUTHN_RP_ID` es
**distinto por env** (env vars del manifest):

| Env | RP_ID | Origins cubiertos |
|---|---|---|
| prod | `the-full-stack.com` | apex + www + los 6 niches (`*.portfolio.the-full-stack.com`) |
| dev | `portfolio.dev.the-full-stack.com` | los niches `*.portfolio.dev.the-full-stack.com` + localhost:9970 |
| stage | `portfolio.stage.the-full-stack.com` | los niches `*.portfolio.stage.the-full-stack.com` |

**Implicancia**: un passkey registrado en `dev` NO migra a `prod` (y
viceversa). En prod su `allowCredentials` queda vacio y
`navigator.credentials.get()` falla en el cliente. Es esperado y correcto
(AC-26).

## Clone detection por sign_count (decision 14, AC-15)

El WebAuthn standard pide guardar el `sign_count` del authenticator y
validar que cada assertion lo trae mayor que el guardado. fido2 NO valida
la regresion — lo hace `verify_authentication`:

```python
if stored_count > 0 and new_sign_count <= stored_count:
    raise WebauthnCloneError(..., credential_id=matched_id)
```

`WebauthnCloneError` (subclase de `WebauthnVerifyError`) lleva el
`credential_id` para que `WebauthnService.verify_login` marque ese
credential `disabled_at=now()` y re-lance. El controller traduce a
`401 WEBAUTHN_CLONE_DETECTED` + audit `webauthn.login.clone_detected`. La
deshabilitacion es **SIEMPRE** (no opcional); la reactivacion solo via un
endpoint admin futuro. En login exitoso normal: `update_sign_count` avanza
el contador guardado.

## User verification (decision 6)

- Register: `UserVerificationRequirement.PREFERRED` +
  `ResidentKeyRequirement.PREFERRED`.
- Login: `UserVerificationRequirement.REQUIRED`.

Trade-off: algunos YubiKeys hardware-only (sin biometric/PIN) pueden
fallar en login si no soportan UV; la seguridad lo justifica.

## Persistencia del credential

`verify_registration` retorna `{credential_id, public_key, sign_count,
aaguid, attestation_format, transports}`:

- `public_key` se serializa con **CBOR** (`fido2.cbor.encode`) y se guarda
  en `auth_webauthn_credentials.public_key` (BYTEA). Al verificar el login
  se reconstruye con `CoseKey.parse(cbor.decode(...))`.
- `credential_id` (BYTEA, UNIQUE) y `sign_count` (INT default 0).
- AC-27: registrar el PRIMER metodo MFA del user (`total_mfa: 0 -> 1`)
  revoca las sesiones previas via `SessionService.revoke_all_for_user`
  (ver [04-mfa.md](04-mfa.md#ac-27)).

`list-credentials` (GET) devuelve `[{credential_id, nickname, transports,
created_at, last_used_at}, ...]`. `delete-credential` aplica el guard
transversal `MUST_KEEP_ONE_MFA_METHOD` (`count_active <= 1` -> 409) y
devuelve `404 NOT_FOUND` si el credential no existe o es de otro user
(anti-enumeration, AC-25).

## Las 6 actions de `webauthn`

| operation.action | Metodo | Que hace |
|---|---|---|
| `webauthn.register-options` | POST | Challenge + options para create(); guarda state en DDB |
| `webauthn.register-verify` | POST | Valida attestation, persiste credential, borra challenge |
| `webauthn.login-options` | POST | Challenge + allowCredentials para get(); guarda state |
| `webauthn.login-verify` | POST | Valida assertion + clone check, emite access+refresh |
| `webauthn.list-credentials` | GET | Lista credentials activos del user |
| `webauthn.delete-credential` | POST | Borra un credential (guard MUST_KEEP_ONE + 404 anti-enum) |

## Codigos de error

| Codigo | Significado |
|---|---|
| `WEBAUTHN_CHALLENGE_NOT_FOUND` | challenge_id no esta en DDB o expiro |
| `WEBAUTHN_CLONE_DETECTED` | sign_count <= stored -> credential disabled |
| `MUST_KEEP_ONE_MFA_METHOD` | delete dejaria al user con total_mfa==0 (transversal) |
| `NOT_FOUND` | credential inexistente / de otro user (anti-enumeration) |

## Gotcha — fido2 1.2 + soft-webauthn en tests unit

`soft-webauthn 0.1.4` es **incompatible** con `RegistrationResponse.
from_dict` / `AuthenticationResponse.from_dict` de fido2 1.2 (el shape del
PublicKeyCredential JSON cambio). Por eso los unit tests **mockean el
boundary `Fido2Server`** (no usan SoftWebauthnDevice contra el codigo
real). Las firmas validadas en el spike (decision 4): `register_begin /
register_complete` y `authenticate_begin / authenticate_complete`, con el
`state` como dict JSON-serializable (NO bytes) que se persiste en DDB.

---

[< README](README.md) — knowledge tree del dominio auth.
