import { z } from "zod";

/**
 * @module features/cv-management/validation
 * @description Zod schemas de los forms del CV — mirror de los modelos
 *   Pydantic de cv_admin (slug kebab-case, fechas YYYY[-MM[-DD]], bloques
 *   BiLang). Regla de la fase 3: en los campos BiLang REQUERIDOS ambos
 *   locales (es y en) son obligatorios y el error señala el locale faltante.
 *   Los opcionales aceptan ambos vacios, pero si un locale se llena el otro
 *   tambien se exige.
 */

export const SLUG_PATTERN = /^[a-z0-9]+(-[a-z0-9]+)*$/;

export const slugSchema = z
	.string()
	.min(1, "El slug es obligatorio")
	.regex(SLUG_PATTERN, "Slug invalido: usa kebab-case (a-z, 0-9 y guiones)");

const DATE_PATTERN = /^\d{4}(-\d{2}(-\d{2})?)?$/;

function validateDateParts(value: string, ctx: z.RefinementCtx): void {
	const [, month, day] = value.split("-");
	if (month !== undefined) {
		const monthNum = Number(month);
		if (monthNum < 1 || monthNum > 12) {
			ctx.addIssue({
				code: z.ZodIssueCode.custom,
				message: "Mes invalido (01-12)",
			});
			return;
		}
	}
	if (day !== undefined) {
		const dayNum = Number(day);
		if (dayNum < 1 || dayNum > 31) {
			ctx.addIssue({
				code: z.ZodIssueCode.custom,
				message: "Dia invalido (01-31)",
			});
		}
	}
}

/** Fecha del seed: YYYY, YYYY-MM o YYYY-MM-DD con mes/dia validos. */
export const flexDateSchema = z
	.string()
	.min(1, "La fecha es obligatoria")
	.regex(DATE_PATTERN, "Formato de fecha invalido: YYYY-MM o YYYY-MM-DD")
	.superRefine((value, ctx) => {
		if (DATE_PATTERN.test(value)) validateDateParts(value, ctx);
	});

/** Fecha opcional: '' permitido; si hay valor aplica flexDateSchema. */
export const optionalFlexDateSchema = z.string().superRefine((value, ctx) => {
	if (value === "") return;
	if (!DATE_PATTERN.test(value)) {
		ctx.addIssue({
			code: z.ZodIssueCode.custom,
			message: "Formato de fecha invalido: YYYY-MM o YYYY-MM-DD",
		});
		return;
	}
	validateDateParts(value, ctx);
});

/** BiLang requerido: ambos locales obligatorios, error por locale. */
export const biLangRequiredSchema = z.object({
	es: z.string().min(1, "Falta el texto en español (es)"),
	en: z.string().min(1, "Falta el texto en inglés (en)"),
});
export type BiLangInput = z.infer<typeof biLangRequiredSchema>;

/** BiLang opcional: ambos vacios OK; con un locale lleno se exige el otro. */
export const biLangOptionalSchema = z
	.object({ es: z.string(), en: z.string() })
	.superRefine((value, ctx) => {
		if (value.es !== "" && value.en === "") {
			ctx.addIssue({
				code: z.ZodIssueCode.custom,
				message: "Falta el texto en inglés (en)",
				path: ["en"],
			});
		}
		if (value.en !== "" && value.es === "") {
			ctx.addIssue({
				code: z.ZodIssueCode.custom,
				message: "Falta el texto en español (es)",
				path: ["es"],
			});
		}
	});

/** Listas paralelas es/en: cada bullet con ambos idiomas completos. */
export const biLangListSchema = z
	.object({ es: z.array(z.string()), en: z.array(z.string()) })
	.superRefine((value, ctx) => {
		const incomplete =
			value.es.some((item) => item.trim() === "") ||
			value.en.some((item) => item.trim() === "") ||
			value.es.length !== value.en.length;
		if (incomplete) {
			ctx.addIssue({
				code: z.ZodIssueCode.custom,
				message: "Completa ambos idiomas en cada bullet",
			});
		}
	});

export const nichesRequiredSchema = z
	.array(z.string())
	.min(1, "Selecciona al menos un niche");

export const prioritySchema = z.record(z.string(), z.number().int());

