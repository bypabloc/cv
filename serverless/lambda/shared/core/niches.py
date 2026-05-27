"""@module niches — fuente unica de verdad de los niches del portfolio.

El portfolio tiene 6 subdominios:

- `hub` (selector multi-niche, sin CV propio)
- `fintech`, `architect`, `leader`, `vibe`, `generic` (CV filtrado)

`ALL_NICHES` cubre los 6 — se usa para tracking (persistencia en
`session_visits.niche` y `tracking_events.niche`) y para inferir el
niche desde el header HTTP `Origin`. `CV_NICHES` excluye `hub` y se
usa SOLO en el Lambda `cv` para filtrar contenido del CV (que no
existe para `hub`).

El helper `niche_from_origin(origin)` se usa cuando un POST `/contact`
llega sin un `/track` previo (decision 2 del plan sessions-normalize):
infiere el niche del primer label del hostname del Origin.

Reemplaza el `_VALID_NICHES` que vivia en
`services/cv/core/models/cv.py`.
"""

from __future__ import annotations

from urllib.parse import urlparse

ALL_NICHES: frozenset[str] = frozenset(
    {'hub', 'fintech', 'architect', 'leader', 'vibe', 'generic'},
)
"""Los 6 niches/subdominios reales del portfolio. Usar para tracking,
session_visits.niche, y validacion de entrada cuando aplique."""

CV_NICHES: frozenset[str] = ALL_NICHES - {'hub'}
"""Los 5 niches con contenido en el CV. `hub` es solo selector, no
tiene CV propio. Usar SOLO en el Lambda `cv` para filtrado."""


def niche_from_origin(origin: str | None) -> str | None:
    """Infiere el niche del header `Origin` de la request HTTP.

    Parsea el primer label del hostname y matchea contra `ALL_NICHES`.
    Retorna `None` si `origin` es `None`, no es una URL valida, o el
    primer label no esta en `ALL_NICHES`.

    Examples
    --------
    >>> niche_from_origin('https://fintech.portfolio.dev.the-full-stack.com')
    'fintech'
    >>> niche_from_origin('https://hub.portfolio.the-full-stack.com')
    'hub'
    >>> niche_from_origin('https://the-full-stack.com') is None
    True
    >>> niche_from_origin('https://localhost:9970') is None
    True
    >>> niche_from_origin(None) is None
    True
    >>> niche_from_origin('') is None
    True
    """
    if not origin:
        return None
    try:
        hostname = urlparse(origin).hostname
    except ValueError:
        return None
    if not hostname:
        return None
    first_label = hostname.split('.', 1)[0]
    if first_label in ALL_NICHES:
        return first_label
    return None
