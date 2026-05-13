"""Unit tests for shared.console output stream discipline.

Path mirroring: devtools/shared/console.py -> this file.

Verifica que header/info/ok/warn/err/step van a STDERR, no stdout. Esto
mantiene stdout limpio para JSON / data output, asi callers pueden hacer
``cmd --output=json | jq ...`` sin que los banners contaminen el parse.
"""

from collections.abc import Callable
from typing import Any

import pytest


pytestmark = pytest.mark.unit


@pytest.fixture
def captured(
    capsys: pytest.CaptureFixture[str],
) -> Callable[..., pytest.CaptureResult[str]]:
    """Devuelve un closure que ejecuta una funcion y devuelve (out, err)."""

    def _run(
        fn: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> pytest.CaptureResult[str]:
        fn(*args, **kwargs)
        return capsys.readouterr()

    return _run


class TestConsoleGoesToStderr:
    """All decorative helpers route to stderr (the rule that keeps
    stdout clean for JSON/data piping)."""

    def test_header_to_stderr(self, captured):
        from shared.console import header

        result = captured(header, 'titulo')
        assert result.out == ''
        assert 'titulo' in result.err

    def test_info_to_stderr(self, captured):
        from shared.console import info

        result = captured(info, 'mensaje informativo')
        assert result.out == ''
        assert 'mensaje informativo' in result.err
        assert '[INFO]' in result.err

    def test_ok_to_stderr(self, captured):
        from shared.console import ok

        result = captured(ok, 'todo bien')
        assert result.out == ''
        assert 'todo bien' in result.err
        assert '[OK]' in result.err

    def test_warn_to_stderr(self, captured):
        from shared.console import warn

        result = captured(warn, 'cuidado')
        assert result.out == ''
        assert '[WARN]' in result.err

    def test_err_to_stderr(self, captured):
        from shared.console import err

        result = captured(err, 'fallo')
        assert result.out == ''
        assert '[ERROR]' in result.err

    def test_step_to_stderr(self, captured):
        from shared.console import step

        result = captured(step, 'paso 1')
        assert result.out == ''
        assert '>>>' in result.err
        assert 'paso 1' in result.err

    def test_underscore_aliases_match_canonical(self, captured):
        # Los aliases _header, _info, etc. son los que usa la mayoria del
        # codebase. Deben comportarse identico (mismo stream).
        from shared.console import _err
        from shared.console import _header
        from shared.console import _info
        from shared.console import _ok
        from shared.console import _step
        from shared.console import _warn

        for fn, marker in [
            (_header, 'h'),
            (_info, 'i'),
            (_ok, 'o'),
            (_warn, 'w'),
            (_err, 'e'),
            (_step, 's'),
        ]:
            result = captured(fn, marker)
            assert result.out == '', f'{fn.__name__} fugo a stdout'
            assert marker in result.err, f'{fn.__name__} no escribio en stderr'


class TestColourReturnsString:
    """colour() es funcion pura: devuelve string, no escribe a ningun stream."""

    def test_colour_returns_string_with_codes(self, capsys):
        from shared.console import CYAN
        from shared.console import NC
        from shared.console import colour

        result = colour(CYAN, 'hola')
        captured = capsys.readouterr()
        assert result == f'{CYAN}hola{NC}'
        assert captured.out == ''
        assert captured.err == ''
