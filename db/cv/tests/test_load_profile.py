"""@tests test_load_profile — parseo del profile.ts por el seed.

`profile.ts` no es YAML: es un objeto TS dentro de `ProfileSchema.parse(
{...})`. El seed lo parsea como YAML laxo, pero antes debe quitar los
comentarios de linea `//` (YAML usa `#`). Estos tests cubren el helper
`_strip_ts_line_comments` y la funcion `_load_profile` — ambos puros, sin
DB, asi que corren siempre (a diferencia de test_seed.py).
"""

from seed.seed_from_yaml import _load_profile
from seed.seed_from_yaml import _strip_ts_line_comments


def test_strip_ts_line_comments_removes_full_line_comment() -> None:
    """Given una linea que es solo un comentario `//`,
    When se procesa con _strip_ts_line_comments,
    Then la linea queda vacia.
    """
    # Arrange
    block = '  // comentario suelto'

    # Act
    result = _strip_ts_line_comments(block)

    # Assert
    assert result == ''


def test_strip_ts_line_comments_removes_trailing_comment() -> None:
    """Given una linea con codigo seguido de un comentario `//`,
    When se procesa,
    Then queda solo el codigo, sin el comentario ni el espacio sobrante.
    """
    # Arrange
    block = '  companies: 5,  // 5 empresas distintas'

    # Act
    result = _strip_ts_line_comments(block)

    # Assert
    assert result == '  companies: 5,'


def test_strip_ts_line_comments_keeps_double_slash_inside_double_quotes() -> (
    None
):
    """Given un `//` dentro de un string con comillas dobles,
    When se procesa,
    Then el `//` se conserva (no es un comentario).
    """
    # Arrange
    block = '  avatarUrl: "https://example.com/a.avif",'

    # Act
    result = _strip_ts_line_comments(block)

    # Assert
    assert result == '  avatarUrl: "https://example.com/a.avif",'


def test_strip_ts_line_comments_keeps_double_slash_inside_single_quotes() -> (
    None
):
    """Given un `//` dentro de un string con comillas simples,
    When se procesa,
    Then el `//` se conserva.
    """
    # Arrange
    block = "  website: 'https://the-full-stack.com',"

    # Act
    result = _strip_ts_line_comments(block)

    # Assert
    assert result == "  website: 'https://the-full-stack.com',"


def test_strip_ts_line_comments_cuts_comment_after_quoted_value() -> None:
    """Given una linea con un valor entre comillas seguido de comentario,
    When se procesa,
    Then conserva el valor entre comillas y corta el comentario.
    """
    # Arrange
    block = "  url: 'https://x.com',  // comentario tras la url"

    # Act
    result = _strip_ts_line_comments(block)

    # Assert
    assert result == "  url: 'https://x.com',"


def test_load_profile_returns_corrected_stats() -> None:
    """Given el profile.ts real,
    When se invoca _load_profile,
    Then stats refleja la data corregida (companies=5, years=12).
    """
    # Act
    profile = _load_profile()

    # Assert
    assert profile['stats'] == {
        'yearsExperience': 12,
        'companies': 5,
        'countries': 4,
        'certifications': 11,
    }


def test_load_profile_returns_all_five_niches() -> None:
    """Given el profile.ts real,
    When se invoca _load_profile,
    Then niches trae los 5 niches del portfolio en orden.
    """
    # Act
    profile = _load_profile()

    # Assert
    assert profile['niches'] == [
        'fintech',
        'architect',
        'leader',
        'vibe',
        'generic',
    ]


def test_load_profile_summary_mentions_twelve_years() -> None:
    """Given el profile.ts real,
    When se invoca _load_profile,
    Then el summary es/en menciona 12 años y no 8.
    """
    # Act
    profile = _load_profile()

    # Assert
    assert '12 años' in profile['summary']['es']
    assert '8 años' not in profile['summary']['es']
    assert '12 years' in profile['summary']['en']
    assert '8 years' not in profile['summary']['en']


def test_load_profile_preserves_urls_with_double_slash() -> None:
    """Given el profile.ts real (avatarUrl y contactos con https://),
    When se invoca _load_profile,
    Then las URLs conservan el `//` (no se truncan como comentario).
    """
    # Act
    profile = _load_profile()

    # Assert
    assert profile['avatarUrl'].startswith('https://')
    assert profile['contacts']['linkedin'].startswith('https://')
    assert profile['contacts']['github'].startswith('https://')
