"""Controller `content.upsert-certificate` — Upsert de un certificado + niches + priorities.

Admin-only (access JWT + whitelist SSM). Valida el payload con
`CertificateIn` (shape YAML del seed), delega en
`content_service.upsert_entity` (UNA transaccion + invalidacion del
cache tag 'cv') y normaliza la salida.
"""

from __future__ import annotations

from models.content_simple import CertificateIn

from .._base import ContentUpsertBase


class UpsertCertificate(ContentUpsertBase):
    """Upsert de certificate (action `upsert-certificate`)."""

    event_model = CertificateIn
    entity = 'certificate'
