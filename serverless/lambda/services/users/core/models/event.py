"""EventModel del Lambda `users`.

Construye `EVENT_MODEL` con `build_event_model(OPERATIONS)` del kit
(`shared.lambda_kit`). El handler lo usa para validar la estructura
`{operation, action, data}` del evento sintetico y resolver el controller.

Los modelos Pydantic concretos por action se importan aqui para garantizar
que sus modulos se cargan en cold start; cada controller los reutiliza
como `event_model` para validar su payload dentro de `validate()`.
"""

from __future__ import annotations

from settings.operations import OPERATIONS
from shared.lambda_kit.event_model import build_event_model

from .admin import (
    AdminDeleteUserIn,
    AdminDisableUserIn,
    AdminEnableUserIn,
    AdminForceLogoutIn,
    AdminGetUserIn,
    AdminListAdminActionsIn,
    AdminListUsersIn,
)
from .profile import (
    ProfileChangeEmailIn,
    ProfileConfirmEmailChangeIn,
    ProfileDeleteAccountIn,
    ProfileGetIn,
    ProfileUpdateIn,
)
from .status import (
    StatusGetIn,
    StatusListSessionsIn,
    StatusRevokeSessionIn,
)

# Eviten F401 (los imports estan para forzar la carga del modulo).
_ = (
    ProfileGetIn,
    ProfileUpdateIn,
    ProfileChangeEmailIn,
    ProfileConfirmEmailChangeIn,
    ProfileDeleteAccountIn,
    StatusGetIn,
    StatusListSessionsIn,
    StatusRevokeSessionIn,
    AdminListUsersIn,
    AdminGetUserIn,
    AdminDisableUserIn,
    AdminEnableUserIn,
    AdminForceLogoutIn,
    AdminDeleteUserIn,
    AdminListAdminActionsIn,
)

EVENT_MODEL = build_event_model(OPERATIONS)
