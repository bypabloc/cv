/**
 * @module features/cv-management/types
 * @description Tipos espejo del contrato del Lambda `cv_admin` (operations
 *   `content` + `publish`) y del shape de lectura del GET /cv publico. Las
 *   claves son camelCase (los alias Pydantic del backend: `companyUrl`,
 *   `skillsTechnical`, `metricsEstimated`, ...). Ver
 *   serverless/lambda/services/cv_admin/core/models/.
 */

/** Bloque bilingue `{es, en}` — el backend exige al menos un locale. */
export type BiLang = Partial<Record<"es" | "en", string>>;

/** Listas paralelas es/en (bullets de experiencia). */
export type BiLangList = Partial<Record<"es" | "en", string[]>>;

/** Mapa de prioridades por niche: `{<niche-slug>: <peso>}`. */
export type PriorityMap = Record<string, number>;

/** Las 10 secciones del CV en el admin (mismas rutas /cv/<seccion>). */
export type CvSection =
	| "profile"
	| "experiences"
	| "projects"
	| "education"
	| "certificates"
	| "awards"
	| "languages"
	| "endorsements"
	| "publications"
	| "skills";

/** Secciones con lista de entidades (todas menos el singleton profile). */
export type CvEntitySectionKind = Exclude<CvSection, "profile">;

/** entity_type del payload `reorder` (espejo de ReorderEntityType). */
export type ReorderEntityType =
	| "experience"
	| "project"
	| "skill_category"
	| "certificate"
	| "award"
	| "education"
	| "language"
	| "endorsement"
	| "publication";

export type Seniority = "intern" | "junior" | "mid" | "senior" | "lead";
export type ProjectStatus = "active" | "inactive" | "concept";
export type ProjectType =
	| "web"
	| "mobile"
	| "cli"
	| "library"
	| "ai"
	| "fintech-platform";
export type SkillKind = "technical" | "soft";

export interface ProfileContacts {
	email: string;
	phone?: string;
	linkedin: string;
	github: string;
	website?: string;
}

export interface ProfileStats {
	yearsExperience: number;
	companies: number;
	countries: number;
	certifications: number;
}

export interface CvProfile {
	name: string;
	handle: string;
	headline: BiLang;
	summary: BiLang;
	location: string;
	availability?: BiLang;
	contacts: ProfileContacts;
	avatarUrl: string;
	niches: string[];
	stats?: ProfileStats;
}

export interface CvExperience {
	slug: string;
	role: BiLang;
	company: string;
	country: string;
	companyUrl?: string;
	start: string;
	end?: string;
	seniority: Seniority;
	summary?: BiLang;
	metricsEstimated?: boolean;
	responsibilities?: BiLangList;
	achievements?: BiLangList;
	skillsTechnical: string[];
	skillsSoft: string[];
	niches: string[];
	priority: PriorityMap;
}

export interface CvProjectLink {
	label: string;
	url: string;
}

export interface CaseStudyDetailed {
	problem?: BiLang;
	process?: BiLang;
	result?: BiLang;
}

export interface CvProject {
	slug: string;
	name: string;
	summary: BiLang;
	description?: BiLang;
	url?: string;
	links?: CvProjectLink[];
	repo?: string;
	status: ProjectStatus;
	projectType: ProjectType;
	isConfidential?: boolean;
	metricsEstimated?: boolean;
	stack: string[];
	caseStudy?: BiLang;
	caseStudyDetailed?: CaseStudyDetailed;
	/** Mapa key/value ORDENADO (el orden de insercion es el de presentacion). */
	metrics: Record<string, string | number>;
	niches: string[];
	priority: PriorityMap;
}

export interface CvEducation {
	slug: string;
	institution: string;
	start: string;
	end?: string;
	url?: string;
	degree?: BiLang;
	description: BiLang;
	niches?: string[];
	priority?: PriorityMap;
}

export interface CvCertificate {
	slug: string;
	title: string;
	issuer: string;
	date: string;
	url: string;
	niches?: string[];
	priority?: PriorityMap;
}

export interface CvAward {
	slug: string;
	title: BiLang;
	issuer: string;
	date: string;
	url?: string;
	motivation: BiLang;
	niches?: string[];
	priority?: PriorityMap;
}

export interface CvLanguage {
	slug: string;
	name: BiLang;
	level: BiLang;
	niches?: string[];
	priority?: PriorityMap;
}

export interface CvEndorsement {
	slug: string;
	name: string;
	role: string;
	relation: BiLang;
	company?: string;
	linkedin: string;
	niches?: string[];
	priority?: PriorityMap;
}

export interface CvPublication {
	slug: string;
	title: string;
	platform: string;
	url: string;
	canonical?: string;
	date: string;
	summary: BiLang;
	niches?: string[];
	priority?: PriorityMap;
}

export interface CvSkillCategory {
	slug: string;
	name: BiLang;
	kind: SkillKind;
	skills: string[];
	niches: string[];
	priority?: PriorityMap;
}

/** Union de los records que renderizan las listas por seccion. */
export type CvEntityRecord =
	| CvExperience
	| CvProject
	| CvEducation
	| CvCertificate
	| CvAward
	| CvLanguage
	| CvEndorsement
	| CvPublication
	| CvSkillCategory;

/** Union de los payloads de upsert (operation content). */
export type CvUpsertPayload =
	| CvProfile
	| CvExperience
	| CvProject
	| CvEducation
	| CvCertificate
	| CvAward
	| CvLanguage
	| CvEndorsement
	| CvPublication
	| CvSkillCategory;

export interface DeletePayload {
	slug: string;
}

export interface ReorderPayload {
	entity_type: ReorderEntityType;
	niche: string;
	ordered_slugs: string[];
}

export interface CatalogEntry {
	slug: string;
	name: string;
}

/** Respuesta de content.catalogs (vocabularios para los selects). */
export interface CvCatalogs {
	niches: string[];
	skills: CatalogEntry[];
	techTags: CatalogEntry[];
}

/** Respuesta de los upsert-*: clave natural + id interno. */
export interface UpsertResponse {
	entity: string;
	id: string;
}

/** Respuesta de los delete-*. */
export interface DeleteResponse {
	entity: string;
	deleted: boolean;
}

/** Respuesta de content.reorder. */
export interface ReorderResponse {
	entity_type: ReorderEntityType;
	niche: string;
	reordered: number;
}

/** Respuesta de publish.dispatch. */
export interface PublishDispatchResponse {
	dispatched: boolean;
	ref: string;
	actions_url: string;
}

/** Respuesta de publish.status (`status: 'none'` cuando no hay runs). */
export interface PublishStatusResponse {
	status: string;
	ref: string;
	conclusion?: string | null;
	url?: string;
	created_at?: string;
}
