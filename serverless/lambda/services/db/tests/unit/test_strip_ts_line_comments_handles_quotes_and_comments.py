"""Helper seed_service._strip_ts_line_comments.

Given lineas TS con comentarios `//` dentro y fuera de strings,
When se procesan con _strip_ts_line_comments,
Then se recortan los comentarios reales y se preservan los `//` que estan
dentro de comillas (parte de una URL, no un comentario).
"""

import pytest

pytestmark = pytest.mark.unit

# (entrada, salida esperada) — un caso por fila.
_CASES = [
    ('  // comentario suelto', ''),
    ('  companies: 5,  // 5 empresas', '  companies: 5,'),
    (
        '  avatarUrl: "https://example.com/a.avif",',
        '  avatarUrl: "https://example.com/a.avif",',
    ),
    (
        "  website: 'https://the-full-stack.com',",
        "  website: 'https://the-full-stack.com',",
    ),
    (
        "  url: 'https://x.com',  // comentario tras la url",
        "  url: 'https://x.com',",
    ),
]


@pytest.mark.parametrize(('raw', 'expected'), _CASES)
def test_strip_ts_line_comments_handles_quotes_and_comments(
    raw: str, expected: str
) -> None:
    from services.seed_service import _strip_ts_line_comments

    # Act
    result = _strip_ts_line_comments(raw)

    # Assert
    assert result == expected
