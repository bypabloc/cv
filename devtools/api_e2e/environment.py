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
import secrets
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
        self._lambda = session.client('lambda', region_name=AWS_REGION)
        self._dynamodb = session.client('dynamodb', region_name=AWS_REGION)
        self._neon_url: str | None = None
        self._private_key: str | None = None
        self._rate_limit_table: str | None = None

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

        El token lo verifica el backend con la clave PUBLICA (SSM). TTL 1800s
        (30 min): el harness completo (auth + users + admin con cold restart)
        encadena decenas de invocaciones que superan el default de 300s; el
        backend solo valida `now >= exp` (sin tope de TTL). Aplica solo a
        dev/stage.
        """
        private_key = self._bypass_private_key()
        if not private_key:
            return None
        return sign_bypass_token(
            stage=self._env,
            private_key_b64=private_key,
            now=int(time.time()),
            ttl=1800,
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

    def seed_magic_link(
        self,
        *,
        user_id: str,
        kind: str,
        plaintext: str,
    ) -> bool:
        """Fija el token_hash del magic-link vigente a sha256(plaintext).

        Tras un register.start / login.start existe una fila en
        auth_magic_links (kind=register|login, consumed_at IS NULL). El
        plain del token NO vuelve en la respuesta (solo viaja por email);
        para probar verify-magic-link sin leer el email, reescribimos su
        hash a uno conocido. Refresca expires_at. True si actualizo >=1.
        """
        digest = hashlib.sha256(plaintext.encode('utf-8')).digest()
        sql = (
            'UPDATE auth_magic_links '
            'SET token_hash = %s, '
            "expires_at = now() + interval '15 minutes' "
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

    def user_email(self, user_id: str) -> str | None:
        """Email actual del user (para verificar change-email)."""
        rows = self._query(
            'SELECT email FROM auth_users WHERE id = %s',
            (user_id,),
        )
        return str(rows[0][0]) if rows else None

    def user_status(self, user_id: str) -> str | None:
        """Status actual del user (active/disabled/...), o None si borrado."""
        rows = self._query(
            'SELECT status, deleted_at FROM auth_users WHERE id = %s',
            (user_id,),
        )
        if not rows:
            return None
        status, deleted_at = rows[0]
        return 'deleted' if deleted_at is not None else str(status)

    def session_ids(self, user_id: str) -> list[str]:
        """IDs de las sesiones activas del user (auth_user_sessions).

        Una sesion activa = fila existente: revoke_session/force-logout
        BORRAN la fila (no hay columna revoked_at). Orden por created_at
        para que el [0] sea la mas vieja.
        """
        rows = self._query(
            'SELECT id FROM auth_user_sessions '
            'WHERE user_id = %s ORDER BY created_at',
            (user_id,),
        )
        return [str(r[0]) for r in rows]

    # --- Admin whitelist (SSM) + cold restart del Lambda users ---

    def _admin_emails_path(self) -> str:
        """SSM path de la whitelist de admins por stage."""
        return f'/portfolio/{self._env}/admin-emails'

    def read_admin_emails(self) -> str:
        """Valor crudo (CSV) de la whitelist SSM. NUNCA se imprime."""
        return self._ssm.get_parameter(
            Name=self._admin_emails_path(),
            WithDecryption=True,
        )['Parameter']['Value']

    def write_admin_emails(self, value: str) -> None:
        """Sobrescribe la whitelist SSM (SecureString). value NO se imprime."""
        self._ssm.put_parameter(
            Name=self._admin_emails_path(),
            Value=value,
            Type='SecureString',
            Overwrite=True,
        )

    def bust_users_cache(self) -> None:
        """Fuerza un cold start del Lambda users (recicla el contenedor).

        La whitelist de admins se cachea module-level por contenedor (TTL
        300s). Tras promover un email en SSM, el contenedor caliente sigue
        con el cache viejo -> 404. Cambiar una env var EFIMERA recicla el
        contenedor (cold start -> cache fresco). La env var se BORRA en
        restore (`clear_users_cache_buster`) para no dejar drift de config.
        """
        fn = f'portfolio-users-{self._env}'
        current = self._lambda.get_function_configuration(FunctionName=fn)
        env_vars = dict(current.get('Environment', {}).get('Variables', {}))
        # Marca unica por corrida (token_hex en vez de timestamp: el harness
        # corre con secrets, no con reloj).
        env_vars['E2E_CACHE_BUSTER'] = secrets.token_hex(4)
        self._lambda.update_function_configuration(
            FunctionName=fn,
            Environment={'Variables': env_vars},
        )
        self._lambda.get_waiter('function_updated').wait(FunctionName=fn)

    def clear_users_cache_buster(self) -> None:
        """Quita la env var efimera para dejar la config como estaba."""
        fn = f'portfolio-users-{self._env}'
        current = self._lambda.get_function_configuration(FunctionName=fn)
        env_vars = dict(current.get('Environment', {}).get('Variables', {}))
        if env_vars.pop('E2E_CACHE_BUSTER', None) is None:
            return
        self._lambda.update_function_configuration(
            FunctionName=fn,
            Environment={'Variables': env_vars},
        )
        self._lambda.get_waiter('function_updated').wait(FunctionName=fn)

    # --- Rate-limit blacklist de IPs TEST-NET (DynamoDB) ---

    def _rate_limit_table_name(self) -> str:
        """Nombre de la tabla rate-limit-rules (resuelto via SSM, cacheado)."""
        if self._rate_limit_table is None:
            self._rate_limit_table = self._ssm.get_parameter(
                Name=f'/portfolio/{self._env}/dynamodb/rate-limit-rules/name',
            )['Parameter']['Value']
        return self._rate_limit_table

    def cleanup_rate_limit_blacklist(self) -> int:
        """Borra las ip_blacklist auto-creadas para las IPs TEST-NET del pool.

        El bot-detection auto-blacklistea (24h) una IP con 3+ tokens validos
        en 60s. El harness rota IPs de TEST-NET (RFC 5737); corridas con
        samples>=3 al mismo endpoint pueden auto-blacklistear alguna, y la
        rule persiste 24h -> 403 intermitente en corridas siguientes cuando
        el round-robin la reusa. Esto borra esas rules (solo las del pool
        TEST-NET del harness; NO toca blacklists reales). Devuelve cuantas
        borro. Best-effort: un fallo no aborta el run.
        """
        table = self._rate_limit_table_name()
        prefixes = ('ip#198.51.100.', 'ip#203.0.113.', 'ip#192.0.2.')
        deleted = 0
        try:
            for prefix in prefixes:
                deleted += self._delete_rules_by_prefix(table, prefix)
        except Exception as exc:  # noqa: BLE001 -- best-effort
            print(
                f'  [WARN] cleanup blacklist parcial: '
                f'{type(exc).__name__}: {exc}'
            )
        return deleted

    def _delete_rules_by_prefix(self, table: str, prefix: str) -> int:
        """Scan begins_with(rule_key, prefix) + BatchDelete. Devuelve count."""
        deleted = 0
        start_key: dict[str, Any] | None = None
        while True:
            kwargs: dict[str, Any] = {
                'TableName': table,
                'FilterExpression': 'begins_with(rule_key, :p)',
                'ExpressionAttributeValues': {':p': {'S': prefix}},
                'ProjectionExpression': 'rule_key, kind',
            }
            if start_key:
                kwargs['ExclusiveStartKey'] = start_key
            resp = self._dynamodb.scan(**kwargs)
            for item in resp.get('Items', []):
                self._dynamodb.delete_item(
                    TableName=table,
                    Key={
                        'rule_key': item['rule_key'],
                        'kind': item['kind'],
                    },
                )
                deleted += 1
            start_key = resp.get('LastEvaluatedKey')
            if not start_key:
                return deleted

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
