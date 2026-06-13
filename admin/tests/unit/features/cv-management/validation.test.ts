import { describe, expect, it } from "vitest";
import {
	biLangListSchema,
	biLangOptionalSchema,
	biLangRequiredSchema,
	experienceFormSchema,
	flexDateSchema,
	nichesRequiredSchema,
	optionalFlexDateSchema,
	slugSchema,
} from "@/features/cv-management/validation";

/**
 * @module tests/unit/features/cv-management/validation
 * @description Verifica los Zod schemas base: slug kebab-case, fechas con
 *   mes/dia validos (2026-13 rechazada), BiLang requerido con error POR
 *   LOCALE, BiLang opcional simetrico, bullets paralelos y niches >= 1.
 */

describe("validation schemas", () => {
	it("Given un slug kebab-case When se valida Then pasa", () => {
		// Arrange + Act + Assert
		expect(slugSchema.safeParse("mi-entrada-2").success).toBe(true);
	});

	it("Given un slug con mayusculas When se valida Then falla con el mensaje exacto", () => {
		// Arrange + Act
		const result = slugSchema.safeParse("Mi-Entrada");

		// Assert
		expect(result.success).toBe(false);
		expect(result.success ? "" : result.error.issues[0]?.message).toBe(
			"Slug invalido: usa kebab-case (a-z, 0-9 y guiones)",
		);
	});

	it("Given fechas YYYY, YYYY-MM y YYYY-MM-DD When se validan Then pasan", () => {
		// Arrange + Act + Assert
		expect(flexDateSchema.safeParse("2024").success).toBe(true);
		expect(flexDateSchema.safeParse("2024-06").success).toBe(true);
		expect(flexDateSchema.safeParse("2024-06-15").success).toBe(true);
	});

	it("Given la fecha 2026-13 When se valida Then falla con Mes invalido (01-12)", () => {
		// Arrange + Act
		const result = flexDateSchema.safeParse("2026-13");

		// Assert
		expect(result.success).toBe(false);
		expect(result.success ? "" : result.error.issues[0]?.message).toBe(
			"Mes invalido (01-12)",
		);
	});

	it("Given la fecha 2026-01-32 When se valida Then falla con Dia invalido (01-31)", () => {
		// Arrange + Act
		const result = flexDateSchema.safeParse("2026-01-32");

		// Assert
		expect(result.success).toBe(false);
		expect(result.success ? "" : result.error.issues[0]?.message).toBe(
			"Dia invalido (01-31)",
		);
	});

	it("Given un formato no fecha When se valida Then falla con el mensaje de formato", () => {
		// Arrange + Act
		const result = flexDateSchema.safeParse("junio 2024");

		// Assert
		expect(result.success).toBe(false);
		expect(result.success ? "" : result.error.issues[0]?.message).toBe(
			"Formato de fecha invalido: YYYY-MM o YYYY-MM-DD",
		);
	});

	it("Given una fecha opcional vacia When se valida Then pasa; invalida Then falla", () => {
		// Arrange + Act + Assert
		expect(optionalFlexDateSchema.safeParse("").success).toBe(true);
		expect(optionalFlexDateSchema.safeParse("2024-02").success).toBe(true);
		const bad = optionalFlexDateSchema.safeParse("13-2026");
		expect(bad.success).toBe(false);
		expect(bad.success ? "" : bad.error.issues[0]?.message).toBe(
			"Formato de fecha invalido: YYYY-MM o YYYY-MM-DD",
		);
		const badMonth = optionalFlexDateSchema.safeParse("2026-13");
		expect(badMonth.success).toBe(false);
		expect(badMonth.success ? "" : badMonth.error.issues[0]?.message).toBe(
			"Mes invalido (01-12)",
		);
	});

	it("Given un BiLang requerido sin en When se valida Then el error señala el locale en", () => {
		// Arrange + Act
		const result = biLangRequiredSchema.safeParse({ es: "Hola", en: "" });

		// Assert
		expect(result.success).toBe(false);
		const issue = result.success ? undefined : result.error.issues[0];
		expect(issue?.path).toEqual(["en"]);
		expect(issue?.message).toBe("Falta el texto en inglés (en)");
	});

	it("Given un BiLang requerido sin es When se valida Then el error señala el locale es", () => {
		// Arrange + Act
		const result = biLangRequiredSchema.safeParse({ es: "", en: "Hi" });

		// Assert
		expect(result.success).toBe(false);
		const issue = result.success ? undefined : result.error.issues[0];
		expect(issue?.path).toEqual(["es"]);
		expect(issue?.message).toBe("Falta el texto en español (es)");
	});

	it("Given un BiLang opcional vacio When se valida Then pasa", () => {
		// Arrange + Act + Assert
		expect(biLangOptionalSchema.safeParse({ es: "", en: "" }).success).toBe(
			true,
		);
	});

	it("Given un BiLang opcional con solo es When se valida Then exige el en", () => {
		// Arrange + Act
		const result = biLangOptionalSchema.safeParse({ es: "Hola", en: "" });

		// Assert
		expect(result.success).toBe(false);
		const issue = result.success ? undefined : result.error.issues[0];
		expect(issue?.path).toEqual(["en"]);
		expect(issue?.message).toBe("Falta el texto en inglés (en)");
	});

	it("Given un BiLang opcional con solo en When se valida Then exige el es", () => {
		// Arrange + Act
		const result = biLangOptionalSchema.safeParse({ es: "", en: "Hi" });

		// Assert
		expect(result.success).toBe(false);
		const issue = result.success ? undefined : result.error.issues[0];
		expect(issue?.path).toEqual(["es"]);
		expect(issue?.message).toBe("Falta el texto en español (es)");
	});

	it("Given bullets con un item sin en When se valida Then falla con el mensaje de bullets", () => {
		// Arrange + Act
		const result = biLangListSchema.safeParse({ es: ["uno"], en: [""] });

		// Assert
		expect(result.success).toBe(false);
		expect(result.success ? "" : result.error.issues[0]?.message).toBe(
			"Completa ambos idiomas en cada bullet",
		);
	});

	it("Given bullets parejos When se validan Then pasan", () => {
		// Arrange + Act + Assert
		expect(
			biLangListSchema.safeParse({ es: ["uno"], en: ["one"] }).success,
		).toBe(true);
	});

	it("Given niches vacios When se validan Then falla con el mensaje exacto", () => {
		// Arrange + Act
		const result = nichesRequiredSchema.safeParse([]);

		// Assert
		expect(result.success).toBe(false);
		expect(result.success ? "" : result.error.issues[0]?.message).toBe(
			"Selecciona al menos un niche",
		);
	});

	it("Given una experiencia completa When se valida Then pasa", () => {
		// Arrange
		const values = {
			slug: "exp-valida",
			role: { es: "Rol", en: "Role" },
			company: "Acme",
			country: "Peru",
			companyUrl: "",
			start: "2024-01",
			end: "",
			seniority: "senior",
			summary: { es: "", en: "" },
			metricsEstimated: false,
			responsibilities: { es: [], en: [] },
			achievements: { es: [], en: [] },
			skillsTechnical: [],
			skillsSoft: [],
			niches: ["generic"],
			priority: { generic: 1 },
		};

		// Act + Assert
		expect(experienceFormSchema.safeParse(values).success).toBe(true);
	});

	it("Given una experiencia sin seniority When se valida Then falla con Selecciona la seniority", () => {
		// Arrange
		const values = {
			slug: "exp-valida",
			role: { es: "Rol", en: "Role" },
			company: "Acme",
			country: "Peru",
			companyUrl: "",
			start: "2024-01",
			end: "",
			seniority: "",
			summary: { es: "", en: "" },
			metricsEstimated: false,
			responsibilities: { es: [], en: [] },
			achievements: { es: [], en: [] },
			skillsTechnical: [],
			skillsSoft: [],
			niches: ["generic"],
			priority: {},
		};

		// Act
		const result = experienceFormSchema.safeParse(values);

		// Assert
		expect(result.success).toBe(false);
		const message = result.success
			? ""
			: result.error.issues.find((issue) => issue.path[0] === "seniority")
					?.message;
		expect(message).toBe("Selecciona la seniority");
	});
});
