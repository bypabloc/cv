"""JWT HS256 — issue + verify para temp/access/refresh.

3 tipos de tokens:
- `temp`: 5 min, rolling refresh entre pasos de un flujo (register/login/
  verify). Claims extras: `flow`, `step`.
- `access`: 15 min, stateless con verificacion blacklist en DDB.
- `refresh`: 30 dias, rotation + `family_id` para detectar token reuse.

El secret se lee de SSM `/portfolio/${stage}/jwt-secret` (SecureString +
KMS) en cold start de cada Lambda — este modulo recibe el secret como
argumento (NO lo lee directo).

Los claims contienen SOLO `sub` (user_id). El email NUNCA viaja en el
JWT (JWT no es secreto: jwt.io lo decodifica).
"""

from typing import Any, Literal
from uuid import UUID

import jwt as pyjwt
from shared.auth.constants import (
    ACCESS_TTL,
    DEFAULT_AUDIENCE,
    DEFAULT_ISSUER,
    JWT_ALGORITHM,
    REFRESH_TTL,
    TEMP_TTL,
)
from shared.core import (
    ApplicationError,
    BaseModel,
    ConfigDict,
    new_uuidv7,
)

__all__ = [
    'JwtClaims',
    'JwtError',
    'JwtExpiredError',
    'JwtInvalidError',
    'JwtRevokedError',
    'issue_access_jwt',
    'issue_refresh_jwt',
    'issue_temp_jwt',
    'verify_jwt',
]


JwtType = Literal['temp', 'access', 'refresh']


class JwtClaims(BaseModel):
    """Claims canonicos del JWT.

    Subset de RFC 7519 + custom (`flow`, `step`, `family_id`). Sin PII.
    Pydantic v2 con `model_config` para alias del campo.
    """

    sub: UUID  # subject = user_id (NO email)
    jti: UUID  # JWT ID (uuidv7)
    typ: JwtType
    iat: int  # issued at (unix seconds)
    exp: int  # expires at (unix seconds)
    iss: str = DEFAULT_ISSUER
    aud: str = DEFAULT_AUDIENCE
    # custom
    flow: str | None = None  # solo en typ=temp
    step: int | None = None  # solo en typ=temp
    family_id: UUID | None = None  # solo en typ=refresh

    model_config = ConfigDict(extra='forbid')


class JwtError(ApplicationError):
    """Base de errores de JWT."""

    default_code = 'JWT_ERROR'
    status_code = 401


class JwtExpiredError(JwtError):
    """exp < now."""

    default_code = 'JWT_EXPIRED'


class JwtInvalidError(JwtError):
    """Signature mismatch, aud mismatch, typ mismatch, malformed."""

    default_code = 'JWT_INVALID'


class JwtRevokedError(JwtError):
    """`jti` en la blacklist DDB.

    Se levanta desde el Lambda (NO desde este modulo) tras un lookup
    `GetItem` en `portfolio-jwt-blacklist-${stage}`. Aqui solo existe
    para que el caller pueda importarlo desde un solo lugar.
    """

    default_code = 'JWT_REVOKED'


def _now() -> int:
    """Unix seconds. Aislado para mockear con freezegun en tests."""
    import time

    return int(time.time())


def _encode(claims: JwtClaims, secret: str) -> str:
    """Helper interno: serializa JwtClaims a JSON-safe dict y firma."""
    payload: dict[str, Any] = {
        'sub': str(claims.sub),
        'jti': str(claims.jti),
        'typ': claims.typ,
        'iat': claims.iat,
        'exp': claims.exp,
        'iss': claims.iss,
        'aud': claims.aud,
    }
    if claims.flow is not None:
        payload['flow'] = claims.flow
    if claims.step is not None:
        payload['step'] = claims.step
    if claims.family_id is not None:
        payload['family_id'] = str(claims.family_id)
    return pyjwt.encode(payload, secret, algorithm=JWT_ALGORITHM)


