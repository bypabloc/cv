"""EventModel del Lambda `auth`.

Construye `EVENT_MODEL` con `build_event_model(OPERATIONS)` del kit
(`shared.lambda_kit`). El handler lo usa para validar la estructura
`{operation, action, data}` del evento sintetico y resolver el
controller correspondiente.

Los modelos Pydantic concretos por action (`LoginStartIn`, ...) se
importan aqui para garantizar que sus modulos se cargan al cold start;
los controllers los reutilizan para validar el payload concreto dentro
de `validate()`.
"""

from __future__ import annotations

from settings.operations import OPERATIONS
from shared.lambda_kit.event_model import build_event_model

# Side-effect: importar los modelos garantiza que se cargan en cold
# start (algunos controllers los importan via `models.<operation>` y
# nos beneficiamos del module caching de Python).
from .login import (
    LoginStartIn,
    LoginVerifyCodeIn,
    LoginVerifyMagicLinkIn,
    LoginVerifyPasswordIn,
    LoginVerifyTotpIn,
)
from .mfa import (
    MfaConfirmTotpIn,
    MfaDisableIn,
    MfaListIn,
    MfaRecoveryCodesConsumeIn,
    MfaRecoveryCodesGenerateIn,
    MfaSetPreferredIn,
    MfaSetupEmailCodeIn,
    MfaSetupTotpIn,
)
from .session import SessionLogoutIn, SessionRefreshIn
from .verify import VerifyResendCodeIn, VerifySetPasswordIn
from .webauthn import (
    WebauthnDeleteCredentialIn,
    WebauthnListCredentialsIn,
    WebauthnLoginOptionsIn,
    WebauthnLoginVerifyIn,
    WebauthnRegisterOptionsIn,
    WebauthnRegisterVerifyIn,
)

# Eviten F401 (los imports estan para forzar la carga del modulo).
_ = (
    LoginStartIn,
    LoginVerifyMagicLinkIn,
    LoginVerifyCodeIn,
    LoginVerifyPasswordIn,
    LoginVerifyTotpIn,
    VerifySetPasswordIn,
    VerifyResendCodeIn,
    SessionRefreshIn,
    SessionLogoutIn,
    MfaSetupTotpIn,
    MfaConfirmTotpIn,
    MfaSetupEmailCodeIn,
    MfaSetPreferredIn,
    MfaDisableIn,
    MfaListIn,
    MfaRecoveryCodesGenerateIn,
    MfaRecoveryCodesConsumeIn,
    WebauthnRegisterOptionsIn,
    WebauthnRegisterVerifyIn,
    WebauthnLoginOptionsIn,
    WebauthnLoginVerifyIn,
    WebauthnListCredentialsIn,
    WebauthnDeleteCredentialIn,
)

EVENT_MODEL = build_event_model(OPERATIONS)
