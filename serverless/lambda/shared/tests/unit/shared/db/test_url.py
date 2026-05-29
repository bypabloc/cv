"""Unit tests para shared.db.url (resolucion de la connection string)."""

from __future__ import annotations

import pytest
import shared.db.url as url_mod

pytestmark = pytest.mark.unit


class TestNormalize:
    """_normalize - normaliza la URL al driver psycopg v3."""

    def test_when_plain_postgresql_scheme_then_rewrites_to_psycopg(
        self,
    ) -> None:
        """
        Given una URL con scheme 'postgresql://',
        When _normalize la procesa,
        Then el scheme pasa a 'postgresql+psycopg://'.
        """
        result = url_mod._normalize('postgresql://user:p@host/db')

        assert result == 'postgresql+psycopg://user:p@host/db'

    def test_when_already_psycopg_scheme_then_unchanged(self) -> None:
        """
        Given una URL ya con scheme 'postgresql+psycopg://',
        When _normalize la procesa,
        Then se devuelve sin cambios.
        """
        original = 'postgresql+psycopg://user:p@host/db'

        result = url_mod._normalize(original)

        assert result == original


class TestResolveDatabaseUrl:
    """resolve_database_url - DATABASE_URL del entorno o SSM."""

    def test_when_database_url_in_env_then_returns_normalized(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given DATABASE_URL seteada en el entorno,
        When resolve_database_url,
        Then la devuelve normalizada al driver psycopg (sin tocar SSM).
        """
        monkeypatch.setenv('DATABASE_URL', 'postgresql://u:p@h/db')

        result = url_mod.resolve_database_url()

        assert result == 'postgresql+psycopg://u:p@h/db'

    def test_when_no_database_url_then_resolves_from_ssm(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given DATABASE_URL ausente pero SSM_NEON_URL_PATH seteada,
        When resolve_database_url,
        Then resuelve el parametro SSM y normaliza el resultado.
        """
        monkeypatch.delenv('DATABASE_URL', raising=False)
        monkeypatch.setenv('SSM_NEON_URL_PATH', '/portfolio/dev/neon-url')
        monkeypatch.setattr(
            'shared.aws.ssm.get_secret',
            lambda path: 'postgresql://ssm-user:p@ssm-host/db',
        )

        result = url_mod.resolve_database_url()

        assert result == 'postgresql+psycopg://ssm-user:p@ssm-host/db'

    def test_when_no_url_and_no_ssm_path_then_raises(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given ni DATABASE_URL ni SSM_NEON_URL_PATH seteadas,
        When resolve_database_url,
        Then lanza RuntimeError (config incompleta).
        """
        monkeypatch.delenv('DATABASE_URL', raising=False)
        monkeypatch.delenv('SSM_NEON_URL_PATH', raising=False)

        with pytest.raises(RuntimeError, match='SSM_NEON_URL_PATH'):
            url_mod.resolve_database_url()


class TestEnsureDatabaseUrl:
    """ensure_database_url - garantiza DATABASE_URL en el entorno."""

    def test_when_database_url_present_then_unchanged(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given DATABASE_URL ya seteada,
        When ensure_database_url,
        Then no la sobrescribe (es no-op).
        """
        monkeypatch.setenv('DATABASE_URL', 'postgresql+psycopg://u:p@h/db')

        url_mod.ensure_database_url()

        import os

        assert os.environ['DATABASE_URL'] == 'postgresql+psycopg://u:p@h/db'

    def test_when_database_url_absent_then_set_from_ssm(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given DATABASE_URL ausente y SSM_NEON_URL_PATH seteada,
        When ensure_database_url,
        Then DATABASE_URL queda en el entorno con el valor resuelto.
        """
        monkeypatch.delenv('DATABASE_URL', raising=False)
        monkeypatch.setenv('SSM_NEON_URL_PATH', '/portfolio/neon-url')
        monkeypatch.setattr(
            'shared.aws.ssm.get_secret',
            lambda path: 'postgresql://u:p@h/db',
        )

        url_mod.ensure_database_url()

        import os

        assert os.environ['DATABASE_URL'] == 'postgresql+psycopg://u:p@h/db'
