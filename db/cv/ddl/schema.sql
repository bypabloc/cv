-- ===========================================================================
-- Schema relacional del CV — DDL de referencia (PostgreSQL 18)
-- ===========================================================================
-- GENERADO por db/cv/ddl/generate_schema_sql.py — NO editar a mano.
-- La fuente de verdad del schema son las migraciones Alembic
-- (db/cv/alembic/versions/). Este archivo es solo documentacion legible.
-- ===========================================================================

SET search_path TO public;

-- Tipos ENUM nativos.
CREATE TYPE locale AS ENUM ('es', 'en');
CREATE TYPE seniority AS ENUM ('intern', 'junior', 'mid', 'senior', 'lead');
CREATE TYPE project_type AS ENUM ('web', 'mobile', 'cli', 'library', 'ai', 'fintech-platform');
CREATE TYPE project_status AS ENUM ('active', 'inactive', 'concept');
CREATE TYPE skill_kind AS ENUM ('technical', 'soft');
CREATE TYPE bullet_kind AS ENUM ('responsibility', 'achievement');
CREATE TYPE entity_type AS ENUM ('profile', 'experience', 'experience_bullet', 'project', 'project_case_study', 'project_metric', 'skill_category', 'certificate', 'award', 'education', 'reference', 'language', 'publication');

-- Tablas.
CREATE TABLE awards (
	slug VARCHAR(120) NOT NULL, 
	issuer VARCHAR(200) NOT NULL, 
	awarded_ym VARCHAR(7) NOT NULL, 
	url VARCHAR(500), 
	id UUID DEFAULT uuidv7() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_awards PRIMARY KEY (id), 
	CONSTRAINT ck_awards_awarded_ym_format CHECK (awarded_ym ~ '^\d{4}-(0[1-9]|1[0-2])$'), 
	CONSTRAINT uq_awards_slug UNIQUE (slug)
);

CREATE TABLE certificates (
	slug VARCHAR(120) NOT NULL, 
	title VARCHAR(300) NOT NULL, 
	issuer VARCHAR(200) NOT NULL, 
	issued_on DATE NOT NULL, 
	url VARCHAR(500) NOT NULL, 
	id UUID DEFAULT uuidv7() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_certificates PRIMARY KEY (id), 
	CONSTRAINT uq_certificates_slug UNIQUE (slug)
);

CREATE TABLE education (
	slug VARCHAR(120) NOT NULL, 
	institution VARCHAR(200) NOT NULL, 
	start_year VARCHAR(16) NOT NULL, 
	end_year VARCHAR(16) NOT NULL, 
	url VARCHAR(500), 
	id UUID DEFAULT uuidv7() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_education PRIMARY KEY (id), 
	CONSTRAINT uq_education_slug UNIQUE (slug)
);

CREATE TABLE experiences (
	slug VARCHAR(120) NOT NULL, 
	company VARCHAR(160) NOT NULL, 
	company_url VARCHAR(500), 
	start_ym VARCHAR(7) NOT NULL, 
	end_ym VARCHAR(7), 
	seniority seniority NOT NULL, 
	id UUID DEFAULT uuidv7() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_experiences PRIMARY KEY (id), 
	CONSTRAINT ck_experiences_start_ym_format CHECK (start_ym ~ '^\d{4}-(0[1-9]|1[0-2])$'), 
	CONSTRAINT ck_experiences_end_ym_format CHECK (end_ym IS NULL OR end_ym ~ '^\d{4}-(0[1-9]|1[0-2])$'), 
	CONSTRAINT uq_experiences_slug UNIQUE (slug)
);

CREATE TABLE languages (
	slug VARCHAR(120) NOT NULL, 
	id UUID DEFAULT uuidv7() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_languages PRIMARY KEY (id), 
	CONSTRAINT uq_languages_slug UNIQUE (slug)
);

CREATE TABLE niches (
	slug VARCHAR(32) NOT NULL, 
	position INTEGER NOT NULL, 
	id UUID DEFAULT uuidv7() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_niches PRIMARY KEY (id), 
	CONSTRAINT uq_niches_slug UNIQUE (slug)
);

CREATE TABLE profile (
	name VARCHAR(160) NOT NULL, 
	handle VARCHAR(80) NOT NULL, 
	location VARCHAR(160) NOT NULL, 
	email VARCHAR(254) NOT NULL, 
	phone VARCHAR(40), 
	linkedin_url VARCHAR(500) NOT NULL, 
	github_url VARCHAR(500) NOT NULL, 
	website_url VARCHAR(500), 
	avatar_url VARCHAR(500) NOT NULL, 
	id UUID DEFAULT uuidv7() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_profile PRIMARY KEY (id), 
	CONSTRAINT uq_profile_handle UNIQUE (handle)
);

