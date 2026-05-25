# 05 — Fase 1: Modelos SQLAlchemy + reorganizacion

[README](README.md) | [04-archivos](04-archivos-afectados.md) |
**05-fase-modelos** | [06-fase-migracion](06-fase-migracion-alembic.md)

## Objetivo

Reorganizar `serverless/lambda/shared/db/models/` en 4 subcarpetas por
dominio (`cv/`, `visitor/`, `taxonomy/`, `i18n/`), aplicar prefijos al
`__tablename__` de cada clase, normalizar columnas (fechas DATE, slugs,
PK fisica) y preservar la API publica de imports (`from
shared.db.models import Profile` sigue funcionando).

## Pre-requisitos

- Rama `feature/group-tables-by-domain` activa (creada desde `dev`).
- `docs/specs/group-tables-by-domain/` ya commiteado (commit 1).
- Tests escritos primero (TDD) — ver `03-tests-requeridos.md`.

## Pasos

### Paso 1.1 — Crear subcarpetas y mover clases

Estructura objetivo:

```text
serverless/lambda/shared/db/models/
├── __init__.py             # re-exports planos: from .cv import *; etc
├── cv/
│   ├── __init__.py         # re-exports planos
│   ├── profile.py          # Profile, ProfileStats, ProfileNiche
│   ├── experience.py       # Experience, ExperienceBullet, ExperienceNiche, ExperienceSkill
│   ├── education.py        # EducationEntry, EducationEntryNiche
│   ├── project.py          # Project, ProjectCaseStudy, ProjectMetric, ProjectNiche, ProjectTechTag
│   ├── skill.py            # Skill, SkillCategory, SkillCategorySkill, SkillCategoryNiche
│   └── cv_entity.py        # Award, AwardNiche, Certificate, CertificateNiche, Language, LanguageNiche, Publication, PublicationNiche, Endorsement, EndorsementNiche
├── visitor/
│   ├── __init__.py
│   ├── contact.py          # Contact
│   ├── session.py          # Session
│   ├── session_visit.py    # SessionVisit
│   └── tracking.py         # TrackingEvent
├── taxonomy/
│   ├── __init__.py
│   ├── catalog.py          # Niche, TechTag
│   ├── priority.py         # NichePriority
│   └── event_type.py       # EventType
└── i18n/
    ├── __init__.py
    └── translation.py      # Translation
```

Razon de la agrupacion dentro de `cv/`:

- 1 archivo por entidad raiz + sus auxiliares 1:N + sus junctions.
- `cv_entity.py` agrupa las 5 entidades del CV simples (sin auxiliares
  1:N propios): awards, certificates, languages, publications,
  endorsements. Cada una con su junction `*_niches`. Tenerlas juntas
  evita 10 archivos diminutos.

### Paso 1.2 — Aplicar `__tablename__` con prefijo

Por cada clase, cambiar el string literal:

```python
# antes
class Profile(Base):
    __tablename__ = 'profile'
    ...

# despues
class Profile(Base):
    __tablename__ = 'cv_profiles'   # prefijo + plural forzado
    ...
```

Tabla completa de cambios: ver `02-diagrama-er.md`.

### Paso 1.3 — Normalizar columnas

**Experience (cv_experiences)**:

```python
# antes
start_ym: Mapped[str] = mapped_column(String(7), nullable=False)
end_ym:   Mapped[str | None] = mapped_column(String(7), nullable=True)
# CHECK (start_ym ~ '^\d{4}-\d{2}$')

# despues
started_on: Mapped[date] = mapped_column(Date, nullable=False)
ended_on:   Mapped[date | None] = mapped_column(Date, nullable=True)
# sin CHECK (tipo Date ya valida)
```

**Award (cv_awards)**: idem `awarded_ym -> awarded_on Date`.

**EducationEntry (cv_education_entries)**:

```python
# antes
start_year: Mapped[str] = mapped_column(String(16))
end_year:   Mapped[str | None] = mapped_column(String(16), nullable=True)

# despues
started_on: Mapped[date] = mapped_column(Date)
ended_on:   Mapped[date | None] = mapped_column(Date, nullable=True)
```

**Skill (cv_skills)**:

```python
# agregar
slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
# preservar
name: Mapped[str] = mapped_column(String(120))    # display, ya no UK
```

**TechTag (tax_tech_tags)**: idem skill (slug UK + name display).

**Niche (tax_niches)**:

```python
# antes
position: Mapped[int] = mapped_column(Integer, nullable=False)

# despues
display_order: Mapped[int] = mapped_column(Integer, nullable=False)
```

**TrackingEvent (vis_tracking_events)**:

