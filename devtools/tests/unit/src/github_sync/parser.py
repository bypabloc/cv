"""Unit tests for github_sync.parser.

Path mirroring: devtools/github_sync/parser.py -> this file.

Cubre el parser de .env: keys validas, valores vacios, comillas,
comentarios, errores. Hermetico: el parser solo se testea con strings
inventados (no se leen .env reales del proyecto).
"""

from pathlib import Path

import pytest

from github_sync.catalog import SYNCED_KEYS
from github_sync.parser import EnvParseError
from github_sync.parser import filter_catalog
from github_sync.parser import parse_env_file


pytestmark = pytest.mark.unit


def test_parse_extracts_simple_key_value(tmp_path: Path) -> None:
    """
    Given un .env con KEY=value,
    When parse_env_file,
    Then retorna {KEY: value}.
    """
    env = tmp_path / '.dev'
    env.write_text('BASE_DOMAIN=portfolio.dev.example.com\n', encoding='utf-8')
    result = parse_env_file(env)
    assert result == {'BASE_DOMAIN': 'portfolio.dev.example.com'}


def test_parse_ignores_comments_and_blank_lines(tmp_path: Path) -> None:
    """
    Given un .env con comentarios y lineas en blanco,
    When parse_env_file,
    Then las ignora.
    """
    env = tmp_path / '.dev'
    env.write_text(
        '# este es un comentario\n\nBASE_SCHEME=https\n  # leading whitespace\n',
        encoding='utf-8',
    )
    result = parse_env_file(env)
    assert result == {'BASE_SCHEME': 'https'}


def test_parse_strips_quotes(tmp_path: Path) -> None:
    """
    Given un .env con valores entre comillas,
    When parse_env_file,
    Then strippa las comillas.
    """
    env = tmp_path / '.dev'
    env.write_text(
        'A="dquoted"\nB=\'squoted\'\nC=mixed"chars\n',
        encoding='utf-8',
    )
    result = parse_env_file(env)
    assert result == {'A': 'dquoted', 'B': 'squoted', 'C': 'mixed"chars'}


def test_parse_allows_empty_value(tmp_path: Path) -> None:
    """
    Given KEY= (valor vacio),
    When parse_env_file,
    Then KEY existe con valor ''.
    """
    env = tmp_path / '.dev'
    env.write_text('APEX_DOMAIN=\n', encoding='utf-8')
    result = parse_env_file(env)
    assert result == {'APEX_DOMAIN': ''}


def test_parse_raises_on_missing_equals(tmp_path: Path) -> None:
    """
    Given una linea sin =,
    When parse_env_file,
    Then lanza EnvParseError SIN imprimir el contenido.
    """
    env = tmp_path / '.dev'
    env.write_text('not_a_valid_line\n', encoding='utf-8')
    with pytest.raises(EnvParseError, match='linea invalida'):
        parse_env_file(env)


def test_parse_raises_on_missing_file(tmp_path: Path) -> None:
    """
    Given un path inexistente,
    When parse_env_file,
    Then lanza FileNotFoundError.
    """
    with pytest.raises(FileNotFoundError):
        parse_env_file(tmp_path / 'no-such-file')


def test_filter_catalog_keeps_only_known_keys() -> None:
    """
    Given un dict con keys del catalogo + extras,
    When filter_catalog,
    Then retorna solo las del catalogo.
    """
    parsed = {
        'BASE_DOMAIN': 'x',
        'PROXY_PORT': '9970',  # NOT in catalog
        'PUBLIC_API_ENDPOINT': 'y',
        'TURNSTILE_ENABLED': 'true',  # NOT in catalog
    }
    result = filter_catalog(parsed, SYNCED_KEYS)
    assert result == {'BASE_DOMAIN': 'x', 'PUBLIC_API_ENDPOINT': 'y'}


def test_catalog_matches_example_keys_expectation() -> None:
    """
    Invariante: el catalogo SYNCED_KEYS contiene exactamente las 5 keys
    documentadas en docker/env/client/.example que afectan el build.

    Si alguien agrega una key nueva al .example, debe agregar tambien
    a SYNCED_KEYS o a IGNORED_KEYS (decision explicita).
    """
    expected = {
        'BASE_DOMAIN',
        'BASE_SCHEME',
        'APEX_DOMAIN',
        'PUBLIC_API_ENDPOINT',
        'PUBLIC_TURNSTILE_SITEKEY',
    }
    assert frozenset(expected) == SYNCED_KEYS