def issue_temp_jwt(
    *,
    user_id: UUID,
    flow: str,
    step: int,
    secret: str,
    ttl: int = TEMP_TTL,
    issuer: str = DEFAULT_ISSUER,
    audience: str = DEFAULT_AUDIENCE,
) -> tuple[str, JwtClaims]:
    """Emite un JWT temporal (rolling refresh entre pasos del flujo).

    Returns:
        (token_string, claims) — el caller persiste o devuelve el token
        al cliente, y usa `claims.jti` para blacklistear el anterior.
    """
    now = _now()
    claims = JwtClaims(
        sub=user_id,
        jti=UUID(new_uuidv7()),
        typ='temp',
        iat=now,
        exp=now + ttl,
        iss=issuer,
        aud=audience,
        flow=flow,
        step=step,
    )
    return _encode(claims, secret), claims


def issue_access_jwt(
    *,
    user_id: UUID,
    secret: str,
    ttl: int = ACCESS_TTL,
    issuer: str = DEFAULT_ISSUER,
    audience: str = DEFAULT_AUDIENCE,
) -> tuple[str, JwtClaims]:
    """Emite un JWT access (15 min, stateless con blacklist DDB).

    El access NO incluye email ni datos de perfil. El consumidor
    (dashboard) obtiene esos datos del response del endpoint de login/
    verify y los persiste en su store.
    """
    now = _now()
    claims = JwtClaims(
        sub=user_id,
        jti=UUID(new_uuidv7()),
        typ='access',
        iat=now,
        exp=now + ttl,
        iss=issuer,
        aud=audience,
    )
    return _encode(claims, secret), claims


def issue_refresh_jwt(
    *,
    user_id: UUID,
    family_id: UUID,
    secret: str,
    ttl: int = REFRESH_TTL,
    issuer: str = DEFAULT_ISSUER,
    audience: str = DEFAULT_AUDIENCE,
) -> tuple[str, JwtClaims]:
    """Emite un JWT refresh (30 dias, rotation + `family_id`).

    `family_id` agrupa todos los refresh rotados del mismo session — si
    llega un refresh ya consumido (blacklisted), el Lambda detecta reuso
    y revoca toda la familia via Query GSI `by_family_id`.
    """
    now = _now()
    claims = JwtClaims(
        sub=user_id,
        jti=UUID(new_uuidv7()),
        typ='refresh',
        iat=now,
        exp=now + ttl,
        iss=issuer,
        aud=audience,
        family_id=family_id,
    )
    return _encode(claims, secret), claims


def verify_jwt(
    token: str,
    *,
    secret: str,
    expected_typ: JwtType | None = None,
    audience: str = DEFAULT_AUDIENCE,
    issuer: str = DEFAULT_ISSUER,
) -> JwtClaims:
    """Valida signature + exp + aud + iss + (opcional) typ.

    NO verifica blacklist — eso lo hace el Lambda contra DynamoDB con el
    `jti` retornado.

    Raises:
        JwtExpiredError: si exp < now.
        JwtInvalidError: si signature/aud/iss/typ mismatch o el token
            esta malformed.
    """
    try:
        payload: dict[str, Any] = pyjwt.decode(
            token,
            secret,
            algorithms=[JWT_ALGORITHM],
            audience=audience,
            issuer=issuer,
            options={
                'require': ['sub', 'jti', 'typ', 'iat', 'exp', 'iss', 'aud']
            },
        )
    except pyjwt.ExpiredSignatureError as exc:
        raise JwtExpiredError('JWT expired') from exc
    except pyjwt.InvalidTokenError as exc:
        # Cubre InvalidSignatureError, InvalidAudienceError, InvalidIssuerError,
        # DecodeError, MissingRequiredClaimError, etc.
        raise JwtInvalidError(f'JWT invalid: {exc}') from exc

    typ_value = payload.get('typ')
    if expected_typ is not None and typ_value != expected_typ:
        raise JwtInvalidError(
            f'JWT typ mismatch: expected {expected_typ!r}, got {typ_value!r}',
        )

    try:
        return JwtClaims(
            sub=UUID(payload['sub']),
            jti=UUID(payload['jti']),
            typ=payload['typ'],
            iat=int(payload['iat']),
            exp=int(payload['exp']),
            iss=payload['iss'],
            aud=payload['aud'],
            flow=payload.get('flow'),
            step=payload.get('step'),
            family_id=UUID(payload['family_id'])
            if 'family_id' in payload
            else None,
        )
    except (ValueError, KeyError, TypeError) as exc:
        raise JwtInvalidError(f'JWT claims malformed: {exc}') from exc