```python
# antes
__table_args__ = (
    # NO PrimaryKeyConstraint (ORM-only PK)
    Index('ix_tracking_events_created_at', 'created_at'),
    {'postgresql_partition_by': 'RANGE (created_at)'},
)

# despues
__table_args__ = (
    PrimaryKeyConstraint('created_at', 'visit_id', 'page_id',
                         name='pk_vis_tracking_events'),
    Index('ix_vis_tracking_events_created_at', 'created_at'),
    {'postgresql_partition_by': 'RANGE (created_at)'},
)
```

**Endorsement (cv_endorsements)** = ex `References`:

```python
# antes (file: cv_entities.py)
class Reference(Base):
    __tablename__ = 'references'
    ...

# despues (file: cv/cv_entity.py)
class Endorsement(Base):
    __tablename__ = 'cv_endorsements'
    ...
```

Y la junction:

```python
class EndorsementNiche(Base):
    __tablename__ = 'cv_endorsement_niches'
    endorsement_id: Mapped[UUID] = mapped_column(
        ForeignKey('cv_endorsements.id', ondelete='CASCADE'),
        primary_key=True,
    )
    niche_id: Mapped[UUID] = mapped_column(
        ForeignKey('tax_niches.id', ondelete='CASCADE'),
        primary_key=True,
    )
```

### Paso 1.4 — `__init__.py` planos

Cada `__init__.py` de subcarpeta hace re-exports planos:

```python
# shared/db/models/cv/__init__.py
from .profile import Profile, ProfileStats, ProfileNiche
from .experience import Experience, ExperienceBullet, ExperienceNiche, ExperienceSkill
from .education import EducationEntry, EducationEntryNiche
from .project import Project, ProjectCaseStudy, ProjectMetric, ProjectNiche, ProjectTechTag
from .skill import Skill, SkillCategory, SkillCategorySkill, SkillCategoryNiche
from .cv_entity import (
    Award, AwardNiche,
    Certificate, CertificateNiche,
    Language, LanguageNiche,
    Publication, PublicationNiche,
    Endorsement, EndorsementNiche,
)

__all__ = [
    'Profile', 'ProfileStats', 'ProfileNiche',
    'Experience', 'ExperienceBullet', 'ExperienceNiche', 'ExperienceSkill',
    'EducationEntry', 'EducationEntryNiche',
    'Project', 'ProjectCaseStudy', 'ProjectMetric', 'ProjectNiche', 'ProjectTechTag',
    'Skill', 'SkillCategory', 'SkillCategorySkill', 'SkillCategoryNiche',
    'Award', 'AwardNiche',
    'Certificate', 'CertificateNiche',
    'Language', 'LanguageNiche',
    'Publication', 'PublicationNiche',
    'Endorsement', 'EndorsementNiche',
]
```

El `__init__.py` raiz preserva la API publica:

```python
# shared/db/models/__init__.py
from .cv import *
from .visitor import *
from .taxonomy import *
from .i18n import *
```

Asi `from shared.db.models import Profile` (legacy) sigue funcionando
sin cambio en call-sites.

### Paso 1.5 — Eliminar archivos viejos

Una vez todas las clases se movieron y `__init__.py` raiz funciona,
borrar los 11 archivos viejos en `shared/db/models/*.py` (raiz). Ver
`04-archivos-afectados.md` -> "Eliminar".

### Paso 1.6 — Verificacion incremental

```bash
# 1. Sintaxis Python
python -m compileall -q serverless/lambda/shared/db/models/

# 2. Imports compatibles
python -c "from shared.db.models import Profile, Contact, Niche, Translation, Endorsement; \
           assert Profile.__tablename__ == 'cv_profiles'; \
           assert Contact.__tablename__ == 'vis_contacts'; \
           assert Niche.__tablename__ == 'tax_niches'; \
           assert Translation.__tablename__ == 'i18n_translations'; \
           assert Endorsement.__tablename__ == 'cv_endorsements'"

# 3. Tests unitarios
serverless tests --type=unit --shared
```

## Definition of done (Fase 1)

- [ ] 18 archivos nuevos en `shared/db/models/{cv,visitor,taxonomy,i18n}/` creados
- [ ] 11 archivos viejos en `shared/db/models/*.py` eliminados
- [ ] `__init__.py` raiz preserva API publica (call-sites sin cambio)
- [ ] Todas las clases tienen el `__tablename__` correcto (verificado por tests)
- [ ] Tests unit del shared kit verdes: `serverless tests --type=unit --shared`
- [ ] `python -m compileall -q serverless/lambda/shared/` sin errores

Esta fase NO requiere todavia ninguna migracion Alembic — los modelos
quedan apuntando a las tablas nuevas, pero la DB sigue con los nombres
viejos. Eso lo corrige la Fase 2.
