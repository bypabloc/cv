import type {
	BiLang,
	CvEntityRecord,
	CvSection,
	ReorderEntityType,
} from "../types";

/**
 * @module features/cv-management/lib/sections
 * @description Configuracion por seccion del CV: label del sub-nav, action de
 *   lectura del GET /cv publico (null = sin endpoint de lectura, ej.
 *   publications), entity_type del reorder y helpers de presentacion
 *   (toListItem, countEntries) que normalizan cada record al shape que
 *   renderiza la lista de cards.
 */

export const CV_SECTIONS = [
	"profile",
	"experiences",
	"projects",
	"education",
	"certificates",
	"awards",
	"languages",
	"endorsements",
	"publications",
	"skills",
] as const satisfies readonly CvSection[];

interface SectionConfig {
	label: string;
	/** Action del GET /cv publico; null = la seccion no tiene lectura. */
	readAction: string | null;
	/** entity_type del payload reorder; null = singleton (profile). */
	entityType: ReorderEntityType | null;
}

export const SECTION_CONFIG: Record<CvSection, SectionConfig> = {
	profile: { label: "Perfil", readAction: "profile", entityType: null },
	experiences: {
		label: "Experiencias",
		readAction: "experiences",
		entityType: "experience",
	},
	projects: {
		label: "Proyectos",
		readAction: "projects",
		entityType: "project",
	},
	education: {
		label: "Educacion",
		readAction: "education",
		entityType: "education",
	},
	certificates: {
		label: "Certificados",
		readAction: "certificates",
		entityType: "certificate",
	},
	awards: { label: "Premios", readAction: "awards", entityType: "award" },
	languages: {
		label: "Idiomas",
		readAction: "languages",
		entityType: "language",
	},
	// El read action publico se llama `references` (nombre legacy del
	// endpoint); la escritura usa upsert/delete-endorsement.
	endorsements: {
		label: "Referencias",
		readAction: "references",
		entityType: "endorsement",
	},
	// El GET /cv NO expone publications (sin lectura publica todavia): la
	// lista del admin queda vacia hasta que el backend agregue la action.
	publications: {
		label: "Publicaciones",
		readAction: null,
		entityType: "publication",
	},
	skills: {
		label: "Skills",
		readAction: "skills",
		entityType: "skill_category",
	},
};

/** Item normalizado que renderiza cada card de la lista de una seccion. */
export interface SectionListItem {
	slug: string;
	title: string;
	subtitle: string;
	niches: string[];
}

function biLangText(value: BiLang | undefined): string {
	return value?.es ?? value?.en ?? "";
}

type RawRecord = CvEntityRecord & Record<string, unknown>;

function titleOf(section: CvSection, raw: RawRecord): string {
	if (section === "experiences" || section === "languages") {
		const labeled = raw as { role?: BiLang; name?: BiLang };
		return (
			biLangText(section === "experiences" ? labeled.role : labeled.name) ||
			raw.slug
		);
	}
	if (section === "awards" || section === "skills") {
		const labeled = raw as { title?: BiLang; name?: BiLang };
		return (
			biLangText(section === "awards" ? labeled.title : labeled.name) ||
			raw.slug
		);
	}
	const flat = raw as { name?: string; title?: string; institution?: string };
	return flat.name ?? flat.title ?? flat.institution ?? raw.slug;
}

function subtitleOf(section: CvSection, raw: RawRecord): string {
	switch (section) {
		case "experiences": {
			const exp = raw as { company?: string; start?: string; end?: string };
			return `${exp.company ?? ""} · ${exp.start ?? ""} — ${exp.end ?? "Presente"}`;
		}
		case "projects": {
			const proj = raw as { status?: string; projectType?: string };
			return [proj.projectType, proj.status].filter(Boolean).join(" · ");
		}
		case "education": {
			const edu = raw as { degree?: BiLang; start?: string; end?: string };
			return [biLangText(edu.degree), edu.start].filter(Boolean).join(" · ");
		}
		case "certificates":
		case "awards": {
			const issued = raw as { issuer?: string; date?: string };
			return [issued.issuer, issued.date].filter(Boolean).join(" · ");
		}
		case "languages":
			return biLangText((raw as { level?: BiLang }).level);
		case "endorsements": {
			const ref = raw as { role?: string; company?: string };
			return [ref.role, ref.company].filter(Boolean).join(" · ");
		}
		case "publications": {
			const pub = raw as { platform?: string; date?: string };
			return [pub.platform, pub.date].filter(Boolean).join(" · ");
		}
		case "skills": {
			const cat = raw as { kind?: string; skills?: string[] };
			return [cat.kind, `${cat.skills?.length ?? 0} skills`]
				.filter(Boolean)
				.join(" · ");
		}
		default:
			return "";
	}
}

/**
 * @function toListItem
 * @description Normaliza un record crudo del GET /cv al shape de card de la
 *   lista (titulo + subtitulo + badges de niches) segun la seccion.
 */
export function toListItem(
	section: CvSection,
	raw: CvEntityRecord,
): SectionListItem {
	const record = raw as RawRecord;
	return {
		slug: record.slug,
		title: titleOf(section, record),
		subtitle: subtitleOf(section, record),
		niches: (record.niches as string[] | undefined) ?? [],
	};
}

/**
 * @function countEntries
 * @description Conteo de entradas para la card del overview: arrays -> length,
 *   profile -> 1 si tiene datos, secciones sin lectura (publications) -> null
 *   (la card muestra un guion).
 */
export function countEntries(section: CvSection, data: unknown): number | null {
	if (SECTION_CONFIG[section].readAction === null) return null;
	if (section === "profile") {
		return data !== null &&
			typeof data === "object" &&
			Object.keys(data).length > 0
			? 1
			: 0;
	}
	return Array.isArray(data) ? data.length : 0;
}
