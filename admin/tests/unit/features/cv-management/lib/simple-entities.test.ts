import { describe, expect, it } from "vitest";
import {
	buildSimpleEntitySchema,
	SECTION_SIMPLE_ENTITY,
	SIMPLE_ENTITY_FIELDS,
} from "@/features/cv-management/lib/simple-entities";

/**
 * @module tests/unit/features/cv-management/lib/simple-entities
 * @description Verifica la config de las 6 entidades simples y el schema
 *   dinamico: requeridos por kind (text/date/bilang), opcionales vacios
 *   permitidos y mapeo seccion -> entidad.
 */

describe("SIMPLE_ENTITY_FIELDS", () => {
	it("Given las 6 entidades When se inspeccionan Then declaran sus campos del contrato", () => {
		// Arrange + Act + Assert
		expect(Object.keys(SIMPLE_ENTITY_FIELDS)).toEqual([
			"education",
			"certificate",
			"award",
			"language",
			"endorsement",
			"publication",
		]);
		expect(SIMPLE_ENTITY_FIELDS.certificate.map((field) => field.name)).toEqual(
			["title", "issuer", "date", "url"],
		);
		expect(SIMPLE_ENTITY_FIELDS.publication.map((field) => field.name)).toEqual(
			["title", "platform", "url", "canonical", "date", "summary"],
		);
	});

	it("Given el mapeo de secciones When se inspecciona Then cubre las 6 secciones simples", () => {
		// Arrange + Act + Assert
		expect(SECTION_SIMPLE_ENTITY).toEqual({
			education: "education",
			certificates: "certificate",
			awards: "award",
			languages: "language",
			endorsements: "endorsement",
			publications: "publication",
		});
	});
});

describe("buildSimpleEntitySchema", () => {
	it("Given un certificate valido When se valida Then pasa", () => {
		// Arrange
		const schema = buildSimpleEntitySchema("certificate");

		// Act
		const result = schema.safeParse({
			slug: "cert-1",
			title: "Cert",
			issuer: "AWS",
			date: "2024-01",
			url: "https://x.test",
			niches: ["generic"],
			priority: {},
		});

		// Assert
		expect(result.success).toBe(true);
	});

	it("Given un certificate sin title When se valida Then falla con el label en el mensaje", () => {
		// Arrange
		const schema = buildSimpleEntitySchema("certificate");

		// Act
		const result = schema.safeParse({
			slug: "cert-1",
			title: "",
			issuer: "AWS",
			date: "2024-01",
			url: "https://x.test",
			niches: ["generic"],
			priority: {},
		});

		// Assert
		expect(result.success).toBe(false);
		const message = result.success
			? ""
			: result.error.issues.find((issue) => issue.path[0] === "title")?.message;
		expect(message).toBe("Titulo: campo obligatorio");
	});

	it("Given una education con end vacio y degree vacio When se valida Then pasa (opcionales)", () => {
		// Arrange
		const schema = buildSimpleEntitySchema("education");

		// Act
		const result = schema.safeParse({
			slug: "edu-1",
			institution: "Uni",
			start: "2015",
			end: "",
			url: "",
			degree: { es: "", en: "" },
			description: { es: "a", en: "b" },
			niches: ["generic"],
			priority: {},
		});

		// Assert
		expect(result.success).toBe(true);
	});

	it("Given un language sin name.en When se valida Then el error señala el locale en", () => {
		// Arrange
		const schema = buildSimpleEntitySchema("language");

		// Act
		const result = schema.safeParse({
			slug: "lang-1",
			name: { es: "Ingles", en: "" },
			level: { es: "Avanzado", en: "Advanced" },
			niches: ["generic"],
			priority: {},
		});

		// Assert
		expect(result.success).toBe(false);
		const issue = result.success
			? undefined
			: result.error.issues.find((entry) => entry.path[0] === "name");
		expect(issue?.path).toEqual(["name", "en"]);
		expect(issue?.message).toBe("Falta el texto en inglés (en)");
	});

	it("Given un endorsement sin niches When se valida Then falla con el mensaje de niches", () => {
		// Arrange
		const schema = buildSimpleEntitySchema("endorsement");

		// Act
		const result = schema.safeParse({
			slug: "endo-1",
			name: "Persona",
			role: "CTO",
			company: "",
			linkedin: "https://li.test",
			relation: { es: "a", en: "b" },
			niches: [],
			priority: {},
		});

		// Assert
		expect(result.success).toBe(false);
		const message = result.success
			? ""
			: result.error.issues.find((issue) => issue.path[0] === "niches")
					?.message;
		expect(message).toBe("Selecciona al menos un niche");
	});
});
