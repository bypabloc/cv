import type {
	BiLang,
	BiLangList,
	CvExperience,
	CvProfile,
	CvProject,
	CvProjectLink,
	CvSkillCategory,
} from "../types";
import type {
	ExperienceFormValues,
	PairInput,
	ProfileFormValues,
	ProjectFormValues,
	SkillCategoryFormValues,
} from "../validation";
import {
	SIMPLE_ENTITY_FIELDS,
	type SimpleEntityFormValues,
	type SimpleEntityKind,
} from "./simple-entities";

/**
 * @module features/cv-management/lib/payloads
 * @description Conversion form <-> payload del contrato cv_admin. Los forms
 *   trabajan con strings vacios y listas de pares; los payloads omiten los
 *   opcionales vacios (el backend trata ausencia como null) y convierten las
 *   metricas a un objeto key/value ORDENADO.
 */

/** '' -> undefined (los opcionales vacios se omiten del payload). */
export function optionalText(value: string): string | undefined {
	return value === "" ? undefined : value;
}

/** BiLang de form ({es:'',en:''}) -> BiLang del payload o undefined. */
export function optionalBiLang(value: {
	es: string;
	en: string;
}): BiLang | undefined {
	if (value.es === "" && value.en === "") return undefined;
	return { es: value.es, en: value.en };
}

/** BiLang del payload -> shape de form (ambos locales como string). */
export function biLangToForm(value: BiLang | undefined): {
	es: string;
	en: string;
} {
	return { es: value?.es ?? "", en: value?.en ?? "" };
}

/** BiLangList del payload -> listas paralelas con ambos arrays. */
export function biLangListToForm(value: BiLangList | undefined): {
	es: string[];
	en: string[];
} {
	return { es: [...(value?.es ?? [])], en: [...(value?.en ?? [])] };
}

/** Pares {key,value} -> objeto ORDENADO (insercion = presentacion). */
export function pairsToRecord(pairs: PairInput[]): Record<string, string> {
	const record: Record<string, string> = {};
	for (const pair of pairs) {
		record[pair.key] = pair.value;
	}
	return record;
}

/** Objeto ordenado -> pares {key,value} para el editor. */
export function recordToPairs(
	record: Record<string, string | number> | undefined,
): PairInput[] {
	return Object.entries(record ?? {}).map(([key, value]) => ({
		key,
		value: String(value),
	}));
}

/** Links {label,url} -> pares del editor (key=label, value=url). */
export function linksToPairs(links: CvProjectLink[] | undefined): PairInput[] {
	return (links ?? []).map((link) => ({ key: link.label, value: link.url }));
}

export function pairsToLinks(pairs: PairInput[]): CvProjectLink[] {
	return pairs.map((pair) => ({ label: pair.key, url: pair.value }));
}

// --- Experience ---

export function experienceToForm(
	initial: CvExperience | undefined,
): ExperienceFormValues {
	return {
		slug: initial?.slug ?? "",
		role: biLangToForm(initial?.role),
		company: initial?.company ?? "",
		country: initial?.country ?? "",
		companyUrl: initial?.companyUrl ?? "",
		start: initial?.start ?? "",
		end: initial?.end ?? "",
		seniority: initial?.seniority ?? ("" as ExperienceFormValues["seniority"]),
		summary: biLangToForm(initial?.summary),
		metricsEstimated: initial?.metricsEstimated ?? false,
		responsibilities: biLangListToForm(initial?.responsibilities),
		achievements: biLangListToForm(initial?.achievements),
		skillsTechnical: [...(initial?.skillsTechnical ?? [])],
		skillsSoft: [...(initial?.skillsSoft ?? [])],
		niches: [...(initial?.niches ?? [])],
		priority: { ...(initial?.priority ?? {}) },
	};
}

export function experienceToPayload(
	values: ExperienceFormValues,
): CvExperience {
	return {
		slug: values.slug,
		role: values.role,
		company: values.company,
		country: values.country,
		companyUrl: optionalText(values.companyUrl),
		start: values.start,
		end: optionalText(values.end),
		seniority: values.seniority,
		summary: optionalBiLang(values.summary),
		metricsEstimated: values.metricsEstimated,
		responsibilities: values.responsibilities,
		achievements: values.achievements,
		skillsTechnical: values.skillsTechnical,
		skillsSoft: values.skillsSoft,
		niches: values.niches,
		priority: values.priority,
	};
}

// --- Project ---

export function projectToForm(
	initial: CvProject | undefined,
): ProjectFormValues {
	return {
		slug: initial?.slug ?? "",
		name: initial?.name ?? "",
		summary: biLangToForm(initial?.summary),
		description: biLangToForm(initial?.description),
		url: initial?.url ?? "",
		repo: initial?.repo ?? "",
		links: linksToPairs(initial?.links),
		status: initial?.status ?? ("" as ProjectFormValues["status"]),
		projectType:
			initial?.projectType ?? ("" as ProjectFormValues["projectType"]),
		isConfidential: initial?.isConfidential ?? false,
		metricsEstimated: initial?.metricsEstimated ?? false,
		stack: [...(initial?.stack ?? [])],
		caseStudy: biLangToForm(initial?.caseStudy),
		caseStudyProblem: biLangToForm(initial?.caseStudyDetailed?.problem),
		caseStudyProcess: biLangToForm(initial?.caseStudyDetailed?.process),
		caseStudyResult: biLangToForm(initial?.caseStudyDetailed?.result),
		metrics: recordToPairs(initial?.metrics),
		niches: [...(initial?.niches ?? [])],
		priority: { ...(initial?.priority ?? {}) },
	};
}