CREATE TABLE projects (
	slug VARCHAR(120) NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	url VARCHAR(500), 
	repo VARCHAR(500), 
	status project_status NOT NULL, 
	project_type project_type NOT NULL, 
	is_confidential BOOLEAN NOT NULL, 
	id UUID DEFAULT uuidv7() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_projects PRIMARY KEY (id), 
	CONSTRAINT uq_projects_slug UNIQUE (slug)
);

CREATE TABLE publications (
	slug VARCHAR(120) NOT NULL, 
	title VARCHAR(300) NOT NULL, 
	platform VARCHAR(120) NOT NULL, 
	url VARCHAR(500) NOT NULL, 
	canonical_url VARCHAR(500), 
	published_on DATE NOT NULL, 
	id UUID DEFAULT uuidv7() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_publications PRIMARY KEY (id), 
	CONSTRAINT uq_publications_slug UNIQUE (slug)
);

CREATE TABLE "references" (
	slug VARCHAR(120) NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	role VARCHAR(200) NOT NULL, 
	company VARCHAR(200), 
	linkedin_url VARCHAR(500) NOT NULL, 
	id UUID DEFAULT uuidv7() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_references PRIMARY KEY (id), 
	CONSTRAINT uq_references_slug UNIQUE (slug)
);

CREATE TABLE skill_categories (
	slug VARCHAR(120) NOT NULL, 
	kind skill_kind NOT NULL, 
	id UUID DEFAULT uuidv7() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_skill_categories PRIMARY KEY (id), 
	CONSTRAINT uq_skill_categories_slug UNIQUE (slug)
);

CREATE TABLE skills (
	name VARCHAR(120) NOT NULL, 
	id UUID DEFAULT uuidv7() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_skills PRIMARY KEY (id), 
	CONSTRAINT uq_skills_name UNIQUE (name)
);

CREATE TABLE tech_tags (
	name VARCHAR(120) NOT NULL, 
	id UUID DEFAULT uuidv7() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_tech_tags PRIMARY KEY (id), 
	CONSTRAINT uq_tech_tags_name UNIQUE (name)
);

CREATE TABLE translations (
	entity_type entity_type NOT NULL, 
	entity_id UUID NOT NULL, 
	field VARCHAR(64) NOT NULL, 
	locale locale NOT NULL, 
	value TEXT NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_translations PRIMARY KEY (entity_type, entity_id, field, locale)
);

CREATE TABLE award_niches (
	award_id UUID NOT NULL, 
	niche_id UUID NOT NULL, 
	CONSTRAINT pk_award_niches PRIMARY KEY (award_id, niche_id), 
	CONSTRAINT fk_award_niches_award_id_awards FOREIGN KEY(award_id) REFERENCES awards (id) ON DELETE CASCADE, 
	CONSTRAINT fk_award_niches_niche_id_niches FOREIGN KEY(niche_id) REFERENCES niches (id) ON DELETE CASCADE
);

CREATE TABLE certificate_niches (
	certificate_id UUID NOT NULL, 
	niche_id UUID NOT NULL, 
	CONSTRAINT pk_certificate_niches PRIMARY KEY (certificate_id, niche_id), 
	CONSTRAINT fk_certificate_niches_certificate_id_certificates FOREIGN KEY(certificate_id) REFERENCES certificates (id) ON DELETE CASCADE, 
	CONSTRAINT fk_certificate_niches_niche_id_niches FOREIGN KEY(niche_id) REFERENCES niches (id) ON DELETE CASCADE
);

CREATE TABLE education_niches (
	education_id UUID NOT NULL, 
	niche_id UUID NOT NULL, 
	CONSTRAINT pk_education_niches PRIMARY KEY (education_id, niche_id), 
	CONSTRAINT fk_education_niches_education_id_education FOREIGN KEY(education_id) REFERENCES education (id) ON DELETE CASCADE, 
	CONSTRAINT fk_education_niches_niche_id_niches FOREIGN KEY(niche_id) REFERENCES niches (id) ON DELETE CASCADE
);

CREATE TABLE experience_bullets (
	experience_id UUID NOT NULL, 
	kind bullet_kind NOT NULL, 
	position INTEGER NOT NULL, 
	id UUID DEFAULT uuidv7() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_experience_bullets PRIMARY KEY (id), 
	CONSTRAINT experience_bullet UNIQUE (experience_id, kind, position), 
	CONSTRAINT fk_experience_bullets_experience_id_experiences FOREIGN KEY(experience_id) REFERENCES experiences (id) ON DELETE CASCADE
);

