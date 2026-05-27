"""@module seed_helpers — helpers compartidos para el seeder del CV.

Funciones puras sin dependencias del ORM. Se usan desde
`services/db/core/services/seed_service.py` (Fase 3 del plan
group-tables-by-domain) y los tests del shared kit.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import date


def _parse_ym(raw: str | int | None) -> date | None:
    """Convierte 'YYYY-MM', 'YYYY-MM-DD', 'YYYY' (o int) a `date`.

    Strings no-parseables como 'Actual', 'Present', 'Hoy' retornan None
    (estudios/experiencias en curso del schema viejo).

    >>> _parse_ym('2024-01')
    datetime.date(2024, 1, 1)
    >>> _parse_ym('2024-01-15')
    datetime.date(2024, 1, 15)
    >>> _parse_ym('2024')
    datetime.date(2024, 1, 1)
    >>> _parse_ym(2024)
    datetime.date(2024, 1, 1)
    >>> _parse_ym(None)
    >>> _parse_ym('Actual')
    >>> _parse_ym('Present')
    """
    if raw is None:
        return None
    if isinstance(raw, int):
        return date(raw, 1, 1)
    s = raw.strip()
    if not s:
        return None
    # YYYY-MM-DD
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}', s):
        year, month, day = (int(p) for p in s.split('-'))
        return date(year, month, day)
    # YYYY-MM
    if re.fullmatch(r'\d{4}-\d{2}', s):
        year, month = (int(p) for p in s.split('-'))
        return date(year, month, 1)
    # YYYY
    if re.fullmatch(r'\d{4}', s):
        return date(int(s), 1, 1)
    # No parseable (Actual / Present / Hoy / etc.)
    return None


_SLUG_NON_ALNUM = re.compile(r'[^a-z0-9]+')
_SLUG_EDGES = re.compile(r'(^-+|-+$)')


def _to_slug(name: str) -> str:
    """Convierte un display name a slug ASCII kebab-case.

    Normaliza tildes (NFD + drop combining marks) antes del regex, asi
    'Analisis' -> 'analisis' (no 'an-lisis'). Coincide con el backfill
    SQL de la migracion Alembic (que usa la extension `unaccent`).

    >>> _to_slug('Python')
    'python'
    >>> _to_slug('Node.js')
    'node-js'
    >>> _to_slug('AWS Lambda')
    'aws-lambda'
    >>> _to_slug('Análisis de Productividad')
    'analisis-de-productividad'
    >>> _to_slug('C#')
    'c'
    >>> _to_slug('  espacios  ')
    'espacios'
    """
    # NFD descompone tildes en char + combining mark; encode/decode drop
    # las marks combinadoras (categoria 'Mn'). Equivalente Python al
    # unaccent() de PostgreSQL.
    decomposed = unicodedata.normalize('NFD', name)
    ascii_only = ''.join(
        c for c in decomposed if not unicodedata.combining(c)
    )
    lowered = ascii_only.lower()
    hyphenated = _SLUG_NON_ALNUM.sub('-', lowered)
    return _SLUG_EDGES.sub('', hyphenated)
