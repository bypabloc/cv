"""@module shared.db.models.registry — carga TODOS los modelos.

Import con efecto secundario: importa TODOS los modulos concretos de modelo
(uno por uno) registrando sus clases en `Base.metadata`. Lo usan los
consumidores que necesitan el schema COMPLETO: el `env.py` de Alembic
(autogenerate) y el seed del Lambda `db`.

NO re-exporta simbolos (no es un barrel). Los consumidores de runtime NO
importan de aca: importan el MODULO concreto que usan
(`from shared.db.models.auth.user import AuthUser`) para registrar solo su
closure, no las 43 clases. Ver `.claude/rules/lambda-config.md`.
"""

import shared.db.models.auth.admin_action
import shared.db.models.auth.audit_log
import shared.db.models.auth.consent_log
import shared.db.models.auth.credentials
import shared.db.models.auth.email_code
import shared.db.models.auth.magic_link
import shared.db.models.auth.mfa_method
import shared.db.models.auth.recovery_code
import shared.db.models.auth.user
import shared.db.models.auth.user_session
import shared.db.models.auth.webauthn_credential
import shared.db.models.cv.cv_entity
import shared.db.models.cv.education
import shared.db.models.cv.experience
import shared.db.models.cv.profile
import shared.db.models.cv.project
import shared.db.models.cv.skill
import shared.db.models.i18n.translation
import shared.db.models.taxonomy.catalog
import shared.db.models.taxonomy.event_type
import shared.db.models.taxonomy.priority
import shared.db.models.visitor.contact
import shared.db.models.visitor.session
import shared.db.models.visitor.session_visit
import shared.db.models.visitor.tracking  # noqa: F401
