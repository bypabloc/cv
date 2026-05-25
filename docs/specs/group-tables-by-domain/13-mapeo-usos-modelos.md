# 13 — Mapeo exhaustivo de usos de modelos

[README](README.md) | [12-verificacion](12-verificacion-e2e.md) | **13-mapeo**

> Checklist generada por grep automatico. Cada bloque lista TODOS los lugares donde se referencia un modelo/tabla/columna a renombrar. Verificar todos los items al implementar la fase correspondiente.

## Convenciones

- Path relativo desde la raiz del repo
- Linea:Snippet (max 95 chars)
- [F1]/[F2]/[F3]/[F4] marca a que fase del plan pertenece el cambio:
  - F1 = modelos Python (Fase 1)
  - F2 = migracion Alembic (Fase 2)
  - F3 = seeds + seed_service (Fase 3)
  - F4 = lambdas downstream (Fase 4)

---

## profile / Profile

### Como string literal 'profile'

- [F1] services/cv/core/controllers/cv/_base.py:29:     opcionalmente `requires_niche` (default True; profile usa False).
- [F1] services/cv/core/controllers/cv/profile.py:1: """Controller cv/profile — profile + stats + textos bilingues."""
- [F1] services/cv/core/controllers/cv/profile.py:7:     """Devuelve el profile. No filtra por niche (singleton)."""
- [F1] services/cv/core/handler.py:9:     GET /cv?operation=cv&action=profile&locale=es
- [F1] services/cv/core/services/cv_service.py:83:     """Devuelve el profile + stats + textos bilingues."""
- [F1] services/cv/core/settings/operations.py:4: `get`, `profile`, `experiences`, `projects`, `certificates`, `awards`,
- [F1] services/cv/tests/unit/test_controllers_invoke_service_and_normalize.py:17:     ('controllers.cv.profile', 'Profile', 'get_profile', False),
- [F1] services/cv/tests/unit/test_cv_service_delegates_to_repository.py:34:     expected = {'profile': {}, 'experiences': []}
- [F1] services/cv/tests/unit/test_handler_routes_get_action.py:33:         'profile': {'name': 'Pablo', 'handle': 'bypabloc'},
- [F1] services/cv/tests/unit/test_handler_routes_get_action.py:67:     assert body['profile']['name'] == 'Pablo'
- [F3] services/db/core/services/seed_service.py:20: 2. Entidades (profile, experiences, projects, ...) — UUID resuelto por slug.
- [F3] services/db/core/services/seed_service.py:106:     """Extrae el dict del profile del archivo TS `seeds/data/profile.ts`.
- [F3] services/db/core/services/seed_service.py:108:     `profile.ts` no es YAML; el objeto vive dentro de `ProfileSchema.parse(
- [F3] services/db/core/services/seed_service.py:112:     raw = (_DATA_DIR / 'profile.ts').read_text(encoding='utf-8')
- [F3] services/db/core/services/seed_service.py:342:     _set_translation(session, 'profile', profile_id, 'headline', p['headline'])
- [F3] services/db/core/services/seed_service.py:343:     _set_translation(session, 'profile', profile_id, 'summary', p['summary'])
- [F3] services/db/core/services/seed_service.py:345:         session, 'profile', profile_id, 'availability', p.get('availability')
- [F3] services/db/core/services/seed_service.py:841:     ('profile', Profile),
- [F3] services/db/tests/integration/test_seed_command_e2e.py:32:     assert counts['profile'] == 1
- [F3] services/db/tests/unit/test_handler_routes_seed_command.py:26:             return_value={'seeded': True, 'counts': {'profile': 1}},
- [F3] services/db/tests/unit/test_handler_routes_seed_command.py:38:         'counts': {'profile': 1},
- [F1] services/db/tests/unit/test_load_profile_parses_stats_and_niches.py:3: Given el archivo real seeds/data/profile.ts,
- [F1] services/db/tests/unit/test_load_profile_parses_stats_and_niches.py:5: Then devuelve el dict del profile con stats, niches y URLs intactas
- [F1] services/db/tests/unit/test_load_profile_parses_stats_and_niches.py:18:     profile = _load_profile()
- [F1] services/db/tests/unit/test_load_profile_parses_stats_and_niches.py:21:     assert profile['stats'] == {
- ... (+46 ocurrencias más)

### Como clase Profile

- [F1] services/cv/core/controllers/cv/profile.py:6: class Profile(CvControllerBase):
- [F1] shared/db/models/__init__.py:39: from .profile import Profile, ProfileNiche, ProfileStats
- [F1] shared/db/models/profile.py:15: class Profile(UUIDPKMixin, TimestampMixin, Base):

---

## profile_stats / ProfileStats

### Como string literal 'profile_stats'

- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:303:     op.create_table('profile_stats',
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:478:     op.drop_table('profile_stats')
- [F1] shared/db/models/profile.py:42:     __tablename__ = 'profile_stats'

### Como clase ProfileStats

- [F1] shared/db/models/__init__.py:39: from .profile import Profile, ProfileNiche, ProfileStats
- [F1] shared/db/models/profile.py:37: class ProfileStats(UUIDPKMixin, TimestampMixin, Base):

---

## profile_niches / ProfileNiche

### Como string literal 'profile_niches'

- [F3] services/db/core/services/seed_service.py:842:     ('profile_niches', ProfileNiche),
- [F2] shared/db/alembic/versions/79bacfd3c091_add_profile_niches.py:1: """add profile_niches
- [F2] shared/db/alembic/versions/79bacfd3c091_add_profile_niches.py:26:         'profile_niches',
- [F2] shared/db/alembic/versions/79bacfd3c091_add_profile_niches.py:48:     op.drop_table('profile_niches')
- [F1] shared/db/models/profile.py:6: del profile se persisten en la union `profile_niches`.
- [F1] shared/db/models/profile.py:63:     __tablename__ = 'profile_niches'

### Como clase ProfileNiche

- [F1] shared/db/models/__init__.py:39: from .profile import Profile, ProfileNiche, ProfileStats
- [F1] shared/db/models/profile.py:55: class ProfileNiche(Base):

---

## experiences / Experience

### Como string literal 'experiences'

- [F1] services/cv/core/controllers/cv/experiences.py:1: """Controller cv/experiences — experiencias filtradas por niche."""
- [F1] services/cv/core/handler.py:8:     GET /cv?operation=cv&action=experiences&niche=fintech
- [F1] services/cv/core/settings/operations.py:4: `get`, `profile`, `experiences`, `projects`, `certificates`, `awards`,
- [F1] services/cv/tests/unit/test_controller_maps_service_error.py:16:     from controllers.cv.experiences import Experiences
- [F1] services/cv/tests/unit/test_controllers_invoke_service_and_normalize.py:18:     ('controllers.cv.experiences', 'Experiences', 'list_experiences', True),
- [F1] services/cv/tests/unit/test_cv_service_delegates_to_repository.py:34:     expected = {'profile': {}, 'experiences': []}
- [F1] services/cv/tests/unit/test_handler_routes_get_action.py:34:         'experiences': [],
- [F3] services/db/core/services/seed_service.py:20: 2. Entidades (profile, experiences, projects, ...) — UUID resuelto por slug.
- [F3] services/db/core/services/seed_service.py:440:     for slug, data in _load_dir('experiences'):
- [F3] services/db/core/services/seed_service.py:821:     for _slug, data in _load_dir('experiences'):
- [F3] services/db/core/services/seed_service.py:843:     ('experiences', Experience),
- [F3] services/db/core/services/seed_service.py:876:     # 3. experience_skills (depende de experiences + skills ya cargados).
- [F3] services/db/core/services/seed_service.py:877:     for slug, data in _load_dir('experiences'):
- [F3] services/db/tests/integration/test_seed_command_e2e.py:34:     assert counts['experiences'] == 9
- [F3] services/db/tests/unit/test_load_dir_reads_seed_yaml_files.py:3: Given el directorio real seeds/data/experiences/,
- [F3] services/db/tests/unit/test_load_dir_reads_seed_yaml_files.py:4: When se invoca _load_dir('experiences'),
- [F3] services/db/tests/unit/test_load_dir_reads_seed_yaml_files.py:18:     entries = _load_dir('experiences')
- [F3] services/db/tests/unit/test_seed_controller_returns_ok_result.py:23:             'counts': {'profile': 1, 'experiences': 9},
- [F3] services/db/tests/unit/test_seed_controller_returns_ok_result.py:39:             'counts': {'profile': 1, 'experiences': 9},
- [F3] services/db/tests/unit/test_seed_service_delegates_to_seed_service.py:19:     expected = {'seeded': True, 'counts': {'profile': 1, 'experiences': 9}}
- [F1] shared/db/__init__.py:5: + contenido del CV (experiences, projects, translations, ...).
- [F2] shared/db/alembic/_init_schema_extras.py:46:         WHEN 'experience'         THEN 'experiences'
- [F2] shared/db/alembic/versions/649aa862c0fa_add_cv_country_metrics.py:22:     # experiences.country: NOT NULL. server_default='' temporal para que el
- [F2] shared/db/alembic/versions/649aa862c0fa_add_cv_country_metrics.py:25:         'experiences',
- [F2] shared/db/alembic/versions/649aa862c0fa_add_cv_country_metrics.py:33:     op.alter_column('experiences', 'country', server_default=None)
- ... (+22 ocurrencias más)

