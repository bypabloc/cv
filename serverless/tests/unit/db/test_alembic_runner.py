"""Unit tests de db.alembic_runner (wrapper de Alembic Config)."""

from __future__ import annotations

import pytest
from alembic.config import Config

from db import alembic_runner

pytestmark = pytest.mark.unit


class TestBuildConfig:
    """build_config - arma el Config de Alembic del schema unificado."""

    def test_when_called_then_returns_config_with_script_location(
        self,
    ) -> None:
        """
        Given build_config sin buffer,
        When se invoca,
        Then devuelve un Config con script_location apuntando al alembic/
        del modulo _shared/db.
        """
        cfg = alembic_runner.build_config()

        assert isinstance(cfg, Config)
        script_location = cfg.get_main_option('script_location')
        assert script_location is not None
        assert script_location.endswith('_shared/db/alembic')

    def test_when_out_buffer_given_then_config_writes_to_it(self) -> None:
        """
        Given un buffer pasado a build_config,
        When Alembic escribe a stdout del Config,
        Then el texto cae en ese buffer (no en sys.stdout).
        """
        import io

        buffer = io.StringIO()
        cfg = alembic_runner.build_config(out=buffer)

        cfg.print_stdout('linea de prueba')

        assert 'linea de prueba' in buffer.getvalue()


class TestCapture:
    """capture - ejecuta un comando Alembic capturando lo que imprime."""

    def test_when_callback_prints_then_capture_returns_text(self) -> None:
        """
        Given un callback que imprime via el Config recibido,
        When capture lo ejecuta,
        Then devuelve el texto impreso (stripped).
        """
        captured = alembic_runner.capture(
            lambda cfg: cfg.print_stdout('hola desde alembic')
        )

        assert captured == 'hola desde alembic'

    def test_when_callback_prints_nothing_then_capture_returns_empty(
        self,
    ) -> None:
        """
        Given un callback que no imprime nada,
        When capture lo ejecuta,
        Then devuelve string vacio.
        """
        captured = alembic_runner.capture(lambda _cfg: None)

        assert captured == ''
