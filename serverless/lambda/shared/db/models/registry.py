"""@module shared.db.models.registry — carga TODOS los modelos.

Import con efecto secundario: importar los 5 dominios registra sus clases
en `Base.metadata`. Lo usan los consumidores que necesitan el schema
COMPLETO: el `env.py` de Alembic (autogenerate) y el seed del Lambda `db`.

NO re-exporta simbolos (no es un barrel). Los consumidores de runtime
(repos de un dominio) NO importan de aca: importan su dominio puntual
(`from shared.db.models.auth import AuthUser`) para no registrar las 43
clases cuando solo usan ~12. Ver `.claude/rules/lambda-config.md`.
"""

import shared.db.models.auth
import shared.db.models.cv
import shared.db.models.i18n
import shared.db.models.taxonomy
import shared.db.models.visitor  # noqa: F401
