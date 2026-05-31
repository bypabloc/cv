"""@module models.event — EventModel del Lambda send_email.

Construye la clase `EventModel` ligada al `OPERATIONS` del Lambda con el
helper del kit. Valida `{operation, action, data}` y resuelve el controller.
"""

from __future__ import annotations

from settings.operations import OPERATIONS
from shared.lambda_kit.event_model import build_event_model

EVENT_MODEL = build_event_model(OPERATIONS)