function caseStudyDetailedPayload(
	values: ProjectFormValues,
): CvProject["caseStudyDetailed"] {
	const problem = optionalBiLang(values.caseStudyProblem);
	const process = optionalBiLang(values.caseStudyProcess);
	const result = optionalBiLang(values.caseStudyResult);
	if (!problem && !process && !result) return undefined;
	return { problem, process, result };
}

export function projectToPayload(values: ProjectFormValues): CvProject {
	return {
		slug: values.slug,
		name: values.name,
		summary: values.summary,
		description: optionalBiLang(values.description),
		url: optionalText(values.url),
		links: values.links.length > 0 ? pairsToLinks(values.links) : undefined,
		repo: optionalText(values.repo),
		status: values.status,
		projectType: values.projectType,
		isConfidential: values.isConfidential,
		metricsEstimated: values.metricsEstimated,
		stack: values.stack,
		caseStudy: optionalBiLang(values.caseStudy),
		caseStudyDetailed: caseStudyDetailedPayload(values),
		metrics: pairsToRecord(values.metrics),
		niches: values.niches,
		priority: values.priority,
	};
}

// --- Profile ---

export function profileToForm(
	initial: CvProfile | undefined,
): ProfileFormValues {
	return {
		name: initial?.name ?? "",
		handle: initial?.handle ?? "",
		headline: biLangToForm(initial?.headline),
		summary: biLangToForm(initial?.summary),
		location: initial?.location ?? "",
		availability: biLangToForm(initial?.availability),
		email: initial?.contacts?.email ?? "",
		phone: initial?.contacts?.phone ?? "",
		linkedin: initial?.contacts?.linkedin ?? "",
		github: initial?.contacts?.github ?? "",
		website: initial?.contacts?.website ?? "",
		avatarUrl: initial?.avatarUrl ?? "",
		niches: [...(initial?.niches ?? [])],
		yearsExperience: initial?.stats?.yearsExperience ?? 0,
		companies: initial?.stats?.companies ?? 0,
		countries: initial?.stats?.countries ?? 0,
		certifications: initial?.stats?.certifications ?? 0,
	};
}

export function profileToPayload(values: ProfileFormValues): CvProfile {
	return {
		name: values.name,
		handle: values.handle,
		headline: values.headline,
		summary: values.summary,
		location: values.location,
		availability: optionalBiLang(values.availability),
		contacts: {
			email: values.email,
			phone: optionalText(values.phone),
			linkedin: values.linkedin,
			github: values.github,
			website: optionalText(values.website),
		},
		avatarUrl: values.avatarUrl,
		niches: values.niches,
		stats: {
			yearsExperience: values.yearsExperience,
			companies: values.companies,
			countries: values.countries,
			certifications: values.certifications,
		},
	};
}

// --- Skill category ---

export function skillCategoryToForm(
	initial: CvSkillCategory | undefined,
): SkillCategoryFormValues {
	return {
		slug: initial?.slug ?? "",
		name: biLangToForm(initial?.name),
		kind: initial?.kind ?? ("" as SkillCategoryFormValues["kind"]),
		skills: [...(initial?.skills ?? [])],
		niches: [...(initial?.niches ?? [])],
		priority: { ...(initial?.priority ?? {}) },
	};
}

export function skillCategoryToPayload(
	values: SkillCategoryFormValues,
): CvSkillCategory {
	return {
		slug: values.slug,
		name: values.name,
		kind: values.kind,
		skills: values.skills,
		niches: values.niches,
		priority: values.priority,
	};
}

// --- Entidades simples (config-driven) ---

type SimpleValue = string | { es: string; en: string };

function simpleFieldToForm(kind: string, value: unknown): SimpleValue {
	if (kind === "bilang" || kind === "bilang-multiline") {
		return biLangToForm(value as BiLang | undefined);
	}
	return typeof value === "string" ? value : "";
}

/**
 * @function simpleEntityToForm
 * @description Record crudo de una entidad simple -> valores del form
 *   parametrizado (strings vacios para los opcionales ausentes).
 */
export function simpleEntityToForm(
	entity: SimpleEntityKind,
	initial: Record<string, unknown> | undefined,
): SimpleEntityFormValues {
	const values: SimpleEntityFormValues = {
		slug: typeof initial?.slug === "string" ? initial.slug : "",
		niches: Array.isArray(initial?.niches) ? [...initial.niches] : [],
		priority:
			initial?.priority !== null && typeof initial?.priority === "object"
				? ({ ...initial.priority } as Record<string, number>)
				: {},
	};
	for (const field of SIMPLE_ENTITY_FIELDS[entity]) {
		values[field.name] = simpleFieldToForm(field.kind, initial?.[field.name]);
	}
	return values;
}

function simpleFieldToPayload(
	kind: string,
	required: boolean,
	value: SimpleValue,
): unknown {
	if (kind === "bilang" || kind === "bilang-multiline") {
		const biLang = value as { es: string; en: string };
		return required ? biLang : optionalBiLang(biLang);
	}
	const text = value as string;
	return required ? text : optionalText(text);
}

/**
 * @function simpleEntityToPayload
 * @description Valores del form parametrizado -> payload del upsert (omite
 *   opcionales vacios; los BiLang opcionales vacios se descartan).
 */
export function simpleEntityToPayload(
	entity: SimpleEntityKind,
	values: SimpleEntityFormValues,
): Record<string, unknown> {
	const payload: Record<string, unknown> = {
		slug: values.slug,
		niches: values.niches,
		priority: values.priority,
	};
	for (const field of SIMPLE_ENTITY_FIELDS[entity]) {
		const converted = simpleFieldToPayload(
			field.kind,
			field.required,
			values[field.name] as SimpleValue,
		);
		if (converted !== undefined) payload[field.name] = converted;
	}
	return payload;
}
