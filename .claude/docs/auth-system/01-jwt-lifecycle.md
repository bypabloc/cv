# JWT lifecycle — temp / access / refresh

## Tres tipos de JWT

| Tipo | TTL | Estado | Uso |
|------|-----|--------|-----|
| `temp` | 5 min | Stateless + rolling | Vive entre pasos de un flujo (login/verify) |
| `access` | 15 min | Stateless con blacklist | Auth de cada request normal del dashboard |
| `refresh` | 30 dias | Stateful (`family_id` + rotation) | Renueva el access cuando expira |

Todos firmados con HS256. Secret: `/portfolio/${stage}/jwt-secret`
(SSM SecureString + KMS). Leido en cold start con `@cached_property` en
`AppConfig.jwt_secret` — NUNCA env var directa.

## Claims canonicos

```python
class JwtClaims(BaseModel):
    sub: UUID                          # subject = user_id (NO email)
    jti: UUID                          # JWT ID (uuidv7)
    typ: Literal['temp', 'access', 'refresh']
    iat: int                           # issued at (unix)
    exp: int                           # expires at (unix)
    iss: str = 'portfolio-auth'
    aud: str = 'portfolio'
    flow: str | None = None            # solo en typ=temp
    step: int | None = None            # solo en typ=temp
    family_id: UUID | None = None      # solo en typ=refresh
```

Decision: el JWT contiene SOLO `sub` (user_id) como identificador. El
email NO viaja en el token — JWT no es secreto (jwt.io lo decodifica) y
filtrarlo via Referer/logs/history expondria PII. Los Lambdas que
necesiten email hacen lookup a Neon.

## Rolling temp JWT (entre pasos del flujo)

Cada API del flujo:

1. Recibe `temp_token` en el body.
2. Verifica signature + exp + `typ='temp'` + NOT in blacklist.
3. Blacklistea el `jti` viejo en DDB con `TTL=exp` original.
4. Ejecuta el step (verificar code, set password, ...).
5. Si NO es paso terminal: emite un nuevo `temp` con `now+5min` y
   `step=step+1`. Lo devuelve en el body.
6. Si ES terminal: emite `access` + `refresh` (NO temp). Frontend
   borra el temp_token y persiste access/refresh.

Beneficio: si el user esta inactivo 5 min, el JWT expira. Si intenta
replay (reusar el viejo), falla por blacklist.

## Access JWT

- Stateless. El Lambda solo verifica signature + exp + aud + lookup
  `jti` en `portfolio-jwt-blacklist-${stage}`.
- Si el `jti` esta en blacklist con `revoked_at`: `401
  TOKEN_BLACKLISTED`.
- Logout pone el `jti` en blacklist.

## Refresh JWT con `family_id` (token theft detection)

Cada login emite un `family_id` nuevo (uuidv7). Cada uso del refresh
ROTA: blacklistea el actual, emite uno nuevo con el MISMO `family_id`.

Detection: si llega un refresh con `jti` ya blacklisteado (es decir, ya
fue rotado), se considera **token theft**:

1. Query GSI `by_family_id` con `KeyConditionExpression='family_id =
   :fid'` (devuelve lista de `jti`).
2. Blacklistea TODOS los `jti` de esa familia (BatchWriteItem paginando
   de a 25).
3. Devuelve `401 TOKEN_REUSE_DETECTED`.
4. Audit log `session.refresh.reuse_detected`.

Limite operativo: `MAX_FAMILY_SIZE = 10` (cap defensivo; en uso normal
1-3 refresh activos). Si Query devuelve >10, log `family.oversized` y
revoca igual.

## Logout

Recibe access JWT en el body. Opcionalmente refresh JWT:

1. Verifica access -> obtiene `jti_access` + `sub` (user_id).
2. Blacklistea `jti_access` con `reason='logout'`.
3. Si llega refresh: blacklistea TODOS los `jti` de su `family_id`.
4. Devuelve `204`.

Idempotente: si el `jti` ya esta blacklisted, devuelve `204` sin error
(AC-23).

## Tabla DynamoDB `portfolio-jwt-blacklist-${stage}`

```
PK: jti (S)        -- UUID v7 string
TTL: exp           -- unix; AWS borra el item
GSI by_family_id:  -- KEYS_ONLY (solo necesitamos jti para revocar)
  PK: family_id (S)
```

Schema del item:

```jsonc
{
  "jti": "01H9X...uuid",
  "user_id": "01H9V...",
  "typ": "access",                // 'temp'|'access'|'refresh'
  "family_id": "01H9W...",        // solo si typ=refresh
  "revoked_at": 1717000000,       // unix
  "reason": "logout",             // 'logout'|'rotation'|'reuse'|'forced'
  "exp": 1717003600               // unix; TTL attribute
}
```

## Errores tipados

| Excepcion | Cuando | HTTP |
|-----------|--------|------|
| `JwtExpiredError` | exp < now | 401 |
| `JwtInvalidError` | signature/aud/typ mismatch | 401 |
| `JwtRevokedError` | jti en blacklist | 401 |

Implementadas en `shared.auth.jwt`. Los services las propagan; los
controllers las traducen a `{error: 'TEMP_TOKEN_EXPIRED'|'TOKEN_INVALID'|
'TOKEN_BLACKLISTED'}`.