/** Par {key, value} de los editores de listas (links, metricas). */
export const pairSchema = z.object({
	key: z.string().min(1, "Campo obligatorio"),
	value: z.string().min(1, "Campo obligatorio"),
});
export type PairInput = z.infer<typeof pairSchema>;

export const SENIORITY_VALUES = [
	"intern",
	"junior",
	"mid",
	"senior",
	"lead",
] as const;
export const PROJECT_STATUS_VALUES = ["active", "inactive", "concept"] as const;
export const PROJECT_TYPE_VALUES = [
	"web",
	"mobile",
	"cli",
	"library",
	"ai",
	"fintech-platform",
] as const;
export const SKILL_KIND_VALUES = ["technical", "soft"] as const;

export const experienceFormSchema = z.object({
	slug: slugSchema,
	role: biLangRequiredSchema,
	company: z.string().min(1, "La empresa es obligatoria"),
	country: z.string().min(1, "El pais es obligatorio"),
	companyUrl: z.string(),
	start: flexDateSchema,
	end: optionalFlexDateSchema,
	seniority: z.enum(SENIORITY_VALUES, {
		errorMap: () => ({ message: "Selecciona la seniority" }),
	}),
	summary: biLangOptionalSchema,
	metricsEstimated: z.boolean(),
	responsibilities: biLangListSchema,
	achievements: biLangListSchema,
	skillsTechnical: z.array(z.string()),
	skillsSoft: z.array(z.string()),
	niches: nichesRequiredSchema,
	priority: prioritySchema,
});
export type ExperienceFormValues = z.infer<typeof experienceFormSchema>;

export const projectFormSchema = z.object({
	slug: slugSchema,
	name: z.string().min(1, "El nombre es obligatorio"),
	summary: biLangRequiredSchema,
	description: biLangOptionalSchema,
	url: z.string(),
	repo: z.string(),
	links: z.array(pairSchema),
	status: z.enum(PROJECT_STATUS_VALUES, {
		errorMap: () => ({ message: "Selecciona el estado" }),
	}),
	projectType: z.enum(PROJECT_TYPE_VALUES, {
		errorMap: () => ({ message: "Selecciona el tipo" }),
	}),
	isConfidential: z.boolean(),
	metricsEstimated: z.boolean(),
	stack: z.array(z.string()),
	caseStudy: biLangOptionalSchema,
	caseStudyProblem: biLangOptionalSchema,
	caseStudyProcess: biLangOptionalSchema,
	caseStudyResult: biLangOptionalSchema,
	metrics: z.array(pairSchema),
	niches: nichesRequiredSchema,
	priority: prioritySchema,
});
export type ProjectFormValues = z.infer<typeof projectFormSchema>;

export const profileFormSchema = z.object({
	name: z.string().min(1, "El nombre es obligatorio"),
	handle: slugSchema,
	headline: biLangRequiredSchema,
	summary: biLangRequiredSchema,
	location: z.string().min(1, "La ubicacion es obligatoria"),
	availability: biLangOptionalSchema,
	email: z.string().email("Email invalido"),
	phone: z.string(),
	linkedin: z.string().min(1, "El LinkedIn es obligatorio"),
	github: z.string().min(1, "El GitHub es obligatorio"),
	website: z.string(),
	avatarUrl: z.string().min(1, "El avatar es obligatorio"),
	niches: z.array(z.string()),
	yearsExperience: z.coerce.number().int().min(0, "Debe ser >= 0"),
	companies: z.coerce.number().int().min(0, "Debe ser >= 0"),
	countries: z.coerce.number().int().min(0, "Debe ser >= 0"),
	certifications: z.coerce.number().int().min(0, "Debe ser >= 0"),
});
export type ProfileFormValues = z.infer<typeof profileFormSchema>;

export const skillCategoryFormSchema = z.object({
	slug: slugSchema,
	name: biLangRequiredSchema,
	kind: z.enum(SKILL_KIND_VALUES, {
		errorMap: () => ({ message: "Selecciona el tipo" }),
	}),
	skills: z.array(z.string()).min(1, "Agrega al menos una skill"),
	niches: nichesRequiredSchema,
	priority: prioritySchema,
});
export type SkillCategoryFormValues = z.infer<typeof skillCategoryFormSchema>;