CREATE TABLE experience_niches (
	experience_id UUID NOT NULL, 
	niche_id UUID NOT NULL, 
	CONSTRAINT pk_experience_niches PRIMARY KEY (experience_id, niche_id), 
	CONSTRAINT fk_experience_niches_experience_id_experiences FOREIGN KEY(experience_id) REFERENCES experiences (id) ON DELETE CASCADE, 
	CONSTRAINT fk_experience_niches_niche_id_niches FOREIGN KEY(niche_id) REFERENCES niches (id) ON DELETE CASCADE
);

CREATE TABLE experience_skills (
	experience_id UUID NOT NULL, 
	skill_id UUID NOT NULL, 
	kind skill_kind NOT NULL, 
	CONSTRAINT pk_experience_skills PRIMARY KEY (experience_id, skill_id, kind), 
	CONSTRAINT fk_experience_skills_experience_id_experiences FOREIGN KEY(experience_id) REFERENCES experiences (id) ON DELETE CASCADE, 
	CONSTRAINT fk_experience_skills_skill_id_skills FOREIGN KEY(skill_id) REFERENCES skills (id) ON DELETE CASCADE
);

CREATE TABLE language_niches (
	language_id UUID NOT NULL, 
	niche_id UUID NOT NULL, 
	CONSTRAINT pk_language_niches PRIMARY KEY (language_id, niche_id), 
	CONSTRAINT fk_language_niches_language_id_languages FOREIGN KEY(language_id) REFERENCES languages (id) ON DELETE CASCADE, 
	CONSTRAINT fk_language_niches_niche_id_niches FOREIGN KEY(niche_id) REFERENCES niches (id) ON DELETE CASCADE
);

CREATE TABLE niche_priorities (
	entity_type entity_type NOT NULL, 
	entity_id UUID NOT NULL, 
	niche_id UUID NOT NULL, 
	priority INTEGER NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_niche_priorities PRIMARY KEY (entity_type, entity_id, niche_id), 
	CONSTRAINT fk_niche_priorities_niche_id_niches FOREIGN KEY(niche_id) REFERENCES niches (id) ON DELETE CASCADE
);

CREATE TABLE profile_stats (
	profile_id UUID NOT NULL, 
	years_experience INTEGER NOT NULL, 
	companies INTEGER NOT NULL, 
	countries INTEGER NOT NULL, 
	certifications INTEGER NOT NULL, 
	id UUID DEFAULT uuidv7() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_profile_stats PRIMARY KEY (id), 
	CONSTRAINT uq_profile_stats_profile_id UNIQUE (profile_id), 
	CONSTRAINT fk_profile_stats_profile_id_profile FOREIGN KEY(profile_id) REFERENCES profile (id) ON DELETE CASCADE
);

CREATE TABLE project_case_studies (
	project_id UUID NOT NULL, 
	id UUID DEFAULT uuidv7() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_project_case_studies PRIMARY KEY (id), 
	CONSTRAINT uq_project_case_studies_project_id UNIQUE (project_id), 
	CONSTRAINT fk_project_case_studies_project_id_projects FOREIGN KEY(project_id) REFERENCES projects (id) ON DELETE CASCADE
);

CREATE TABLE project_metrics (
	project_id UUID NOT NULL, 
	metric_key VARCHAR(80) NOT NULL, 
	metric_value VARCHAR(500) NOT NULL, 
	position INTEGER NOT NULL, 
	id UUID DEFAULT uuidv7() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_project_metrics PRIMARY KEY (id), 
	CONSTRAINT project_metric UNIQUE (project_id, metric_key), 
	CONSTRAINT fk_project_metrics_project_id_projects FOREIGN KEY(project_id) REFERENCES projects (id) ON DELETE CASCADE
);

CREATE TABLE project_niches (
	project_id UUID NOT NULL, 
	niche_id UUID NOT NULL, 
	CONSTRAINT pk_project_niches PRIMARY KEY (project_id, niche_id), 
	CONSTRAINT fk_project_niches_project_id_projects FOREIGN KEY(project_id) REFERENCES projects (id) ON DELETE CASCADE, 
	CONSTRAINT fk_project_niches_niche_id_niches FOREIGN KEY(niche_id) REFERENCES niches (id) ON DELETE CASCADE
);

CREATE TABLE project_tech_tags (
	project_id UUID NOT NULL, 
	tech_tag_id UUID NOT NULL, 
	position INTEGER NOT NULL, 
	CONSTRAINT pk_project_tech_tags PRIMARY KEY (project_id, tech_tag_id), 
	CONSTRAINT fk_project_tech_tags_project_id_projects FOREIGN KEY(project_id) REFERENCES projects (id) ON DELETE CASCADE, 
	CONSTRAINT fk_project_tech_tags_tech_tag_id_tech_tags FOREIGN KEY(tech_tag_id) REFERENCES tech_tags (id) ON DELETE CASCADE
);

