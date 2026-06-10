import { z } from "zod";
import type { CvEntitySectionKind } from "../types";
import {
	biLangOptionalSchema,
	biLangRequiredSchema,
	flexDateSchema,
	nichesRequiredSchema,
	optionalFlexDateSchema,
	prioritySchema,
	slugSchema,
} from "../validation";

/**
 * @module features/cv-management/lib/simple-entities
 * @description Config declarativa de las 6 entidades simples (education,
 *   certificate, award, language, endorsement, publication): campos por
 *   entidad (kind + requerido) y el Zod schema dinamico que valida el form
 *   parametrizado `SimpleEntityForm`. Mirror de content_simple.py.
 */

export type SimpleEntityKind =
	| "education"
	| "certificate"
	| "award"
	| "language"
	| "endorsement"
	| "publication";

export type SimpleFieldKind = "text" | "date" | "bilang" | "bilang-multiline";

export interface SimpleFieldDef {
	name: string;
	label: string;
	kind: SimpleFieldKind;
	required: boolean;
}

export const SIMPLE_ENTITY_FIELDS: Record<SimpleEntityKind, SimpleFieldDef[]> =
	{
		education: [
			{
				name: "institution",
				label: "Institucion",
				kind: "text",
				required: true,
			},
			{ name: "start", label: "Inicio", kind: "date", required: true },
			{ name: "end", label: "Fin", kind: "date", required: false },
			{ name: "url", label: "URL", kind: "text", required: false },
			{ name: "degree", label: "Titulo", kind: "bilang", required: false },
			{
				name: "description",
				label: "Descripcion",
				kind: "bilang-multiline",
				required: true,
			},
		],
		certificate: [
			{ name: "title", label: "Titulo", kind: "text", required: true },
			{ name: "issuer", label: "Emisor", kind: "text", required: true },
			{ name: "date", label: "Fecha", kind: "date", required: true },
			{ name: "url", label: "URL", kind: "text", required: true },
		],
		award: [
			{ name: "title", label: "Titulo", kind: "bilang", required: true },
			{ name: "issuer", label: "Emisor", kind: "text", required: true },
			{ name: "date", label: "Fecha", kind: "date", required: true },
			{ name: "url", label: "URL", kind: "text", required: false },
			{
				name: "motivation",
				label: "Motivacion",
				kind: "bilang-multiline",
				required: true,
			},
		],
		language: [
			{ name: "name", label: "Idioma", kind: "bilang", required: true },
			{ name: "level", label: "Nivel", kind: "bilang", required: true },
		],
		endorsement: [
			{ name: "name", label: "Nombre", kind: "text", required: true },
			{ name: "role", label: "Cargo", kind: "text", required: true },
			{ name: "company", label: "Empresa", kind: "text", required: false },
			{ name: "linkedin", label: "LinkedIn", kind: "text", required: true },
			{
				name: "relation",
				label: "Relacion",
				kind: "bilang-multiline",
				required: true,
			},
		],
		publication: [
			{ name: "title", label: "Titulo", kind: "text", required: true },
			{ name: "platform", label: "Plataforma", kind: "text", required: true },
			{ name: "url", label: "URL", kind: "text", required: true },
			{
				name: "canonical",
				label: "URL canonica",
				kind: "text",
				required: false,
			},
			{ name: "date", label: "Fecha", kind: "date", required: true },
			{
				name: "summary",
				label: "Resumen",
				kind: "bilang-multiline",
				required: true,
			},
		],
	};

/** Mapea cada seccion de lista del admin a su entidad simple (si lo es). */
export const SECTION_SIMPLE_ENTITY: Partial<
	Record<CvEntitySectionKind, SimpleEntityKind>
> = {
	education: "education",
	certificates: "certificate",
	awards: "award",
	languages: "language",
	endorsements: "endorsement",
	publications: "publication",
};

function fieldSchema(field: SimpleFieldDef): z.ZodTypeAny {
	if (field.kind === "date") {
		return field.required ? flexDateSchema : optionalFlexDateSchema;
	}
	if (field.kind === "bilang" || field.kind === "bilang-multiline") {
		return field.required ? biLangRequiredSchema : biLangOptionalSchema;
	}
	return field.required
		? z.string().min(1, `${field.label}: campo obligatorio`)
		: z.string();
}

/**
 * @function buildSimpleEntitySchema
 * @description Construye el Zod schema del form de una entidad simple desde
 *   su config de campos (+ slug, niches y priority transversales).
 */
export function buildSimpleEntitySchema(
	entity: SimpleEntityKind,
): z.ZodTypeAny {
	const shape: Record<string, z.ZodTypeAny> = { slug: slugSchema };
	for (const field of SIMPLE_ENTITY_FIELDS[entity]) {
		shape[field.name] = fieldSchema(field);
	}
	shape.niches = nichesRequiredSchema;
	shape.priority = prioritySchema;
	return z.object(shape);
}

/** Valores del form parametrizado de entidades simples. */
export type SimpleEntityFormValues = Record<string, unknown> & {
	slug: string;
	niches: string[];
	priority: Record<string, number>;
};
