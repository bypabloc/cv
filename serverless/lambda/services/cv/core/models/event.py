"""EventModel del Lambda `cv` (operations cv + content + publish).

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

from .content import ExperienceIn, ProfileIn, ProjectIn, SkillCategoryIn
from .content_simple import (
    AwardIn,
    CatalogsIn,
    CertificateIn,
    DeleteIn,
    EducationIn,
    EndorsementIn,
    GetAllIn,
    LanguageIn,
    PublicationIn,
    ReorderIn,
)
from .cv import CvQueryModel
from .publish import PublishDispatchIn, PublishStatusIn

# Eviten F401 (los imports estan para forzar la carga del modulo).
_ = (
    CvQueryModel,
    ProfileIn,
    ExperienceIn,
    ProjectIn,
    SkillCategoryIn,
    EducationIn,
    CertificateIn,
    AwardIn,
    LanguageIn,
    EndorsementIn,
    PublicationIn,
    DeleteIn,
    ReorderIn,
    CatalogsIn,
    GetAllIn,
    PublishDispatchIn,
    PublishStatusIn,
)

EVENT_MODEL = build_event_model(OPERATIONS)
