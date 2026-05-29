"""Re-exports planos del dominio visitor."""

# Cross-domain FK target: `vis_tracking_events.event_type_id ->
# tax_event_types.id`. La carga per-dominio debe registrar el dominio
# taxonomy o la FK no resuelve en INSERT de `vis_tracking_events`
# (NoReferencedTableError -> el tracking_worker falla y reintenta hasta DLQ).
# Ver `.claude/rules/lambda-config.md`.
import shared.db.models.taxonomy  # noqa: F401

from .contact import Contact
from .session import Session
from .session_visit import SessionVisit
from .tracking import TrackingEvent

__all__ = ['Contact', 'Session', 'SessionVisit', 'TrackingEvent']
