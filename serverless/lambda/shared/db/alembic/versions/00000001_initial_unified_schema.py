"""initial unified schema

Revision ID: 00000001
Revises:
Create Date: 2026-05-24 21:40:22.342963

Schema unificado del portfolio (37 tablas con prefijo de dominio):
- cv_*  (28): perfil + experiencia + proyectos + skills + entidades CV
- vis_*  (4): visitor tracking (contacts, sessions, session_visits,
              tracking_events) + particion default fisica
- tax_*  (4): catalogos compartidos (niches, niche_priorities,
              tech_tags, event_types)
- i18n_* (1): translations polimorficas

Es la migracion inicial del schema. Reemplaza el conjunto historico
de 9 migraciones (81c2cc51db34 ... e5f6a7b8c9d0) que vivian antes del
plan group-tables-by-domain. Consolidado en una sola init porque la
data del CV es 100% regenerable desde YAMLs en services/db/core/seeds/
y los entornos se rehacen desde cero (decision del usuario, mayo 2026).

Incluye:
- 37 op.create_table()
- CREATE EXTENSION citext + unaccent
- ENUMs nativos PG (los crea inline cada create_table)
- vis_tracking_events PARTITIONED RANGE(created_at) + particion default
- Trigger PL/pgSQL assert_entity_exists para integridad polimorfica de
  i18n_translations y tax_niche_priorities (entity_id NO tiene FK
  fisica, valida el trigger)
- Seed initial de tax_event_types (16 tipos fijos con UUIDv7 literales
  que el frontend replica como constantes TS)
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from shared.db.alembic._init_schema_extras import (
    create_citext_extension,
    create_partition_default,
    entity_trigger_fn_sql,
    entity_trigger_tables,
    enum_type_names,
    event_types_seed,
)

# revision identifiers, used by Alembic.
revision: str = '00000001'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Extensions PG requeridas por las columnas / funciones del schema.
    op.execute(create_citext_extension())
    op.execute('CREATE EXTENSION IF NOT EXISTS unaccent')

    # 37 tablas (autogenerado por Alembic desde shared/db/models/).
    op.create_table('cv_awards',
    sa.Column('slug', sa.String(length=120), nullable=False),
    sa.Column('issuer', sa.String(length=200), nullable=False),
    sa.Column('awarded_on', sa.Date(), nullable=False),
    sa.Column('url', sa.String(length=500), nullable=True),
    sa.Column('id', sa.UUID(as_uuid=False), server_default=sa.text('uuidv7()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_cv_awards')),
    sa.UniqueConstraint('slug', name=op.f('uq_cv_awards_slug'))
    )
    op.create_table('cv_certificates',
    sa.Column('slug', sa.String(length=120), nullable=False),
    sa.Column('title', sa.String(length=300), nullable=False),
    sa.Column('issuer', sa.String(length=200), nullable=False),
    sa.Column('issued_on', sa.Date(), nullable=False),
    sa.Column('url', sa.String(length=500), nullable=False),
    sa.Column('id', sa.UUID(as_uuid=False), server_default=sa.text('uuidv7()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_cv_certificates')),
    sa.UniqueConstraint('slug', name=op.f('uq_cv_certificates_slug'))
    )
    op.create_table('cv_education_entries',
    sa.Column('slug', sa.String(length=120), nullable=False),
    sa.Column('institution', sa.String(length=200), nullable=False),
    sa.Column('started_on', sa.Date(), nullable=False),
    sa.Column('ended_on', sa.Date(), nullable=True),
    sa.Column('url', sa.String(length=500), nullable=True),
    sa.Column('id', sa.UUID(as_uuid=False), server_default=sa.text('uuidv7()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_cv_education_entries')),
    sa.UniqueConstraint('slug', name=op.f('uq_cv_education_entries_slug'))
    )
    op.create_table('cv_endorsements',
    sa.Column('slug', sa.String(length=120), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('role', sa.String(length=200), nullable=False),
    sa.Column('company', sa.String(length=200), nullable=True),
    sa.Column('linkedin_url', sa.String(length=500), nullable=False),
    sa.Column('id', sa.UUID(as_uuid=False), server_default=sa.text('uuidv7()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_cv_endorsements')),
    sa.UniqueConstraint('slug', name=op.f('uq_cv_endorsements_slug'))
    )
    op.create_table('cv_experiences',
    sa.Column('slug', sa.String(length=120), nullable=False),
    sa.Column('company', sa.String(length=160), nullable=False),
    sa.Column('country', sa.String(length=120), nullable=False),
    sa.Column('company_url', sa.String(length=500), nullable=True),
    sa.Column('started_on', sa.Date(), nullable=False),
    sa.Column('ended_on', sa.Date(), nullable=True),
    sa.Column('seniority', sa.Enum('intern', 'junior', 'mid', 'senior', 'lead', name='seniority'), nullable=False),
    sa.Column('metrics_estimated', sa.Boolean(), nullable=False),
    sa.Column('id', sa.UUID(as_uuid=False), server_default=sa.text('uuidv7()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_cv_experiences')),
    sa.UniqueConstraint('slug', name=op.f('uq_cv_experiences_slug'))
    )
    op.create_table('cv_languages',
    sa.Column('slug', sa.String(length=120), nullable=False),
    sa.Column('id', sa.UUID(as_uuid=False), server_default=sa.text('uuidv7()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_cv_languages')),
    sa.UniqueConstraint('slug', name=op.f('uq_cv_languages_slug'))
    )
    op.create_table('cv_profiles',
    sa.Column('name', sa.String(length=160), nullable=False),
    sa.Column('handle', sa.String(length=80), nullable=False),
    sa.Column('location', sa.String(length=160), nullable=False),
    sa.Column('email', sa.String(length=254), nullable=False),
    sa.Column('phone', sa.String(length=40), nullable=True),
    sa.Column('linkedin_url', sa.String(length=500), nullable=False),
    sa.Column('github_url', sa.String(length=500), nullable=False),
    sa.Column('website_url', sa.String(length=500), nullable=True),
    sa.Column('avatar_url', sa.String(length=500), nullable=False),
    sa.Column('id', sa.UUID(as_uuid=False), server_default=sa.text('uuidv7()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_cv_profiles')),
    sa.UniqueConstraint('handle', name=op.f('uq_cv_profiles_handle'))
    )
    op.create_table('cv_projects',
    sa.Column('slug', sa.String(length=120), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('url', sa.String(length=500), nullable=True),
    sa.Column('links', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('repo', sa.String(length=500), nullable=True),
    sa.Column('status', sa.Enum('active', 'inactive', 'concept', name='project_status'), nullable=False),
    sa.Column('project_type', sa.Enum('web', 'mobile', 'cli', 'library', 'ai', 'fintech-platform', name='project_type'), nullable=False),
    sa.Column('is_confidential', sa.Boolean(), nullable=False),
    sa.Column('metrics_estimated', sa.Boolean(), nullable=False),
    sa.Column('id', sa.UUID(as_uuid=False), server_default=sa.text('uuidv7()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_cv_projects')),
    sa.UniqueConstraint('slug', name=op.f('uq_cv_projects_slug'))
    )
    op.create_table('cv_publications',
    sa.Column('slug', sa.String(length=120), nullable=False),
    sa.Column('title', sa.String(length=300), nullable=False),
    sa.Column('platform', sa.String(length=120), nullable=False),
    sa.Column('url', sa.String(length=500), nullable=False),
    sa.Column('canonical_url', sa.String(length=500), nullable=True),
    sa.Column('published_on', sa.Date(), nullable=False),
    sa.Column('id', sa.UUID(as_uuid=False), server_default=sa.text('uuidv7()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_cv_publications')),
    sa.UniqueConstraint('slug', name=op.f('uq_cv_publications_slug'))
    )
    op.create_table('cv_skill_categories',
    sa.Column('slug', sa.String(length=120), nullable=False),
    sa.Column('kind', sa.Enum('technical', 'soft', name='skill_kind'), nullable=False),
    sa.Column('id', sa.UUID(as_uuid=False), server_default=sa.text('uuidv7()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_cv_skill_categories')),
    sa.UniqueConstraint('slug', name=op.f('uq_cv_skill_categories_slug'))
    )
    op.create_table('cv_skills',
    sa.Column('slug', sa.String(length=120), nullable=False),
    sa.Column('name', sa.String(length=120), nullable=False),
    sa.Column('id', sa.UUID(as_uuid=False), server_default=sa.text('uuidv7()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_cv_skills')),
    sa.UniqueConstraint('slug', name=op.f('uq_cv_skills_slug'))
    )
    op.create_table('i18n_translations',
    sa.Column('entity_type', sa.Enum('profile', 'experience', 'experience_bullet', 'project', 'project_case_study', 'project_metric', 'skill_category', 'certificate', 'award', 'education', 'endorsement', 'language', 'publication', name='entity_type'), nullable=False),
    sa.Column('entity_id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('field', sa.String(length=64), nullable=False),
    sa.Column('locale', sa.Enum('es', 'en', name='locale'), nullable=False),
    sa.Column('value', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('entity_type', 'entity_id', 'field', 'locale', name=op.f('pk_i18n_translations')),
    comment='Textos bilingues del CV. entity_id polimorfico — integridad via trigger assert_entity_exists.'
    )
    op.create_table('tax_event_types',
    sa.Column('id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('code_name', sa.Text(), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_tax_event_types')),
    sa.UniqueConstraint('code_name', name=op.f('uq_tax_event_types_code_name'))
    )
    op.create_table('tax_niches',
    sa.Column('slug', sa.String(length=32), nullable=False),
    sa.Column('display_order', sa.Integer(), nullable=False),
    sa.Column('id', sa.UUID(as_uuid=False), server_default=sa.text('uuidv7()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_tax_niches')),
    sa.UniqueConstraint('slug', name=op.f('uq_tax_niches_slug'))
    )
    op.create_table('tax_tech_tags',
    sa.Column('slug', sa.String(length=120), nullable=False),
    sa.Column('name', sa.String(length=120), nullable=False),
    sa.Column('id', sa.UUID(as_uuid=False), server_default=sa.text('uuidv7()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_tax_tech_tags')),
    sa.UniqueConstraint('slug', name=op.f('uq_tax_tech_tags_slug'))
    )
    op.create_table('vis_sessions',
    sa.Column('session_id', sa.Text(), nullable=False),
    sa.Column('first_seen_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('last_seen_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('user_agent', sa.Text(), nullable=True),
    sa.Column('browser', sa.Text(), nullable=True),
    sa.Column('browser_version', sa.Text(), nullable=True),
    sa.Column('os', sa.Text(), nullable=True),
    sa.Column('device_type', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('session_id', name=op.f('pk_vis_sessions'))
    )
    op.create_index('idx_vis_sessions_first_seen_brin', 'vis_sessions', ['first_seen_at'], unique=False, postgresql_using='brin')
    op.create_index('idx_vis_sessions_last_seen', 'vis_sessions', [sa.literal_column('last_seen_at DESC')], unique=False)
    op.create_table('cv_award_niches',
    sa.Column('award_id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('niche_id', sa.UUID(as_uuid=False), nullable=False),
    sa.ForeignKeyConstraint(['award_id'], ['cv_awards.id'], name=op.f('fk_cv_award_niches_award_id_cv_awards'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['niche_id'], ['tax_niches.id'], name=op.f('fk_cv_award_niches_niche_id_tax_niches'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('award_id', 'niche_id', name=op.f('pk_cv_award_niches'))
    )
    op.create_table('cv_certificate_niches',
    sa.Column('certificate_id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('niche_id', sa.UUID(as_uuid=False), nullable=False),
    sa.ForeignKeyConstraint(['certificate_id'], ['cv_certificates.id'], name=op.f('fk_cv_certificate_niches_certificate_id_cv_certificates'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['niche_id'], ['tax_niches.id'], name=op.f('fk_cv_certificate_niches_niche_id_tax_niches'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('certificate_id', 'niche_id', name=op.f('pk_cv_certificate_niches'))
    )
    op.create_table('cv_education_entry_niches',
    sa.Column('education_entry_id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('niche_id', sa.UUID(as_uuid=False), nullable=False),
    sa.ForeignKeyConstraint(['education_entry_id'], ['cv_education_entries.id'], name=op.f('fk_cv_education_entry_niches_education_entry_id_cv_education_entries'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['niche_id'], ['tax_niches.id'], name=op.f('fk_cv_education_entry_niches_niche_id_tax_niches'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('education_entry_id', 'niche_id', name=op.f('pk_cv_education_entry_niches'))
    )
    op.create_table('cv_endorsement_niches',
    sa.Column('endorsement_id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('niche_id', sa.UUID(as_uuid=False), nullable=False),
    sa.ForeignKeyConstraint(['endorsement_id'], ['cv_endorsements.id'], name=op.f('fk_cv_endorsement_niches_endorsement_id_cv_endorsements'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['niche_id'], ['tax_niches.id'], name=op.f('fk_cv_endorsement_niches_niche_id_tax_niches'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('endorsement_id', 'niche_id', name=op.f('pk_cv_endorsement_niches'))
    )
    op.create_table('cv_experience_bullets',
    sa.Column('experience_id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('kind', sa.Enum('responsibility', 'achievement', name='bullet_kind'), nullable=False),
    sa.Column('position', sa.Integer(), nullable=False),
    sa.Column('id', sa.UUID(as_uuid=False), server_default=sa.text('uuidv7()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['experience_id'], ['cv_experiences.id'], name=op.f('fk_cv_experience_bullets_experience_id_cv_experiences'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_cv_experience_bullets')),
    sa.UniqueConstraint('experience_id', 'kind', 'position', name='experience_bullet')
    )
    op.create_table('cv_experience_niches',
    sa.Column('experience_id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('niche_id', sa.UUID(as_uuid=False), nullable=False),
    sa.ForeignKeyConstraint(['experience_id'], ['cv_experiences.id'], name=op.f('fk_cv_experience_niches_experience_id_cv_experiences'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['niche_id'], ['tax_niches.id'], name=op.f('fk_cv_experience_niches_niche_id_tax_niches'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('experience_id', 'niche_id', name=op.f('pk_cv_experience_niches'))
    )
    op.create_table('cv_experience_skills',
    sa.Column('experience_id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('skill_id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('kind', sa.Enum('technical', 'soft', name='skill_kind'), nullable=False),
    sa.ForeignKeyConstraint(['experience_id'], ['cv_experiences.id'], name=op.f('fk_cv_experience_skills_experience_id_cv_experiences'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['skill_id'], ['cv_skills.id'], name=op.f('fk_cv_experience_skills_skill_id_cv_skills'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('experience_id', 'skill_id', 'kind', name=op.f('pk_cv_experience_skills'))
    )
    op.create_table('cv_language_niches',
    sa.Column('language_id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('niche_id', sa.UUID(as_uuid=False), nullable=False),
    sa.ForeignKeyConstraint(['language_id'], ['cv_languages.id'], name=op.f('fk_cv_language_niches_language_id_cv_languages'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['niche_id'], ['tax_niches.id'], name=op.f('fk_cv_language_niches_niche_id_tax_niches'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('language_id', 'niche_id', name=op.f('pk_cv_language_niches'))
    )
    op.create_table('cv_profile_niches',
    sa.Column('profile_id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('niche_id', sa.UUID(as_uuid=False), nullable=False),
    sa.ForeignKeyConstraint(['niche_id'], ['tax_niches.id'], name=op.f('fk_cv_profile_niches_niche_id_tax_niches'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['profile_id'], ['cv_profiles.id'], name=op.f('fk_cv_profile_niches_profile_id_cv_profiles'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('profile_id', 'niche_id', name=op.f('pk_cv_profile_niches'))
    )
    op.create_table('cv_profile_stats',
    sa.Column('profile_id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('years_experience', sa.Integer(), nullable=False),
    sa.Column('companies', sa.Integer(), nullable=False),
    sa.Column('countries', sa.Integer(), nullable=False),
    sa.Column('certifications', sa.Integer(), nullable=False),
    sa.Column('id', sa.UUID(as_uuid=False), server_default=sa.text('uuidv7()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['profile_id'], ['cv_profiles.id'], name=op.f('fk_cv_profile_stats_profile_id_cv_profiles'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_cv_profile_stats')),
    sa.UniqueConstraint('profile_id', name=op.f('uq_cv_profile_stats_profile_id'))
    )
    op.create_table('cv_project_case_studies',
    sa.Column('project_id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('id', sa.UUID(as_uuid=False), server_default=sa.text('uuidv7()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['project_id'], ['cv_projects.id'], name=op.f('fk_cv_project_case_studies_project_id_cv_projects'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_cv_project_case_studies')),
    sa.UniqueConstraint('project_id', name=op.f('uq_cv_project_case_studies_project_id'))
    )
    op.create_table('cv_project_metrics',
    sa.Column('project_id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('metric_key', sa.String(length=80), nullable=False),
    sa.Column('metric_value', sa.String(length=500), nullable=False),
    sa.Column('position', sa.Integer(), nullable=False),
    sa.Column('id', sa.UUID(as_uuid=False), server_default=sa.text('uuidv7()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['project_id'], ['cv_projects.id'], name=op.f('fk_cv_project_metrics_project_id_cv_projects'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_cv_project_metrics')),
    sa.UniqueConstraint('project_id', 'metric_key', name='project_metric')
    )
    op.create_table('cv_project_niches',
    sa.Column('project_id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('niche_id', sa.UUID(as_uuid=False), nullable=False),
    sa.ForeignKeyConstraint(['niche_id'], ['tax_niches.id'], name=op.f('fk_cv_project_niches_niche_id_tax_niches'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['project_id'], ['cv_projects.id'], name=op.f('fk_cv_project_niches_project_id_cv_projects'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('project_id', 'niche_id', name=op.f('pk_cv_project_niches'))
    )
    op.create_table('cv_project_tech_tags',
    sa.Column('project_id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('tech_tag_id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('position', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['project_id'], ['cv_projects.id'], name=op.f('fk_cv_project_tech_tags_project_id_cv_projects'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['tech_tag_id'], ['tax_tech_tags.id'], name=op.f('fk_cv_project_tech_tags_tech_tag_id_tax_tech_tags'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('project_id', 'tech_tag_id', name=op.f('pk_cv_project_tech_tags'))
    )
    op.create_table('cv_publication_niches',
    sa.Column('publication_id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('niche_id', sa.UUID(as_uuid=False), nullable=False),
    sa.ForeignKeyConstraint(['niche_id'], ['tax_niches.id'], name=op.f('fk_cv_publication_niches_niche_id_tax_niches'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['publication_id'], ['cv_publications.id'], name=op.f('fk_cv_publication_niches_publication_id_cv_publications'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('publication_id', 'niche_id', name=op.f('pk_cv_publication_niches'))
    )
    op.create_table('cv_skill_category_niches',
    sa.Column('skill_category_id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('niche_id', sa.UUID(as_uuid=False), nullable=False),
    sa.ForeignKeyConstraint(['niche_id'], ['tax_niches.id'], name=op.f('fk_cv_skill_category_niches_niche_id_tax_niches'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['skill_category_id'], ['cv_skill_categories.id'], name=op.f('fk_cv_skill_category_niches_skill_category_id_cv_skill_categories'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('skill_category_id', 'niche_id', name=op.f('pk_cv_skill_category_niches'))
    )
    op.create_table('cv_skill_category_skills',
    sa.Column('skill_category_id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('skill_id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('position', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['skill_category_id'], ['cv_skill_categories.id'], name=op.f('fk_cv_skill_category_skills_skill_category_id_cv_skill_categories'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['skill_id'], ['cv_skills.id'], name=op.f('fk_cv_skill_category_skills_skill_id_cv_skills'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('skill_category_id', 'skill_id', name=op.f('pk_cv_skill_category_skills'))
    )
    op.create_table('tax_niche_priorities',
    sa.Column('entity_type', sa.Enum('profile', 'experience', 'experience_bullet', 'project', 'project_case_study', 'project_metric', 'skill_category', 'certificate', 'award', 'education', 'endorsement', 'language', 'publication', name='entity_type'), nullable=False),
    sa.Column('entity_id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('niche_id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('priority', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['niche_id'], ['tax_niches.id'], name=op.f('fk_tax_niche_priorities_niche_id_tax_niches'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('entity_type', 'entity_id', 'niche_id', name=op.f('pk_tax_niche_priorities')),
    comment='Priority por (entidad, niche). entity_id polimorfico — integridad via trigger assert_entity_exists.'
    )
    op.create_table('vis_contacts',
    sa.Column('id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('received_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('email', postgresql.CITEXT(), nullable=False),
    sa.Column('message', sa.Text(), nullable=False),
    sa.Column('company', sa.Text(), nullable=True),
    sa.Column('role', sa.Text(), nullable=True),
    sa.Column('service_type', sa.Text(), nullable=True),
    sa.Column('budget', sa.Text(), nullable=True),
    sa.Column('timeline', sa.Text(), nullable=True),
    sa.Column('niche', sa.Text(), nullable=True),
    sa.Column('status', sa.Text(), server_default='new', nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('session_id', sa.Text(), nullable=False),
    sa.CheckConstraint("service_type IS NULL OR service_type IN ('consulting', 'fulltime', 'contract', 'other')", name=op.f('ck_vis_contacts_service_type_valid')),
    sa.CheckConstraint("status IN ('new', 'contacted', 'qualified', 'converted', 'rejected')", name=op.f('ck_vis_contacts_status_valid')),
    sa.ForeignKeyConstraint(['session_id'], ['vis_sessions.session_id'], name=op.f('fk_vis_contacts_session_id_vis_sessions')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_vis_contacts'))
    )
    op.create_index('idx_vis_contacts_created_at', 'vis_contacts', [sa.literal_column('created_at DESC')], unique=False)
    op.create_index('idx_vis_contacts_email', 'vis_contacts', ['email'], unique=False)
    op.create_index('idx_vis_contacts_message_fts', 'vis_contacts', [sa.literal_column("to_tsvector('spanish', message)")], unique=False, postgresql_using='gin')
    op.create_index('idx_vis_contacts_niche_created', 'vis_contacts', ['niche', sa.literal_column('created_at DESC')], unique=False)
    op.create_index('idx_vis_contacts_session_id', 'vis_contacts', ['session_id'], unique=False)
    op.create_index('idx_vis_contacts_status', 'vis_contacts', ['status'], unique=False, postgresql_where=sa.text("status IN ('new', 'contacted')"))
    op.create_table('vis_session_visits',
    sa.Column('visit_id', sa.UUID(as_uuid=False), server_default=sa.text('uuidv7()'), nullable=False),
    sa.Column('session_id', sa.Text(), nullable=False),
    sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('ended_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('event_count', sa.Integer(), server_default=sa.text('0'), nullable=False),
    sa.Column('ip', postgresql.INET(), nullable=True),
    sa.Column('country', sa.CHAR(length=2), nullable=True),
    sa.Column('utm_source', sa.Text(), nullable=True),
    sa.Column('utm_medium', sa.Text(), nullable=True),
    sa.Column('utm_campaign', sa.Text(), nullable=True),
    sa.Column('utm_content', sa.Text(), nullable=True),
    sa.Column('utm_term', sa.Text(), nullable=True),
    sa.Column('referrer', sa.Text(), nullable=True),
    sa.Column('landing_page_path', sa.Text(), nullable=True),
    sa.Column('niche', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['session_id'], ['vis_sessions.session_id'], name=op.f('fk_vis_session_visits_session_id_vis_sessions')),
    sa.PrimaryKeyConstraint('visit_id', name=op.f('pk_vis_session_visits'))
    )
    op.create_index('idx_vis_visits_country', 'vis_session_visits', ['country'], unique=False, postgresql_where=sa.text('country IS NOT NULL'))
    op.create_index('idx_vis_visits_niche', 'vis_session_visits', ['niche'], unique=False, postgresql_where=sa.text('niche IS NOT NULL'))
    op.create_index('idx_vis_visits_session_started', 'vis_session_visits', ['session_id', sa.literal_column('started_at DESC')], unique=False)
    op.create_index('idx_vis_visits_started_brin', 'vis_session_visits', ['started_at'], unique=False, postgresql_using='brin')
    op.create_index('idx_vis_visits_utm_source', 'vis_session_visits', ['utm_source'], unique=False, postgresql_where=sa.text('utm_source IS NOT NULL'))
    op.create_table('vis_tracking_events',
    sa.Column('session_id', sa.Text(), nullable=False),
    sa.Column('visit_id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('page_id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('received_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('page_path', sa.Text(), nullable=True),
    sa.Column('viewport_width', sa.Integer(), nullable=True),
    sa.Column('viewport_height', sa.Integer(), nullable=True),
    sa.Column('niche', sa.Text(), nullable=True),
    sa.Column('event_id', sa.UUID(as_uuid=False), nullable=True),
    sa.Column('event_type_id', sa.UUID(as_uuid=False), nullable=True),
    sa.Column('event_props', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.ForeignKeyConstraint(['event_type_id'], ['tax_event_types.id'], name=op.f('fk_vis_tracking_events_event_type_id_tax_event_types')),
    sa.ForeignKeyConstraint(['session_id'], ['vis_sessions.session_id'], name=op.f('fk_vis_tracking_events_session_id_vis_sessions')),
    sa.ForeignKeyConstraint(['visit_id'], ['vis_session_visits.visit_id'], name=op.f('fk_vis_tracking_events_visit_id_vis_session_visits')),
    sa.PrimaryKeyConstraint('created_at', 'visit_id', 'page_id', name='pk_vis_tracking_events'),
    postgresql_partition_by='RANGE (created_at)'
    )
    op.create_index('idx_vis_tracking_created_brin', 'vis_tracking_events', ['created_at'], unique=False, postgresql_using='brin')
    op.create_index('idx_vis_tracking_event_type', 'vis_tracking_events', ['event_type_id'], unique=False)
    op.create_index('idx_vis_tracking_niche_created', 'vis_tracking_events', ['niche', sa.literal_column('created_at DESC')], unique=False, postgresql_where=sa.text('niche IS NOT NULL'))
    op.create_index('idx_vis_tracking_page_path', 'vis_tracking_events', ['page_path'], unique=False)
    op.create_index('idx_vis_tracking_session_created', 'vis_tracking_events', ['session_id', 'created_at'], unique=False)
    op.create_index('idx_vis_tracking_visit_id', 'vis_tracking_events', ['visit_id'], unique=False)

    # Particion default fisica para vis_tracking_events. Sin ella, un
    # INSERT cuya created_at no cae en ninguna particion explicita falla.
    op.execute(create_partition_default())

    # Trigger PL/pgSQL de integridad polimorfica (entity_id en
    # i18n_translations y tax_niche_priorities NO tiene FK fisica).
    op.execute(entity_trigger_fn_sql)
    for tbl in entity_trigger_tables:
        op.execute(
            f'CREATE TRIGGER {tbl}_assert_entity '
            f'BEFORE INSERT OR UPDATE ON {tbl} '
            f'FOR EACH ROW EXECUTE FUNCTION assert_entity_exists()'
        )

    # Seed inicial de tax_event_types (16 tipos fijos con UUIDv7 literales
    # que el frontend replica como constantes TS en build-time).
    # Cast explicito ::uuid porque psycopg manda el id como varchar.
    for et in event_types_seed:
        op.execute(
            sa.text(
                'INSERT INTO tax_event_types (id, code_name, description) '
                'VALUES (CAST(:id AS uuid), :code_name, :description) '
                'ON CONFLICT (code_name) DO NOTHING'
            ).bindparams(**et)
        )


def downgrade() -> None:
    # Drop triggers + function polimorfica antes de las tablas
    # (CASCADE no aplica a triggers).
    for tbl in entity_trigger_tables:
        op.execute(f'DROP TRIGGER IF EXISTS {tbl}_assert_entity ON {tbl}')
    op.execute('DROP FUNCTION IF EXISTS assert_entity_exists()')

    # Drop particion default antes que la tabla padre.
    op.execute('DROP TABLE IF EXISTS vis_tracking_events_default')

    op.drop_index('idx_vis_tracking_visit_id', table_name='vis_tracking_events')
    op.drop_index('idx_vis_tracking_session_created', table_name='vis_tracking_events')
    op.drop_index('idx_vis_tracking_page_path', table_name='vis_tracking_events')
    op.drop_index('idx_vis_tracking_niche_created', table_name='vis_tracking_events', postgresql_where=sa.text('niche IS NOT NULL'))
    op.drop_index('idx_vis_tracking_event_type', table_name='vis_tracking_events')
    op.drop_index('idx_vis_tracking_created_brin', table_name='vis_tracking_events', postgresql_using='brin')
    op.drop_table('vis_tracking_events')
    op.drop_index('idx_vis_visits_utm_source', table_name='vis_session_visits', postgresql_where=sa.text('utm_source IS NOT NULL'))
    op.drop_index('idx_vis_visits_started_brin', table_name='vis_session_visits', postgresql_using='brin')
    op.drop_index('idx_vis_visits_session_started', table_name='vis_session_visits')
    op.drop_index('idx_vis_visits_niche', table_name='vis_session_visits', postgresql_where=sa.text('niche IS NOT NULL'))
    op.drop_index('idx_vis_visits_country', table_name='vis_session_visits', postgresql_where=sa.text('country IS NOT NULL'))
    op.drop_table('vis_session_visits')
    op.drop_index('idx_vis_contacts_status', table_name='vis_contacts', postgresql_where=sa.text("status IN ('new', 'contacted')"))
    op.drop_index('idx_vis_contacts_session_id', table_name='vis_contacts')
    op.drop_index('idx_vis_contacts_niche_created', table_name='vis_contacts')
    op.drop_index('idx_vis_contacts_message_fts', table_name='vis_contacts', postgresql_using='gin')
    op.drop_index('idx_vis_contacts_email', table_name='vis_contacts')
    op.drop_index('idx_vis_contacts_created_at', table_name='vis_contacts')
    op.drop_table('vis_contacts')
    op.drop_table('tax_niche_priorities')
    op.drop_table('cv_skill_category_skills')
    op.drop_table('cv_skill_category_niches')
    op.drop_table('cv_publication_niches')
    op.drop_table('cv_project_tech_tags')
    op.drop_table('cv_project_niches')
    op.drop_table('cv_project_metrics')
    op.drop_table('cv_project_case_studies')
    op.drop_table('cv_profile_stats')
    op.drop_table('cv_profile_niches')
    op.drop_table('cv_language_niches')
    op.drop_table('cv_experience_skills')
    op.drop_table('cv_experience_niches')
    op.drop_table('cv_experience_bullets')
    op.drop_table('cv_endorsement_niches')
    op.drop_table('cv_education_entry_niches')
    op.drop_table('cv_certificate_niches')
    op.drop_table('cv_award_niches')
    op.drop_index('idx_vis_sessions_last_seen', table_name='vis_sessions')
    op.drop_index('idx_vis_sessions_first_seen_brin', table_name='vis_sessions', postgresql_using='brin')
    op.drop_table('vis_sessions')
    op.drop_table('tax_tech_tags')
    op.drop_table('tax_niches')
    op.drop_table('tax_event_types')
    op.drop_table('i18n_translations')
    op.drop_table('cv_skills')
    op.drop_table('cv_skill_categories')
    op.drop_table('cv_publications')
    op.drop_table('cv_projects')
    op.drop_table('cv_profiles')
    op.drop_table('cv_languages')
    op.drop_table('cv_experiences')
    op.drop_table('cv_endorsements')
    op.drop_table('cv_education_entries')
    op.drop_table('cv_certificates')
    op.drop_table('cv_awards')

    # Drop ENUMs nativos PG (Alembic NO los dropea automaticamente
    # cuando las tablas que los usan se borran).
    for enum_name in enum_type_names:
        op.execute(f'DROP TYPE IF EXISTS {enum_name}')

    # Drop extensions opcional — solo si no las usa otro schema.
    op.execute('DROP EXTENSION IF EXISTS unaccent')
    op.execute('DROP EXTENSION IF EXISTS citext')