CREATE TABLE publication_niches (
	publication_id UUID NOT NULL, 
	niche_id UUID NOT NULL, 
	CONSTRAINT pk_publication_niches PRIMARY KEY (publication_id, niche_id), 
	CONSTRAINT fk_publication_niches_publication_id_publications FOREIGN KEY(publication_id) REFERENCES publications (id) ON DELETE CASCADE, 
	CONSTRAINT fk_publication_niches_niche_id_niches FOREIGN KEY(niche_id) REFERENCES niches (id) ON DELETE CASCADE
);

CREATE TABLE reference_niches (
	reference_id UUID NOT NULL, 
	niche_id UUID NOT NULL, 
	CONSTRAINT pk_reference_niches PRIMARY KEY (reference_id, niche_id), 
	CONSTRAINT fk_reference_niches_reference_id_references FOREIGN KEY(reference_id) REFERENCES "references" (id) ON DELETE CASCADE, 
	CONSTRAINT fk_reference_niches_niche_id_niches FOREIGN KEY(niche_id) REFERENCES niches (id) ON DELETE CASCADE
);

CREATE TABLE skill_category_niches (
	skill_category_id UUID NOT NULL, 
	niche_id UUID NOT NULL, 
	CONSTRAINT pk_skill_category_niches PRIMARY KEY (skill_category_id, niche_id), 
	CONSTRAINT fk_skill_category_niches_skill_category_id_skill_categories FOREIGN KEY(skill_category_id) REFERENCES skill_categories (id) ON DELETE CASCADE, 
	CONSTRAINT fk_skill_category_niches_niche_id_niches FOREIGN KEY(niche_id) REFERENCES niches (id) ON DELETE CASCADE
);

CREATE TABLE skill_category_skills (
	skill_category_id UUID NOT NULL, 
	skill_id UUID NOT NULL, 
	position INTEGER NOT NULL, 
	CONSTRAINT pk_skill_category_skills PRIMARY KEY (skill_category_id, skill_id), 
	CONSTRAINT fk_skill_category_skills_skill_category_id_skill_categories FOREIGN KEY(skill_category_id) REFERENCES skill_categories (id) ON DELETE CASCADE, 
	CONSTRAINT fk_skill_category_skills_skill_id_skills FOREIGN KEY(skill_id) REFERENCES skills (id) ON DELETE CASCADE
);


-- ---------------------------------------------------------------------------
-- Integridad polimorfica de translations / niche_priorities.
-- `entity_id` apunta a tablas distintas segun `entity_type`, asi que no
-- puede tener una FK real — este trigger la valida en cada INSERT/UPDATE.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION assert_entity_exists()
RETURNS TRIGGER AS $$
DECLARE
    target_table text;
    found boolean;
BEGIN
    target_table := CASE NEW.entity_type
        WHEN 'profile'            THEN 'profile'
        WHEN 'experience'         THEN 'experiences'
        WHEN 'experience_bullet'  THEN 'experience_bullets'
        WHEN 'project'            THEN 'projects'
        WHEN 'project_case_study' THEN 'project_case_studies'
        WHEN 'project_metric'     THEN 'project_metrics'
        WHEN 'skill_category'     THEN 'skill_categories'
        WHEN 'certificate'        THEN 'certificates'
        WHEN 'award'              THEN 'awards'
        WHEN 'education'          THEN 'education'
        WHEN 'reference'          THEN 'references'
        WHEN 'language'           THEN 'languages'
        WHEN 'publication'        THEN 'publications'
    END;
    IF target_table IS NULL THEN
        RAISE EXCEPTION
            'assert_entity_exists: entity_type % no mapeado', NEW.entity_type;
    END IF;
    EXECUTE format(
        'SELECT EXISTS (SELECT 1 FROM %I WHERE id = $1)', target_table
    ) INTO found USING NEW.entity_id;
    IF NOT found THEN
        RAISE EXCEPTION
            'assert_entity_exists: % % no existe en %',
            NEW.entity_type, NEW.entity_id, target_table;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_translations_entity_exists
    BEFORE INSERT OR UPDATE ON translations
    FOR EACH ROW EXECUTE FUNCTION assert_entity_exists();

CREATE TRIGGER trg_niche_priorities_entity_exists
    BEFORE INSERT OR UPDATE ON niche_priorities
    FOR EACH ROW EXECUTE FUNCTION assert_entity_exists();

