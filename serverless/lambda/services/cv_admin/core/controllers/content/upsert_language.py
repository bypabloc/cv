"""Controller `content.upsert-language` — Upsert de un idioma + i18n (name/level) + niches + priorities.

Admin-only (access JWT + whitelist SSM). Valida el payload con
`LanguageIn` (shape YAML del seed), delega en
`content_service.upsert_entity` (UNA transaccion + invalidacion del
cache tag 'cv') y normaliza la salida.
"""

from __future__ import annotations

from models.content_simple import LanguageIn

from .._base import ContentUpsertBase


class UpsertLanguage(ContentUpsertBase):
    """Upsert de language (action `upsert-language`)."""

    event_model = LanguageIn
    entity = 'language'