### Como clase Experience

- [F1] services/cv/tests/unit/test_controller_maps_service_error.py:16:     from controllers.cv.experiences import Experiences
- [F1] shared/db/__init__.py:12:     from shared.db.models import Contact, Experience
- [F1] shared/db/models/__init__.py:8:     from shared.db.models import Contact, Experience, TrackingEvent
- [F1] shared/db/models/__init__.py:24: from .experience import Experience, ExperienceBullet
- [F1] shared/db/models/experience.py:30: class Experience(UUIDPKMixin, TimestampMixin, Base):

---

## experience_bullets / ExperienceBullet

### Como string literal 'experience_bullets'

- [F2] shared/db/alembic/_init_schema_extras.py:47:         WHEN 'experience_bullet'  THEN 'experience_bullets'
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:259:     op.create_table('experience_bullets',
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:483:     op.drop_table('experience_bullets')
- [F1] shared/db/models/experience.py:5: modelan como `experience_bullets` (1 fila por bullet) + sus textos en
- [F1] shared/db/models/experience.py:73:     __tablename__ = 'experience_bullets'

### Como clase ExperienceBullet

- [F1] shared/db/models/__init__.py:24: from .experience import Experience, ExperienceBullet
- [F1] shared/db/models/experience.py:65: class ExperienceBullet(UUIDPKMixin, TimestampMixin, Base):

---

## experience_niches / ExperienceNiche

### Como string literal 'experience_niches'

- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:270:     op.create_table('experience_niches',
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:482:     op.drop_table('experience_niches')
- [F1] shared/db/models/experience.py:34:     Niches via `experience_niches`; priority via `niche_priorities`.
- [F1] shared/db/models/junctions.py:37:     __tablename__ = 'experience_niches'

### Como clase ExperienceNiche

- [F1] shared/db/models/junctions.py:36: class ExperienceNiche(Base):

---

## experience_skills / ExperienceSkill

### Como string literal 'experience_skills'

- [F3] services/db/core/services/seed_service.py:876:     # 3. experience_skills (depende de experiences + skills ya cargados).
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:277:     op.create_table('experience_skills',
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:481:     op.drop_table('experience_skills')
- [F1] shared/db/models/experience.py:9: `experience_skills` al catalogo `skills`; el flag tecnica/blanda vive en la
- [F1] shared/db/models/junctions.py:10:    - `experience_skills` — experiencia <-> skill, con `kind` (technical/soft)
- [F1] shared/db/models/junctions.py:146:     __tablename__ = 'experience_skills'

### Como clase ExperienceSkill

- [F1] shared/db/models/junctions.py:141: class ExperienceSkill(Base):

---

## education / Education

### Como string literal 'education'

- [F1] services/cv/core/controllers/cv/education.py:1: """Controller cv/education — educacion filtrada por niche."""
- [F1] services/cv/core/settings/operations.py:5: `education`, `languages`, `references`, `skills`.
- [F1] services/cv/tests/unit/test_controllers_invoke_service_and_normalize.py:22:     ('controllers.cv.education', 'Education', 'list_education', True),
- [F1] services/cv/tests/unit/test_handler_routes_get_action.py:38:         'education': [],
- [F3] services/db/core/services/seed_service.py:694:     for slug, data in _load_dir('education'):
- [F3] services/db/core/services/seed_service.py:708:             session, 'education', edu_id, 'degree', data.get('degree')
- [F3] services/db/core/services/seed_service.py:711:             session, 'education', edu_id, 'description', data['description']
- [F3] services/db/core/services/seed_service.py:798:     """Inserta certificates, awards, education, references, languages,
- [F3] services/db/core/services/seed_service.py:848:     ('education', Education),
- [F2] shared/db/alembic/_init_schema_extras.py:54:         WHEN 'education'          THEN 'education'
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:87:     op.create_table('education',
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:228:     sa.Column('entity_type', sa.Enum('profile', 'experience', 'experience_bullet', 'project',
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:255:     sa.ForeignKeyConstraint(['education_id'], ['education.id'], name=op.f('fk_education_niches_
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:293:     sa.Column('entity_type', sa.Enum('profile', 'experience', 'experience_bullet', 'project',
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:500:     op.drop_table('education')
- [F1] shared/db/cv_repository.py:87:     Para entidades con niches OPCIONAL en Zod (education, languages,
- [F1] shared/db/cv_repository.py:658:             translations = _translations_map(session, 'education', ids)
- [F1] shared/db/cv_repository.py:683:         raise RepositoryError(f'education query failed: {exc}') from exc
- [F1] shared/db/cv_repository.py:842:         'education': list_education(niche=niche, locale=locale),
- [F1] shared/db/enums.py:78:     EDUCATION = 'education'
- [F1] shared/db/models/cv_entities.py:4: education, references, languages, skill_categories, publications.
- [F1] shared/db/models/cv_entities.py:58:     Textos bilingues en `translations` (entity_type='education'): `degree`
- [F1] shared/db/models/cv_entities.py:63:     __tablename__ = 'education'
- [F1] shared/db/models/junctions.py:84:         ForeignKey('education.id', ondelete='CASCADE'), nullable=False

### Como clase Education

- [F1] services/cv/core/controllers/cv/education.py:6: class Education(CvControllerBase):
- [F1] shared/db/models/cv_entities.py:55: class Education(UUIDPKMixin, TimestampMixin, Base):

---

## education_niches / EducationNiche

### Como string literal 'education_niches'

- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:252:     op.create_table('education_niches',
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:484:     op.drop_table('education_niches')
- [F1] shared/db/models/junctions.py:81:     __tablename__ = 'education_niches'

### Como clase EducationNiche

- [F1] shared/db/models/junctions.py:80: class EducationNiche(Base):

---

## projects / Project

### Como string literal 'projects'

- [F1] services/cv/core/controllers/cv/projects.py:1: """Controller cv/projects — proyectos filtrados por niche."""
- [F1] services/cv/core/settings/operations.py:4: `get`, `profile`, `experiences`, `projects`, `certificates`, `awards`,
- [F1] services/cv/tests/unit/test_controllers_invoke_service_and_normalize.py:19:     ('controllers.cv.projects', 'Projects', 'list_projects', True),
- [F1] services/cv/tests/unit/test_handler_routes_get_action.py:35:         'projects': [],
- [F3] services/db/core/services/seed_service.py:20: 2. Entidades (profile, experiences, projects, ...) — UUID resuelto por slug.
- [F3] services/db/core/services/seed_service.py:553:     for slug, data in _load_dir('projects'):
- [F3] services/db/core/services/seed_service.py:830:     for _slug, data in _load_dir('projects'):
- [F3] services/db/core/services/seed_service.py:844:     ('projects', Project),
- [F3] services/db/tests/integration/test_seed_command_e2e.py:35:     assert counts['projects'] == 6
- [F1] services/tracking_pixel/tests/integration/_fixtures/_builders.py:73:         'page_url': 'https://the-full-stack.com/projects',
- [F1] services/tracking_pixel/tests/unit/_helpers.py:53:         'page_url': 'https://the-full-stack.com/projects',
- [F1] services/tracking_pixel/tests/unit/_helpers.py:54:         'page_path': '/projects',
- [F1] shared/db/__init__.py:5: + contenido del CV (experiences, projects, translations, ...).
- [F2] shared/db/alembic/_init_schema_extras.py:48:         WHEN 'project'            THEN 'projects'
- [F2] shared/db/alembic/versions/649aa862c0fa_add_cv_country_metrics.py:34:     # metrics_estimated en experiences y projects. server_default=false es un
- [F2] shared/db/alembic/versions/649aa862c0fa_add_cv_country_metrics.py:46:         'projects',
- [F2] shared/db/alembic/versions/649aa862c0fa_add_cv_country_metrics.py:57:     op.drop_column('projects', 'metrics_estimated')
- [F2] shared/db/alembic/versions/7c4d9e1b2a3f_add_project_links.py:23:     """Agrega columna `links` JSONB nullable a projects.
- [F2] shared/db/alembic/versions/7c4d9e1b2a3f_add_project_links.py:31:         'projects',
- [F2] shared/db/alembic/versions/7c4d9e1b2a3f_add_project_links.py:37:     op.drop_column('projects', 'links')
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:163:     op.create_table('projects',
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:321:     sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name=op.f('fk_project_case_studies
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:333:     sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name=op.f('fk_project_metrics_proj
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:341:     sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name=op.f('fk_project_niches_proje
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:348:     sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name=op.f('fk_project_tech_tags_pr
- ... (+16 ocurrencias más)

### Como clase Project

- [F1] shared/db/models/__init__.py:40: from .project import Project, ProjectCaseStudy, ProjectMetric
- [F1] shared/db/models/project.py:24: class Project(UUIDPKMixin, TimestampMixin, Base):

---

## project_case_studies / ProjectCaseStudy

### Como string literal 'project_case_studies'

- [F2] shared/db/alembic/_init_schema_extras.py:49:         WHEN 'project_case_study' THEN 'project_case_studies'
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:316:     op.create_table('project_case_studies',
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:477:     op.drop_table('project_case_studies')
- [F1] shared/db/models/project.py:9:   `project_case_studies` + textos en `translations`.
- [F1] shared/db/models/project.py:65:     __tablename__ = 'project_case_studies'

### Como clase ProjectCaseStudy

- [F1] shared/db/models/__init__.py:40: from .project import Project, ProjectCaseStudy, ProjectMetric
- [F1] shared/db/models/project.py:57: class ProjectCaseStudy(UUIDPKMixin, TimestampMixin, Base):

---

## project_metrics / ProjectMetric

### Como string literal 'project_metrics'

- [F2] shared/db/alembic/_init_schema_extras.py:50:         WHEN 'project_metric'     THEN 'project_metrics'
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:325:     op.create_table('project_metrics',
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:476:     op.drop_table('project_metrics')
- [F1] shared/db/models/project.py:11:   `project_metrics` (par clave/valor ordenado).
- [F1] shared/db/models/project.py:82:     __tablename__ = 'project_metrics'

### Como clase ProjectMetric

- [F1] shared/db/models/__init__.py:40: from .project import Project, ProjectCaseStudy, ProjectMetric
- [F1] shared/db/models/project.py:74: class ProjectMetric(UUIDPKMixin, TimestampMixin, Base):

---

## project_niches / ProjectNiche

### Como string literal 'project_niches'

- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:337:     op.create_table('project_niches',
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:475:     op.drop_table('project_niches')
- [F1] shared/db/models/junctions.py:48:     __tablename__ = 'project_niches'
- [F1] shared/db/models/project.py:30:     Niches via `project_niches`; priority via `niche_priorities`.

### Como clase ProjectNiche

- [F1] shared/db/models/junctions.py:47: class ProjectNiche(Base):

---

## project_tech_tags / ProjectTechTag

### Como string literal 'project_tech_tags'

- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:344:     op.create_table('project_tech_tags',
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:474:     op.drop_table('project_tech_tags')
- [F1] shared/db/models/junctions.py:13:    - `project_tech_tags` — proyecto <-> tech tag (union pura).
- [F1] shared/db/models/junctions.py:185:     __tablename__ = 'project_tech_tags'
- [F1] shared/db/models/project.py:5: `project_tech_tags` al catalogo `tech_tags`.

### Como clase ProjectTechTag

- [F1] shared/db/models/junctions.py:180: class ProjectTechTag(Base):

---

## skills / Skill

### Como string literal 'skills'

- [F1] services/cv/core/controllers/cv/skills.py:1: """Controller cv/skills — categorias de skills filtradas por niche."""
- [F1] services/cv/core/controllers/cv/skills.py:7:     """Devuelve la lista de categorias de skills."""
- [F1] services/cv/core/services/cv_service.py:125:     """Devuelve las categorias de skills filtradas por niche."""
- [F1] services/cv/core/settings/operations.py:5: `education`, `languages`, `references`, `skills`.
- [F1] services/cv/tests/unit/test_controllers_invoke_service_and_normalize.py:25:     ('controllers.cv.skills', 'Skills', 'list_skill_categories', True),
- [F3] services/db/core/services/seed_service.py:19: 1. Vocabularios deduplicados (`niches`, `skills`, `tech_tags`) primero.
- [F3] services/db/core/services/seed_service.py:310:     """Upsert de un vocabulario con clave natural `name` (skills/tech_tags)."""
- [F3] services/db/core/services/seed_service.py:416:     """Enlaza una experiencia con sus skills (technical + soft)."""
- [F3] services/db/core/services/seed_service.py:602:     """Inserta categorias de skills + sus uniones a skills y niches."""
- [F3] services/db/core/services/seed_service.py:603:     for slug, data in _load_dir('skills'):
- [F3] services/db/core/services/seed_service.py:621:         for position, name in enumerate(data.get('skills') or []):
- [F3] services/db/core/services/seed_service.py:815:     """Reune todos los nombres de skill: de `skill_categories.skills[]` y de
- [F3] services/db/core/services/seed_service.py:819:     for _slug, data in _load_dir('skills'):
- [F3] services/db/core/services/seed_service.py:820:         names.update(data.get('skills') or [])
- [F3] services/db/core/services/seed_service.py:853:     ('skills', Skill),
- [F3] services/db/core/services/seed_service.py:876:     # 3. experience_skills (depende de experiences + skills ya cargados).
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:211:     op.create_table('skills',
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:282:     sa.ForeignKeyConstraint(['skill_id'], ['skills.id'], name=op.f('fk_experience_skills_skill_
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:378:     sa.ForeignKeyConstraint(['skill_id'], ['skills.id'], name=op.f('fk_skill_category_skills_sk
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:489:     op.drop_table('skills')
- [F1] shared/db/cv_repository.py:776:     """Devuelve las categorias de skills filtradas por niche, con sus skills."""
- [F1] shared/db/cv_repository.py:816:                     'skills': skills_by_cat.get(c.id, []),
- [F1] shared/db/enums.py:50:     """Tipo de categoria de skills."""
- [F1] shared/db/models/catalog.py:6: - `skills`            — competencias deduplicadas. Unifica los strings de
- [F1] shared/db/models/catalog.py:7:                         `skill_categories.skills[]` y de
- ... (+12 ocurrencias más)

### Como clase Skill

- [F1] shared/db/models/__init__.py:13: from .catalog import Niche, Skill, TechTag
- [F1] shared/db/models/catalog.py:31: class Skill(UUIDPKMixin, TimestampMixin, Base):

---

## skill_categories / SkillCategory

### Como string literal 'skill_categories'

- [F3] services/db/core/services/seed_service.py:815:     """Reune todos los nombres de skill: de `skill_categories.skills[]` y de
- [F3] services/db/core/services/seed_service.py:845:     ('skill_categories', SkillCategory),
- [F3] services/db/tests/integration/test_seed_command_e2e.py:36:     assert counts['skill_categories'] == 10
- [F2] shared/db/alembic/_init_schema_extras.py:51:         WHEN 'skill_category'     THEN 'skill_categories'
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:202:     op.create_table('skill_categories',
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:370:     sa.ForeignKeyConstraint(['skill_category_id'], ['skill_categories.id'], name=op.f('fk_skill
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:377:     sa.ForeignKeyConstraint(['skill_category_id'], ['skill_categories.id'], name=op.f('fk_skill
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:490:     op.drop_table('skill_categories')
- [F1] shared/db/cv_repository.py:823:             f'skill_categories query failed: {exc}'
- [F1] shared/db/models/catalog.py:7:                         `skill_categories.skills[]` y de
- [F1] shared/db/models/cv_entities.py:4: education, references, languages, skill_categories, publications.
- [F1] shared/db/models/cv_entities.py:107:     __tablename__ = 'skill_categories'
- [F1] shared/db/models/junctions.py:128:         ForeignKey('skill_categories.id', ondelete='CASCADE'),
- [F1] shared/db/models/junctions.py:169:         ForeignKey('skill_categories.id', ondelete='CASCADE'),

### Como clase SkillCategory

- [F1] shared/db/models/cv_entities.py:100: class SkillCategory(UUIDPKMixin, TimestampMixin, Base):

---

## skill_category_skills / SkillCategorySkill

### Como string literal 'skill_category_skills'

- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:373:     op.create_table('skill_category_skills',
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:470:     op.drop_table('skill_category_skills')
- [F1] shared/db/models/cv_entities.py:104:     Las skills se enlazan via `skill_category_skills` al catalogo `skills`.
- [F1] shared/db/models/junctions.py:12:    - `skill_category_skills` — categoria de skills <-> skill (union pura).
- [F1] shared/db/models/junctions.py:166:     __tablename__ = 'skill_category_skills'

### Como clase SkillCategorySkill

- [F1] shared/db/models/junctions.py:161: class SkillCategorySkill(Base):

---

## skill_category_niches / SkillCategoryNiche

### Como string literal 'skill_category_niches'

- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:366:     op.create_table('skill_category_niches',
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:471:     op.drop_table('skill_category_niches')
- [F1] shared/db/models/junctions.py:125:     __tablename__ = 'skill_category_niches'

### Como clase SkillCategoryNiche

- [F1] shared/db/models/junctions.py:124: class SkillCategoryNiche(Base):

---

## awards / Award

### Como string literal 'awards'

- [F1] services/cv/core/controllers/cv/awards.py:1: """Controller cv/awards — premios filtrados por niche."""
- [F1] services/cv/core/settings/operations.py:4: `get`, `profile`, `experiences`, `projects`, `certificates`, `awards`,
- [F1] services/cv/tests/unit/test_controllers_invoke_service_and_normalize.py:21:     ('controllers.cv.awards', 'Awards', 'list_awards', True),
- [F1] services/cv/tests/unit/test_handler_routes_get_action.py:37:         'awards': [],
- [F3] services/db/core/services/seed_service.py:667:     for slug, data in _load_dir('awards'):
- [F3] services/db/core/services/seed_service.py:798:     """Inserta certificates, awards, education, references, languages,
- [F3] services/db/core/services/seed_service.py:847:     ('awards', Award),
- [F2] shared/db/alembic/_init_schema_extras.py:53:         WHEN 'award'              THEN 'awards'
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:32:     op.create_table('awards',
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:241:     sa.ForeignKeyConstraint(['award_id'], ['awards.id'], name=op.f('fk_award_niches_award_id_aw
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:509:     op.drop_table('awards')
- [F1] shared/db/cv_repository.py:614:             awards = list(session.execute(stmt).scalars())
- [F1] shared/db/cv_repository.py:615:             ids = [a.id for a in awards]
- [F1] shared/db/cv_repository.py:634:                 for a in awards
- [F1] shared/db/cv_repository.py:637:         raise RepositoryError(f'awards query failed: {exc}') from exc
- [F1] shared/db/cv_repository.py:841:         'awards': list_awards(niche=niche, locale=locale),
- [F1] shared/db/models/cv_entities.py:3: Agrupa las 7 entidades sin sub-tablas propias: certificates, awards,
- [F1] shared/db/models/cv_entities.py:43:     __tablename__ = 'awards'
- [F1] shared/db/models/junctions.py:73:         ForeignKey('awards.id', ondelete='CASCADE'), nullable=False

### Como clase Award

- [F1] shared/db/models/cv_entities.py:36: class Award(UUIDPKMixin, TimestampMixin, Base):

---

## award_niches / AwardNiche

### Como string literal 'award_niches'

- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:238:     op.create_table('award_niches',
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:486:     op.drop_table('award_niches')
- [F1] shared/db/models/junctions.py:70:     __tablename__ = 'award_niches'

### Como clase AwardNiche

- [F1] shared/db/models/junctions.py:69: class AwardNiche(Base):

---

## certificates / Certificate

### Como string literal 'certificates'

- [F1] services/cv/core/controllers/cv/certificates.py:1: """Controller cv/certificates — certificados filtrados por niche.
- [F1] services/cv/core/settings/operations.py:4: `get`, `profile`, `experiences`, `projects`, `certificates`, `awards`,
- [F1] services/cv/tests/unit/test_controllers_invoke_service_and_normalize.py:20:     ('controllers.cv.certificates', 'Certificates', 'list_certificates', True),
- [F1] services/cv/tests/unit/test_handler_routes_get_action.py:36:         'certificates': [],
- [F3] services/db/core/services/seed_service.py:643:     for slug, data in _load_dir('certificates'):
- [F3] services/db/core/services/seed_service.py:798:     """Inserta certificates, awards, education, references, languages,
- [F3] services/db/core/services/seed_service.py:846:     ('certificates', Certificate),
- [F3] services/db/tests/integration/test_seed_command_e2e.py:37:     assert counts['certificates'] == 11
- [F2] shared/db/alembic/_init_schema_extras.py:52:         WHEN 'certificate'        THEN 'certificates'
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:44:     op.create_table('certificates',
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:248:     sa.ForeignKeyConstraint(['certificate_id'], ['certificates.id'], name=op.f('fk_certificate_
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:508:     op.drop_table('certificates')
- [F1] shared/db/cv_repository.py:574:             certificates = list(session.execute(stmt).scalars())
- [F1] shared/db/cv_repository.py:575:             ids = [c.id for c in certificates]
- [F1] shared/db/cv_repository.py:592:                 for c in certificates
- [F1] shared/db/cv_repository.py:595:         raise RepositoryError(f'certificates query failed: {exc}') from exc
- [F1] shared/db/cv_repository.py:840:         'certificates': list_certificates(niche=niche),
- [F1] shared/db/models/cv_entities.py:3: Agrupa las 7 entidades sin sub-tablas propias: certificates, awards,
- [F1] shared/db/models/cv_entities.py:27:     __tablename__ = 'certificates'
- [F1] shared/db/models/junctions.py:62:         ForeignKey('certificates.id', ondelete='CASCADE'), nullable=False

### Como clase Certificate

- [F1] shared/db/models/cv_entities.py:20: class Certificate(UUIDPKMixin, TimestampMixin, Base):

---

## certificate_niches / CertificateNiche

### Como string literal 'certificate_niches'

- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:245:     op.create_table('certificate_niches',
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:485:     op.drop_table('certificate_niches')
- [F1] shared/db/models/junctions.py:59:     __tablename__ = 'certificate_niches'

### Como clase CertificateNiche

- [F1] shared/db/models/junctions.py:58: class CertificateNiche(Base):

---

## languages / Language

### Como string literal 'languages'

- [F1] services/cv/core/controllers/cv/languages.py:1: """Controller cv/languages — idiomas filtrados por niche."""
- [F1] services/cv/core/settings/operations.py:5: `education`, `languages`, `references`, `skills`.
- [F1] services/cv/tests/unit/test_controllers_invoke_service_and_normalize.py:23:     ('controllers.cv.languages', 'Languages', 'list_languages', True),
- [F1] services/cv/tests/unit/test_handler_routes_get_action.py:39:         'languages': [],
- [F3] services/db/core/services/seed_service.py:751:     for slug, data in _load_dir('languages'):
- [F3] services/db/core/services/seed_service.py:798:     """Inserta certificates, awards, education, references, languages,
- [F3] services/db/core/services/seed_service.py:850:     ('languages', Language),
- [F2] shared/db/alembic/_init_schema_extras.py:56:         WHEN 'language'           THEN 'languages'
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:123:     op.create_table('languages',
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:288:     sa.ForeignKeyConstraint(['language_id'], ['languages.id'], name=op.f('fk_language_niches_la
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:497:     op.drop_table('languages')
- [F1] shared/db/cv_repository.py:87:     Para entidades con niches OPCIONAL en Zod (education, languages,
- [F1] shared/db/cv_repository.py:702:             languages = list(session.execute(stmt).scalars())
- [F1] shared/db/cv_repository.py:703:             ids = [language.id for language in languages]
- [F1] shared/db/cv_repository.py:723:                 for language in languages
- [F1] shared/db/cv_repository.py:726:         raise RepositoryError(f'languages query failed: {exc}') from exc
- [F1] shared/db/cv_repository.py:843:         'languages': list_languages(niche=niche, locale=locale),
- [F1] shared/db/models/cv_entities.py:4: education, references, languages, skill_categories, publications.
- [F1] shared/db/models/cv_entities.py:95:     __tablename__ = 'languages'
- [F1] shared/db/models/junctions.py:106:         ForeignKey('languages.id', ondelete='CASCADE'), nullable=False

### Como clase Language

- [F1] shared/db/models/cv_entities.py:88: class Language(UUIDPKMixin, TimestampMixin, Base):

---

## language_niches / LanguageNiche

### Como string literal 'language_niches'

- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:285:     op.create_table('language_niches',
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:480:     op.drop_table('language_niches')
- [F1] shared/db/models/junctions.py:103:     __tablename__ = 'language_niches'

### Como clase LanguageNiche

- [F1] shared/db/models/junctions.py:102: class LanguageNiche(Base):

---

## publications / Publication

### Como string literal 'publications'

- [F3] services/db/core/services/seed_service.py:768:     for slug, data in _load_dir('publications'):
- [F3] services/db/core/services/seed_service.py:799:     publications — entidades sin sub-tablas propias.
- [F3] services/db/core/services/seed_service.py:851:     ('publications', Publication),
- [F2] shared/db/alembic/_init_schema_extras.py:57:         WHEN 'publication'        THEN 'publications'
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:177:     op.create_table('publications',
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:356:     sa.ForeignKeyConstraint(['publication_id'], ['publications.id'], name=op.f('fk_publication_
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:492:     op.drop_table('publications')
- [F1] shared/db/models/cv_entities.py:4: education, references, languages, skill_categories, publications.
- [F1] shared/db/models/cv_entities.py:121:     __tablename__ = 'publications'
- [F1] shared/db/models/junctions.py:117:         ForeignKey('publications.id', ondelete='CASCADE'), nullable=False

### Como clase Publication

- [F1] shared/db/models/cv_entities.py:113: class Publication(UUIDPKMixin, TimestampMixin, Base):

---

## publication_niches / PublicationNiche

### Como string literal 'publication_niches'

- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:352:     op.create_table('publication_niches',
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:473:     op.drop_table('publication_niches')
- [F1] shared/db/models/junctions.py:114:     __tablename__ = 'publication_niches'

### Como clase PublicationNiche

- [F1] shared/db/models/junctions.py:113: class PublicationNiche(Base):

---

## references / Reference

### Como string literal 'references'

- [F1] services/cv/core/controllers/cv/references.py:1: """Controller cv/references — referencias filtradas por niche."""
- [F1] services/cv/core/settings/operations.py:5: `education`, `languages`, `references`, `skills`.
- [F1] services/cv/tests/unit/test_controllers_invoke_service_and_normalize.py:24:     ('controllers.cv.references', 'References', 'list_references', True),
- [F1] services/cv/tests/unit/test_handler_routes_get_action.py:40:         'references': [],
- [F3] services/db/core/services/seed_service.py:724:     for slug, data in _load_dir('references'):
- [F3] services/db/core/services/seed_service.py:798:     """Inserta certificates, awards, education, references, languages,
- [F3] services/db/core/services/seed_service.py:849:     ('references', Reference),
- [F3] services/db/tests/integration/test_seed_command_e2e.py:38:     assert counts['references'] == 10
- [F2] shared/db/alembic/_init_schema_extras.py:55:         WHEN 'reference'          THEN 'references'
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:190:     op.create_table('references',
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:363:     sa.ForeignKeyConstraint(['reference_id'], ['references.id'], name=op.f('fk_reference_niches
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:491:     op.drop_table('references')
- [F1] shared/db/cv_repository.py:88:     references): una lista vacia provoca Zod `min(1)` error; en su lugar
- [F1] shared/db/cv_repository.py:745:             references = list(session.execute(stmt).scalars())
- [F1] shared/db/cv_repository.py:746:             ids = [r.id for r in references]
- [F1] shared/db/cv_repository.py:767:                 for r in references
- [F1] shared/db/cv_repository.py:770:         raise RepositoryError(f'references query failed: {exc}') from exc
- [F1] shared/db/cv_repository.py:844:         'references': list_references(niche=niche, locale=locale),
- [F1] shared/db/models/cv_entities.py:4: education, references, languages, skill_categories, publications.
- [F1] shared/db/models/cv_entities.py:79:     __tablename__ = 'references'
- [F1] shared/db/models/junctions.py:95:         ForeignKey('references.id', ondelete='CASCADE'), nullable=False

### Como clase Reference

- [F1] shared/db/models/cv_entities.py:72: class Reference(UUIDPKMixin, TimestampMixin, Base):

---

## reference_niches / ReferenceNiche

### Como string literal 'reference_niches'

- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:359:     op.create_table('reference_niches',
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:472:     op.drop_table('reference_niches')
- [F1] shared/db/models/junctions.py:92:     __tablename__ = 'reference_niches'

### Como clase ReferenceNiche

- [F1] shared/db/models/junctions.py:91: class ReferenceNiche(Base):

---

## niches / Niche

### Como string literal 'niches'

- [F1] services/contact_form/core/controllers/contact/create.py:29: from shared.core.niches import niche_from_origin
- [F1] services/cv/core/models/cv.py:4: - `niche`: opcional, uno de los 5 niches con CV (`CV_NICHES`) o None.
- [F1] services/cv/core/models/cv.py:10: Niches: fuente unica en `shared.core.niches` (spec sessions-normalize,
- [F1] services/cv/core/models/cv.py:20: from shared.core.niches import CV_NICHES
- [F1] services/cv/tests/unit/test_cv_query_model_normalizes_invalid_niche.py:3: Given un niche que NO esta en la lista de niches validos,
- [F3] services/db/core/services/seed_service.py:19: 1. Vocabularios deduplicados (`niches`, `skills`, `tech_tags`) primero.
- [F3] services/db/core/services/seed_service.py:77: # Los 5 niches del portfolio, en orden canonico de presentacion.
- [F3] services/db/core/services/seed_service.py:294:     """Inserta los 5 niches del catalogo y devuelve `{slug: id}`."""
- [F3] services/db/core/services/seed_service.py:374:         p.get('niches'),
- [F3] services/db/core/services/seed_service.py:469:             data.get('niches'),
- [F3] services/db/core/services/seed_service.py:585:             data.get('niches'),
- [F3] services/db/core/services/seed_service.py:602:     """Inserta categorias de skills + sus uniones a skills y niches."""
- [F3] services/db/core/services/seed_service.py:618:             data.get('niches'),
- [F3] services/db/core/services/seed_service.py:661:             data.get('niches'),
- [F3] services/db/core/services/seed_service.py:688:             data.get('niches'),
- [F3] services/db/core/services/seed_service.py:718:             data.get('niches'),
- [F3] services/db/core/services/seed_service.py:745:             data.get('niches'),
- [F3] services/db/core/services/seed_service.py:762:             data.get('niches'),
- [F3] services/db/core/services/seed_service.py:790:             data.get('niches'),
- [F3] services/db/core/services/seed_service.py:852:     ('niches', Niche),
- [F3] services/db/tests/integration/test_seed_command_e2e.py:33:     assert counts['niches'] == 5
- [F1] services/db/tests/unit/test_load_profile_parses_stats_and_niches.py:5: Then devuelve el dict del profile con stats, niches y URLs intactas
- [F1] services/db/tests/unit/test_load_profile_parses_stats_and_niches.py:27:     assert profile['niches'] == [
- [F1] shared/core/__init__.py:21: from shared.core.niches import ALL_NICHES, CV_NICHES, niche_from_origin
- [F1] shared/core/niches.py:1: """@module niches — fuente unica de verdad de los niches del portfolio.
- ... (+49 ocurrencias más)

### Como clase Niche

- [F1] shared/db/cv_repository.py:273:             from .models import Niche
- [F1] shared/db/models/__init__.py:13: from .catalog import Niche, Skill, TechTag
- [F1] shared/db/models/__init__.py:39: from .profile import Profile, ProfileNiche, ProfileStats
- [F1] shared/db/models/__init__.py:44: from .translations import NichePriority, Translation
- [F1] shared/db/models/catalog.py:20: class Niche(UUIDPKMixin, TimestampMixin, Base):

---

## niche_priorities / NichePriority

### Como string literal 'niche_priorities'

- [F3] services/db/core/services/seed_service.py:22: 4. Traducciones polimorficas + niche_priorities al final (el trigger exige
- [F3] services/db/core/services/seed_service.py:856:     ('niche_priorities', NichePriority),
- [F2] shared/db/alembic/_init_schema_extras.py:12:   polimorfica de `translations` / `niche_priorities`.
- [F2] shared/db/alembic/_init_schema_extras.py:35: # niche_priorities (apunta a tablas distintas segun `entity_type`, no puede
- [F2] shared/db/alembic/_init_schema_extras.py:77: entity_trigger_tables = ('translations', 'niche_priorities')
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:292:     op.create_table('niche_priorities',
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:430:     # 2. Trigger de integridad polimorfica de translations / niche_priorities.
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:479:     op.drop_table('niche_priorities')
- [F1] shared/db/cv_repository.py:11:   `niche_priorities.priority` desc (cuando aplica).
- [F1] shared/db/enums.py:65:     (`translations`, `niche_priorities`). Un valor por tabla de entidad
- [F1] shared/db/models/cv_entities.py:7: niches -> `<entidad>_niches`; priority -> `niche_priorities` (cuando aplica).
- [F1] shared/db/models/experience.py:34:     Niches via `experience_niches`; priority via `niche_priorities`.
- [F1] shared/db/models/junctions.py:7:    (decision del usuario): va en `niche_priorities` (translations.py).
- [F1] shared/db/models/project.py:30:     Niches via `project_niches`; priority via `niche_priorities`.
- [F1] shared/db/models/translations.py:9: - `niche_priorities` — el `priority` por (entidad, niche). Separado de las
- [F1] shared/db/models/translations.py:69:     __tablename__ = 'niche_priorities'

### Como clase NichePriority

- [F1] shared/db/models/__init__.py:44: from .translations import NichePriority, Translation
- [F1] shared/db/models/translations.py:56: class NichePriority(TimestampMixin, Base):

---

## tech_tags / TechTag

### Como string literal 'tech_tags'

- [F3] services/db/core/services/seed_service.py:19: 1. Vocabularios deduplicados (`niches`, `skills`, `tech_tags`) primero.
- [F3] services/db/core/services/seed_service.py:310:     """Upsert de un vocabulario con clave natural `name` (skills/tech_tags)."""
- [F3] services/db/core/services/seed_service.py:485:     """Reescribe el stack (`tech_tags`) de un proyecto preservando el orden.
- [F3] services/db/core/services/seed_service.py:854:     ('tech_tags', TechTag),
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:219:     op.create_table('tech_tags',
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:349:     sa.ForeignKeyConstraint(['tech_tag_id'], ['tech_tags.id'], name=op.f('fk_project_tech_tags_
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:488:     op.drop_table('tech_tags')
- [F1] shared/db/models/catalog.py:9: - `tech_tags`         — stack tecnico deduplicado (el `stack[]` de projects).
- [F1] shared/db/models/catalog.py:44:     __tablename__ = 'tech_tags'
- [F1] shared/db/models/junctions.py:137: # Familia 2: uniones de vocabulario (skills / tech_tags).
- [F1] shared/db/models/junctions.py:191:         ForeignKey('tech_tags.id', ondelete='CASCADE'), nullable=False
- [F1] shared/db/models/project.py:5: `project_tech_tags` al catalogo `tech_tags`.

### Como clase TechTag

- [F1] shared/db/models/__init__.py:13: from .catalog import Niche, Skill, TechTag
- [F1] shared/db/models/catalog.py:41: class TechTag(UUIDPKMixin, TimestampMixin, Base):

---

## event_types / EventType

### Como string literal 'event_types'

- [F1] services/tracking_pixel/core/models/tracking.py:75:     # Tipo de evento: UUID del catalogo event_types (FK). Requerido: todo
- [F1] shared/db/__init__.py:4: visitante (contacts, tracking_events, event_types, processed_stream_events)
- [F2] shared/db/alembic/_init_schema_extras.py:91: # Seed del catalogo event_types (migraciones 006 + 008). UUIDv7 literales:
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:99:     op.create_table('event_types',
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:410:     sa.ForeignKeyConstraint(['event_type_id'], ['event_types.id'], name=op.f('fk_tracking_event
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:439:     # 3. Seed del catalogo event_types (16 tipos, UUIDv7 literales).
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:442:             'event_types',
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:499:     op.drop_table('event_types')
- [F1] shared/db/models/tracking.py:1: """@module tracking — `event_types` (catalogo) + `tracking_events`.
- [F1] shared/db/models/tracking.py:14: - `event_type_id` es FK a `event_types` (PG soporta FK en tabla
- [F1] shared/db/models/tracking.py:50:     __tablename__ = 'event_types'
- [F1] shared/db/models/tracking.py:111:         UUID(as_uuid=False), ForeignKey('event_types.id')
- [F1] shared/db/models/tracking.py:136:         # FK al catalogo event_types (migracion 007).

### Como clase EventType

- [F1] shared/db/models/__init__.py:43: from .tracking import EventType, TrackingEvent
- [F1] shared/db/models/tracking.py:42: class EventType(Base):

---

## translations / Translation

### Como string literal 'translations'

- [F3] services/db/core/services/seed_service.py:855:     ('translations', Translation),
- [F1] shared/db/__init__.py:5: + contenido del CV (experiences, projects, translations, ...).
- [F2] shared/db/alembic/_init_schema_extras.py:12:   polimorfica de `translations` / `niche_priorities`.
- [F2] shared/db/alembic/_init_schema_extras.py:34: # Trigger de integridad polimorfica: valida el `entity_id` de translations /
- [F2] shared/db/alembic/_init_schema_extras.py:77: entity_trigger_tables = ('translations', 'niche_priorities')
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:227:     op.create_table('translations',
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:430:     # 2. Trigger de integridad polimorfica de translations / niche_priorities.
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:487:     op.drop_table('translations')
- [F1] shared/db/cv_repository.py:12: - `locale` — `es|en`. Selecciona la fila de `translations` por locale.
- [F1] shared/db/cv_repository.py:269:             translations = _translations_map(
- [F1] shared/db/cv_repository.py:285:             availability = translations.get('availability') or None
- [F1] shared/db/cv_repository.py:304:                     'headline': translations.get('headline', {}),
- [F1] shared/db/cv_repository.py:305:                     'summary': translations.get('summary', {}),
- [F1] shared/db/cv_repository.py:347:             translations = _translations_map(session, 'experience', ids)
- [F1] shared/db/cv_repository.py:390:                 summary = translations.get(exp.id, {}).get('summary') or None
- [F1] shared/db/cv_repository.py:401:                 'role': translations.get(exp.id, {}).get('role', {}),
- [F1] shared/db/cv_repository.py:450:             translations = _translations_map(session, 'project', ids)
- [F1] shared/db/cv_repository.py:502:                     translations.get(proj.id, {}).get('description') or None
- [F1] shared/db/cv_repository.py:505:                     translations.get(proj.id, {}).get('case_study') or None
- [F1] shared/db/cv_repository.py:518:                 'summary': translations.get(proj.id, {}).get('
- ... (+34 ocurrencias más)

### Como clase Translation

- [F1] shared/db/models/__init__.py:44: from .translations import NichePriority, Translation
- [F1] shared/db/models/translations.py:26: class Translation(TimestampMixin, Base):

---

## contacts / Contact

### Como string literal 'contacts'

- [F1] services/contact_form/core/services/contact_service.py:85:     - ip/country/user_agent ya NO se persisten en `contacts` (viven en
- [F1] services/contact_form/core/services/contact_service.py:135:         # Paso 2: INSERT del contact. El ORM de `contacts` ya NO tiene
- [F1] services/contact_form/core/services/contact_service.py:316:         `ensure_session_and_visit` (no se persisten en `contacts`).
- [F1] services/contact_form/core/services/contact_service.py:329:     contacts NO duplica datos de origen (ip/country/user_agent): viven
- [F1] services/contact_form/tests/conftest.py:70:     Crea con moto las cuatro tablas DynamoDB (contacts, cache,
- [F1] services/contact_form/tests/conftest.py:76:     # ya no escribe a DynamoDB.contacts. La connection string de Neon va
- [F1] services/contact_form/tests/conftest.py:115:         # La tabla `contacts` se elimino (spec direct-neon-writes): el
- [F1] services/contact_form/tests/integration/_fixtures/__init__.py:110:     """Cantidad de items en la tabla `contacts` (DynamoDB mockeada)."""
- [F1] services/contact_form/tests/integration/_fixtures/__init__.py:112:         'portfolio-contacts-test'
- [F1] services/contact_form/tests/integration/_fixtures/__init__.py:120:         'portfolio-contacts-test'
- [F1] services/contact_form/tests/integration/conftest.py:86:         TableName='portfolio-contacts-test',
- [F1] services/contact_form/tests/integration/conftest.py:125:     Crea con moto las 4 tablas DynamoDB (contacts, cache,
- [F1] services/contact_form/tests/integration/conftest.py:131:     monkeypatch.setenv('CONTACTS_TABLE_NAME', 'portfolio-contacts-test')
- [F1] services/contact_form/tests/unit/test_contact_service_persists_and_sends_email.py:66:     # Assert: una sola escritura a contacts con el payload esperado
- [F1] services/contact_form/tests/unit/test_contact_service_persists_and_sends_email.py:75:     # contacts (movidos a sessions/session_visits).
- [F3] services/db/core/services/seed_service.py:325:     contacts = p['contacts']
- [F3] services/db/core/services/seed_service.py:334:             'email': contacts['email'],
- [F3] services/db/core/services/seed_service.py:335:             'phone': contacts.get('phone'),
- [F3] services/db/core/services/seed_service.py:336:             'linkedin_url': contacts['linkedin'],
- [F3] services/db/core/services/seed_service.py:337:             'github_url': contacts['github'],
- [F3] services/db/core/services/seed_service.py:338:             'website_url': contacts.get('website'),
- [F1] services/db/tests/integration/test_tables_command_e2e.py:28:         [('public.tracking_events', 15000), ('public.contacts', 200)]
- [F1] services/db/tests/integration/test_tables_command_e2e.py:43:             {'name': 'public.contacts', 'rows': 200},
- [F1] services/db/tests/unit/test_handler_routes_tables_command.py:27:                 'tables': [{'name': 'public.contacts', 'rows': 200}],
- [F1] services/db/tests/unit/test_handler_routes_tables_command.py:41:         'tables': [{'name': 'public.contacts', 'rows': 200}],
- ... (+82 ocurrencias más)

### Como clase Contact

- [F1] services/contact_form/core/controllers/contact/create.py:26: from models.contact import ContactCreatedOutput, ContactCreateModel
- [F1] services/contact_form/tests/unit/test_contact_model_accepts_valid_form.py:14:     from models.contact import ContactCreateModel
- [F1] services/contact_form/tests/unit/test_contact_model_rejects_invalid_email.py:15:     from models.contact import ContactCreateModel
- [F1] services/contact_form/tests/unit/test_contact_model_rejects_missing_name.py:15:     from models.contact import ContactCreateModel
- [F1] services/contact_form/tests/unit/test_contact_model_sanitizes_html_in_message.py:14:     from models.contact import ContactCreateModel
- [F1] shared/db/__init__.py:12:     from shared.db.models import Contact, Experience
- [F1] shared/db/models/__init__.py:8:     from shared.db.models import Contact, Experience, TrackingEvent
- [F1] shared/db/models/__init__.py:14: from .contact import Contact
- [F1] shared/db/models/contact.py:32: class Contact(Base):
- [F1] shared/db/repository.py:25: from .models import Contact, SessionVisit, TrackingEvent
- [F1] shared/db/session.py:55:         from shared.db.models import Contact
- [F1] shared/dynamodb/models/__init__.py:8: from shared.dynamodb.models.contact import ContactItem
- [F1] shared/tests/integration/shared/dynamodb/test_base_model_conditional_update_e2e.py:10: from shared.dynamodb import ContactItem
- [F1] shared/tests/integration/shared/dynamodb/test_base_model_crud_lifecycle_e2e.py:11: from shared.dynamodb import ContactItem
- [F1] shared/tests/integration/shared/dynamodb/test_base_model_put_if_absent_e2e.py:10: from shared.dynamodb import ContactItem
- ... (+6 ocurrencias más)

---

## sessions / Session

### Como string literal 'sessions'

- [F1] services/contact_form/core/controllers/contact/create.py:47:     Spec sessions-normalize, decision 2: si el form envia `session_id`
- [F1] services/contact_form/core/controllers/contact/create.py:54:     en localStorage, asi sessions con tracking previo no chocan).
- [F1] services/contact_form/core/models/contact.py:41:     # (spec sessions-normalize, decision 6).
- [F1] services/contact_form/core/services/contact_service.py:75:     """Persiste un contact submission en Neon (sessions + visits + contact).
- [F1] services/contact_form/core/services/contact_service.py:77:     Spec sessions-normalize:
- [F1] services/contact_form/core/services/contact_service.py:81:     - El service UPSERTea `sessions` + `session_visits` via el helper
- [F1] services/contact_form/core/services/contact_service.py:86:       sessions/session_visits via FK).
- [F1] services/contact_form/core/services/contact_service.py:136:         # ip/country/user_agent (movidos a sessions).
- [F1] services/contact_form/core/services/contact_service.py:298:     """Persiste el contacto (sessions + visit + contact) y notifica owner.
- [F1] services/contact_form/core/services/contact_service.py:302:     UPSERTea sessions + session_visits y INSERTea el contact en la misma
- [F1] services/contact_form/core/services/contact_service.py:303:     tx (spec sessions-normalize) y dispara el email.
- [F1] services/contact_form/core/services/contact_service.py:330:     en sessions/session_visits via FK (spec sessions-normalize).
- [F1] services/contact_form/tests/conftest.py:185:     `services.contact_service`. Spec sessions-normalize: el contact
- [F1] services/contact_form/tests/conftest.py:210:     Spec sessions-normalize: el service UPSERTea session + visit antes
- [F1] services/contact_form/tests/unit/test_contact_service_persists_and_sends_email.py:10: Spec sessions-normalize: el service UPSERTea session + visit antes del
- [F1] services/contact_form/tests/unit/test_contact_service_persists_and_sends_email.py:13: ip/country/user_agent (movidos a sessions/session_visits).
- [F1] services/contact_form/tests/unit/test_contact_service_persists_and_sends_email.py:54:     # a sessions, no al contact_payload)
- [F1] services/contact_form/tests/unit/test_contact_service_persists_and_sends_email.py:74:     # Spec sessions-normalize: ip/country/user_agent ya NO van en
- [F1] services/contact_form/tests/unit/test_contact_service_persists_and_sends_email.py:75:     # contacts (movidos a sessions/session_visits).
- [F1] services/cv/core/models/cv.py:10: Niches: fuente unica en `shared.core.niches` (spec sessions-normalize,
- [F1] services/tracking_pixel/core/services/tracking_service.py:113:     """Persiste sessions + session_visits + tracking_events en 1 tx.
- [F1] services/tracking_pixel/core/services/tracking_service.py:115:     Spec sessions-normalize: el INSERT del tracking_event va junto con
- [F1] services/tracking_pixel/core/services/tracking_service.py:129:     se persisten en sessions/session_visits via el helper — el ORM de
- [F1] services/tracking_pixel/core/services/tracking_service.py:201:     Spec sessions-normalize: el payload se enriquece con `ip`/`country`/
- [F1] services/tracking_pixel/tests/conftest.py:140:     Spec sessions-normalize: el service ahora UPSERTea session + visit
- ... (+59 ocurrencias más)

### Como clase Session

- [F3] services/db/core/services/seed_service.py:69: from sqlalchemy.orm import Session
- [F1] shared/db/cv_repository.py:30: from sqlalchemy.orm import Session
- [F1] shared/db/models/__init__.py:41: from .session import Session
- [F1] shared/db/models/__init__.py:42: from .session_visit import SessionVisit
- [F1] shared/db/models/session.py:24: class Session(Base):
- [F1] shared/db/repository.py:23: from sqlalchemy.orm import Session as OrmSession
- [F1] shared/db/repository.py:25: from .models import Contact, SessionVisit, TrackingEvent
- [F1] shared/db/repository.py:26: from .models import Session as SessionRow
- [F1] shared/db/session.py:22: from sqlalchemy.orm import Session, sessionmaker

---

## session_visits / SessionVisit

### Como string literal 'session_visits'

- [F1] services/contact_form/core/services/contact_service.py:81:     - El service UPSERTea `sessions` + `session_visits` via el helper
- [F1] services/contact_form/core/services/contact_service.py:86:       sessions/session_visits via FK).
- [F1] services/contact_form/core/services/contact_service.py:302:     UPSERTea sessions + session_visits y INSERTea el contact en la misma
- [F1] services/contact_form/core/services/contact_service.py:320:         para `session_visits.niche` (decision 6).
- [F1] services/contact_form/core/services/contact_service.py:330:     en sessions/session_visits via FK (spec sessions-normalize).
- [F1] services/contact_form/tests/unit/test_contact_service_persists_and_sends_email.py:13: ip/country/user_agent (movidos a sessions/session_visits).
- [F1] services/contact_form/tests/unit/test_contact_service_persists_and_sends_email.py:75:     # contacts (movidos a sessions/session_visits).
- [F1] services/tracking_pixel/core/services/tracking_service.py:113:     """Persiste sessions + session_visits + tracking_events en 1 tx.
- [F1] services/tracking_pixel/core/services/tracking_service.py:129:     se persisten en sessions/session_visits via el helper — el ORM de
- [F1] services/tracking_pixel/tests/conftest.py:172:     session_visits). Si el test tambien quiere verificar los args del
- [F1] services/tracking_pixel/tests/unit/test_process_tracking_event_persists_enrichment.py:6:      ip + country (datos del visitante van a sessions/session_visits).
- [F1] services/tracking_pixel/tests/unit/test_process_tracking_event_persists_enrichment.py:59:             f'movido a sessions/session_visits'
- [F1] services/tracking_pixel/tests/unit/test_save_tracking_event_persists_item.py:16: sessions/session_visits.
- [F1] services/tracking_pixel/tests/unit/test_save_tracking_event_persists_item.py:65:     # (spec sessions-normalize: movidas a sessions/session_visits)
- [F1] shared/core/niches.py:9: `session_visits.niche` y `tracking_events.niche`) y para inferir el
- [F1] shared/core/niches.py:30: session_visits.niche, y validacion de entrada cuando aplique."""
- [F2] shared/db/alembic/versions/d4e5f6a7b8c9_introduce_sessions_visits.py:1: """introduce sessions + session_visits, FK desde tracking_events y contacts
- [F2] shared/db/alembic/versions/d4e5f6a7b8c9_introduce_sessions_visits.py:16: - `session_visits` (cada cambio de network/utm): visit_id PK (UUIDv7
- [F2] shared/db/alembic/versions/d4e5f6a7b8c9_introduce_sessions_visits.py:24: sessions(session_id) y session_visits(visit_id).
- [F2] shared/db/alembic/versions/d4e5f6a7b8c9_introduce_sessions_visits.py:34: DROP TABLE session_visits, DROP TABLE sessions. Las columnas vuelven a
- [F2] shared/db/alembic/versions/d4e5f6a7b8c9_introduce_sessions_visits.py:53:     """Crea sessions + session_visits, drop columnas redundantes, FKs."""
- [F2] shared/db/alembic/versions/d4e5f6a7b8c9_introduce_sessions_visits.py:94:     # 3. CREATE TABLE session_visits ------------------------------------
- [F2] shared/db/alembic/versions/d4e5f6a7b8c9_introduce_sessions_visits.py:96:         'session_visits',
- [F2] shared/db/alembic/versions/d4e5f6a7b8c9_introduce_sessions_visits.py:143:         'session_visits',
- [F2] shared/db/alembic/versions/d4e5f6a7b8c9_introduce_sessions_visits.py:148:         'session_visits',
- ... (+25 ocurrencias más)

### Como clase SessionVisit

- [F1] shared/db/models/__init__.py:42: from .session_visit import SessionVisit
- [F1] shared/db/models/session_visit.py:29: class SessionVisit(Base):
- [F1] shared/db/repository.py:25: from .models import Contact, SessionVisit, TrackingEvent

---

## tracking_events / TrackingEvent

### Como string literal 'tracking_events'

- [F1] services/db/tests/integration/test_tables_command_e2e.py:28:         [('public.tracking_events', 15000), ('public.contacts', 200)]
- [F1] services/db/tests/integration/test_tables_command_e2e.py:42:             {'name': 'public.tracking_events', 'rows': 15000},
- [F1] services/tracking_pixel/core/services/tracking_service.py:18: La tabla `tracking_events` en Neon NO tiene PK fisica, asi que no usamos
- [F1] services/tracking_pixel/core/services/tracking_service.py:113:     """Persiste sessions + session_visits + tracking_events en 1 tx.
- [F1] services/tracking_pixel/core/services/tracking_service.py:123:     2. INSERT en `tracking_events` con el `visit_id` retornado.
- [F1] services/tracking_pixel/core/services/tracking_service.py:130:     tracking_events YA NO las tiene.
- [F1] services/tracking_pixel/core/services/tracking_service.py:169:         # Paso 2: INSERT en tracking_events con visit_id.
- [F1] services/tracking_pixel/tests/conftest.py:141:     via este helper antes del INSERT de tracking_events. Los tests
- [F1] services/tracking_pixel/tests/conftest.py:171:     `tracking_events` (sin ip/country/ua/utm — esos viven en sessions y
- [F1] services/tracking_pixel/tests/unit/test_process_tracking_event_persists_enrichment.py:9: de tracking_events. Los kwargs del helper se capturan via fixture
- [F1] services/tracking_pixel/tests/unit/test_process_tracking_event_persists_enrichment.py:35:     # Assert: una sola escritura tracking_events + una sola invocacion
- [F1] services/tracking_pixel/tests/unit/test_process_tracking_event_persists_enrichment.py:40:     # El enrichment va al HELPER, no al payload de tracking_events.
- [F1] services/tracking_pixel/tests/unit/test_process_tracking_event_persists_enrichment.py:50:     # tracking_events ya NO tiene ip/country/browser/os/device_type/utm_*
- [F1] services/tracking_pixel/tests/unit/test_process_tracking_event_persists_enrichment.py:58:             f'tracking_events no debe persistir {forbidden}: '
- [F1] services/tracking_pixel/tests/unit/test_save_tracking_event_persists_item.py:10: helper y luego inserta tracking_events con `visit_id`. Mockeamos
- [F1] services/tracking_pixel/tests/unit/test_save_tracking_event_persists_item.py:12: del payload de tracking_events.
- [F1] services/tracking_pixel/tests/unit/test_save_tracking_event_persists_item.py:45:     # Assert: una sola fila tracking_events se escribio
- [F1] services/tracking_pixel/tests/unit/test_save_tracking_event_persists_item.py:58:     # Columnas viejas que YA NO van en tracking_events:
- [F1] shared/core/niches.py:9: `session_visits.niche` y `tracking_events.niche`) y para inferir el
- [F1] shared/db/__init__.py:4: visitante (contacts, tracking_events, event_types, processed_stream_events)
- [F2] shared/db/alembic/_init_schema_extras.py:25:     """SQL: la particion default de `tracking_events`. Sin ella, un INSERT
- [F2] shared/db/alembic/_init_schema_extras.py:30:         'PARTITION OF tracking_events DEFAULT'
- [F2] shared/db/alembic/env.py:17: - `tracking_events_default`: particion de `tracking_events`, no una tabla
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:381:     op.create_table('tracking_events',
- [F2] shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py:413:     op.create_index('idx_tracking_country', 'tracking_events', ['country'], unique=False, postg
- ... (+104 ocurrencias más)

### Como clase TrackingEvent

- [F1] shared/db/models/__init__.py:8:     from shared.db.models import Contact, Experience, TrackingEvent
- [F1] shared/db/models/__init__.py:43: from .tracking import EventType, TrackingEvent
- [F1] shared/db/models/tracking.py:62: class TrackingEvent(Base):
- [F1] shared/db/repository.py:25: from .models import Contact, SessionVisit, TrackingEvent
- [F1] shared/dynamodb/models/__init__.py:11: from shared.dynamodb.models.tracking import TrackingEventItem
- [F1] shared/tests/integration/shared/dynamodb/test_base_model_check_schema_detects_drift_e2e.py:11: from shared.dynamodb import TrackingEventItem
- [F1] shared/tests/integration/shared/dynamodb/test_base_model_check_schema_in_sync_e2e.py:10: from shared.dynamodb import TrackingEventItem
- [F1] shared/tests/integration/shared/dynamodb/test_base_model_query_by_gsi_e2e.py:10: from shared.dynamodb import TrackingEventItem
- [F1] shared/tests/integration/shared/dynamodb/test_base_model_query_by_partition_key_e2e.py:11: from shared.dynamodb import TrackingEventItem
- [F1] shared/tests/unit/shared/db/test_insert_tracking_adds_tracking_event.py:14: from shared.db.models import TrackingEvent
- [F1] shared/tests/integration/shared/dynamodb/test_base_model_check_schema_reports_drift.py:12: from shared.dynamodb import ContactItem, TrackingEventItem
- [F1] shared/tests/unit/shared/dynamodb/test_base_model_create_table_from_meta.py:11: from shared.dynamodb import TrackingEventItem
- [F1] shared/tests/unit/shared/dynamodb/test_base_model_from_item_converts_decimal.py:11: from shared.dynamodb import RateLimitBucketItem, TrackingEventItem
- [F1] shared/tests/unit/shared/dynamodb/test_base_model_query_by_gsi.py:11: from shared.dynamodb import TrackingEventItem
- [F1] shared/tests/unit/shared/dynamodb/test_base_model_query_by_partition_key.py:12: from shared.dynamodb import TrackingEventItem
- ... (+2 ocurrencias más)

---

## Resumen por archivo (top hot-spots)

Archivos con mas hits (mas dificil de migrar):

1. shared/db/alembic/versions/81c2cc51db34_init_unified_schema.py — 138 hits
2. shared/db/alembic/versions/d4e5f6a7b8c9_introduce_sessions_visits.py — 111 hits
3. shared/db/cv_repository.py — 107 hits
4. services/db/core/services/seed_service.py — 82 hits
5. shared/db/models/junctions.py — 51 hits
6. shared/db/models/cv_entities.py — 34 hits
7. shared/db/models/__init__.py — 26 hits
8. shared/db/repository.py — 25 hits
9. shared/db/alembic/_init_schema_extras.py — 23 hits
10. shared/db/models/profile.py — 21 hits
11. shared/db/models/project.py — 21 hits
12. shared/db/models/tracking.py — 20 hits
13. shared/db/alembic/versions/c3d4e5f6a7b8_drop_cloudfront_expires_page_fields.py — 20 hits
14. shared/db/alembic/versions/b2c3d4e5f6a7_drop_stream_event_id.py — 18 hits
15. services/contact_form/core/services/contact_service.py — 18 hits
