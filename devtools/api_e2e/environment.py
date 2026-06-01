"""Acceso al entorno desplegado: bypass firmado + Neon URL (SSM) + seed.

HERMETICO: ningun valor de secreto (clave privada de bypass, connection
string de Neon) se imprime jamas en stdout/stderr. La Neon URL se resuelve
de SSM via boto3; el token de bypass se FIRMA localmente con la clave
privada Ed25519 de `docker/env/dev-cli/.{env}` (extraida sin volcar el
.env). Cumple `.claude/rules/env-files.md`.

El seed de Neon es necesario para el paso verify-code del flujo auth: el
backend NO devuelve el code en claro (solo el hash SHA-256 va a Neon).
Tecnica: generamos un plaintext conocido, calculamos su SHA-256 y
UPDATEamos el `code_hash` de la fila vigente, luego enviamos el plaintext.
"""

from __future__ import annotations

import hashlib
import time
from typing import Any

import boto3
import psycopg

from api_e2e.config import AWS_REGION
from api_e2e.config import neon_ssm_path
from shared.bypass_token import sign_bypass_token
from shared.paths import PROJECT_ROOT


_PRIVATE_KEY_VAR = 'TURNSTILE_BYPASS_PRIVATE_KEY'


class Environment:
    """Resuelve secretos del entorno y opera Neon para seed + cleanup."""

    def __init__(self, env: str, *, aws_profile: str | None = None) -> None:
        self._env = env
        session = boto3.Session(profile_name=aws_profile)
        self._ssm = session.client('ssm', region_name=AWS_REGION)
        self._neon_url: str | None = None
        self._private_key: str | None = None

    # --- Bypass firmado (nunca a stdout) ---

    def _bypass_private_key(self) -> str | None:
        """Lee la clave PRIVADA Ed25519 de docker/env/dev-cli/.{env}.

        Extrae SOLO la key (no vuelca el .env, ver env-files.md). El valor
        vive en proceso; NUNCA se imprime. None si no esta configurada.
        """
        if self._private_key is None:
            self._private_key = ''
            path = PROJECT_ROOT / 'docker' / 'env' / 'dev-cli' / f'.{self._env}'
            if path.exists():
                prefix = f'{_PRIVATE_KEY_VAR}='
                for line in path.read_text().splitlines():
                    if line.startswith(prefix):
                        self._private_key = line[len(prefix) :].strip()
                        break
        return self._private_key or None

    def bypass_token(self) -> str | None:
        """Firma un token de bypass efimero (None si no hay clave privada).

        El token lo verifica el backend con la clave PUBLICA (SSM). TTL 300s
        cubre la duracion de los flujos encadenados del harness.
        """
        private_key = self._bypass_private_key()
        if not private_key:
            return None
        return sign_bypass_token(
            stage=self._env,
            private_key_b64=private_key,
            now=int(time.time()),
        )

    def _neon(self) -> str:
        if self._neon_url is None:
            self._neon_url = self._ssm.get_parameter(
                Name=neon_ssm_path(self._env),
                WithDecryption=True,
            )['Parameter']['Value']
        return self._neon_url

    # --- Neon: seed del code para el paso verify ---

    def seed_code(self, *, user_id: str, kind: str, plaintext: str) -> bool:
        """Fija el code_hash de la fila vigente a sha256(plaintext).

        Filtra por user_id + kind + consumed_at IS NULL, resetea attempts
        y refresca expires_at. Devuelve True si actualizo >=1 fila.
        """
        digest = hashlib.sha256(plaintext.encode('utf-8')).digest()
        sql = (
            'UPDATE auth_email_codes '
            'SET code_hash = %s, attempts = 0, '
            "expires_at = now() + interval '10 minutes' "
            'WHERE user_id = %s AND kind = %s AND consumed_at IS NULL'
        )
        return self._exec(sql, (digest, user_id, kind)) > 0

    def find_user_id(self, email: str) -> str | None:
        """user_id (uuid str) del email, o None si no existe."""
        rows = self._query(
            'SELECT id FROM auth_users WHERE email = %s',
            (email.lower(),),
        )
        return str(rows[0][0]) if rows else None

    # --- Cleanup ---

    def cleanup_users(self, emails: list[str]) -> int:
        """Borra (hard) los users de prueba + sus filas hijas en Neon."""
        if not emails:
            return 0
        ids = [
            r[0]
            for r in self._query(
                'SELECT id FROM auth_users WHERE email = ANY(%s)',
                ([e.lower() for e in emails],),
            )
        ]
        if not ids:
            return 0
        # NO incluye auth_user_admin_actions: esa tabla referencia por
        # actor_user_id/target_user_id (no user_id), y el user sintetico
        # nunca es actor ni target ahi -> no deja filas.
        children = (
            'auth_email_codes',
            'auth_magic_links',
            'auth_credentials',
            'auth_mfa_methods',
            'auth_mfa_recovery_codes',
            'auth_webauthn_credentials',
            'auth_user_sessions',
            'auth_audit_log',
            'auth_user_consent_log',
        )
        total = 0
        for table in children:
            total += self._exec(
                f'DELETE FROM {table} WHERE user_id = ANY(%s)',  # noqa: S608
                (ids,),
                ignore_missing=True,
            )
        total += self._exec(
            'DELETE FROM auth_users WHERE id = ANY(%s)',
            (ids,),
        )
        return total

    def cleanup_tracking(self, session_ids: list[str]) -> int:
        """Borra los tracking events + sessions sinteticos creados."""
        if not session_ids:
            return 0
        n = 0
        for table in ('tracking_events', 'session_visits', 'sessions'):
            n += self._exec(
                f'DELETE FROM {table} WHERE session_id = ANY(%s)',  # noqa: S608
                (session_ids,),
                ignore_missing=True,
            )
        return n

    def cleanup_contacts(self, emails: list[str]) -> int:
        """Borra los contacts sinteticos creados (por email)."""
        if not emails:
            return 0
        return self._exec(
            'DELETE FROM contacts WHERE email = ANY(%s)',
            ([e.lower() for e in emails],),
            ignore_missing=True,
        )

    # --- Internos psycopg ---

    def _exec(
        self,
        sql: str,
        params: tuple,
        *,
        ignore_missing: bool = False,
    ) -> int:
        try:
            with (
                psycopg.connect(self._neon(), connect_timeout=15) as conn,
                conn.cursor() as cur,
            ):
                cur.execute(sql, params)
                return cur.rowcount
        except (psycopg.errors.UndefinedTable, psycopg.errors.UndefinedColumn):
            if ignore_missing:
                return 0
            raise

    def _query(self, sql: str, params: tuple) -> list[tuple[Any, ...]]:
        with (
            psycopg.connect(self._neon(), connect_timeout=15) as conn,
            conn.cursor() as cur,
        ):
            cur.execute(sql, params)
            return cur.fetchall()
