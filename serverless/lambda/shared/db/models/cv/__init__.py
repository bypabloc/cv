"""Re-exports planos del dominio CV.

Renames respecto al schema previo:
- `Education` -> `EducationEntry` (tabla `cv_education_entries`)
- `EducationNiche` -> `EducationEntryNiche`
- `Reference` -> `Endorsement` (tabla `cv_endorsements`, `references` es
  palabra reservada SQL)
- `ReferenceNiche` -> `EndorsementNiche`

Vaciado a proposito: sin re-exports (no-barrel). Los consumidores
importan del modulo concreto (`from shared.db.models.<dom>.<mod>
import <Clase>`). Lo enforza el conformance `serverless lint-deps`.
Ver `.claude/rules/lambda-shared-imports.md`.
"""
