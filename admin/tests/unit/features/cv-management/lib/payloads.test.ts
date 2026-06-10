import { describe, expect, it } from "vitest";
import {
	biLangListToForm,
	biLangToForm,
	experienceToForm,
	experienceToPayload,
	linksToPairs,
	optionalBiLang,
	optionalText,
	pairsToLinks,
	pairsToRecord,
	profileToForm,
	profileToPayload,
	projectToForm,
	projectToPayload,
	recordToPairs,
	simpleEntityToForm,
	simpleEntityToPayload,
	skillCategoryToForm,
	skillCategoryToPayload,
} from "@/features/cv-management/lib/payloads";
import type {
	CvExperience,
	CvProfile,
	CvProject,
} from "@/features/cv-management/types";

/**
 * @module tests/unit/features/cv-management/lib/payloads
 * @description Verifica la conversion form <-> payload: round-trip de
 *   experiencia/proyecto/profile/skill-category, omision de opcionales
 *   vacios, metricas ordenadas array<->record y entidades simples
 *   config-driven.
 */

const EXPERIENCE: CvExperience = {
	slug: "exp-1",
	role: { es: "Rol", en: "Role" },
	company: "Acme",
	country: "Peru",
	companyUrl: "https://acme.test",
	start: "2021-03",
	end: "2024-01",
	seniority: "senior",
	summary: { es: "Resumen", en: "Summary" },
	metricsEstimated: true,
	responsibilities: { es: ["r1"], en: ["r1-en"] },
	achievements: { es: ["a1"], en: ["a1-en"] },
	skillsTechnical: ["Vue"],
	skillsSoft: ["Liderazgo"],
	niches: ["generic"],
	priority: { generic: 5 },
};

describe("helpers", () => {
	it("Given strings y BiLang vacios When se convierten Then se omiten (undefined)", () => {
		// Arrange + Act + Assert
		expect(optionalText("")).toBeUndefined();
		expect(optionalText("x")).toBe("x");
		expect(optionalBiLang({ es: "", en: "" })).toBeUndefined();
		expect(optionalBiLang({ es: "a", en: "b" })).toEqual({ es: "a", en: "b" });
		expect(biLangToForm(undefined)).toEqual({ es: "", en: "" });
		expect(biLangToForm({ es: "a" })).toEqual({ es: "a", en: "" });
		expect(biLangListToForm(undefined)).toEqual({ es: [], en: [] });
	});

	it("Given pares ordenados When se convierten a record y de vuelta Then preservan el orden", () => {
		// Arrange
		const pairs = [
			{ key: "lighthouse", value: "100" },
			{ key: "visitors", value: "5k" },
		];

		// Act
		const record = pairsToRecord(pairs);

		// Assert
		expect(Object.keys(record)).toEqual(["lighthouse", "visitors"]);
		expect(recordToPairs(record)).toEqual(pairs);
		expect(recordToPairs(undefined)).toEqual([]);
		expect(recordToPairs({ n: 3 })).toEqual([{ key: "n", value: "3" }]);
	});

	it("Given links When se convierten a pares y de vuelta Then label/url se preservan", () => {
		// Arrange
		const links = [{ label: "Demo", url: "https://demo.test" }];

		// Act + Assert
		expect(linksToPairs(links)).toEqual([
			{ key: "Demo", value: "https://demo.test" },
		]);
		expect(linksToPairs(undefined)).toEqual([]);
		expect(pairsToLinks([{ key: "Demo", value: "https://demo.test" }])).toEqual(
			links,
		);
	});
});

describe("experience round-trip", () => {
	it("Given una experiencia completa When form->payload Then reproduce el original", () => {
		// Arrange
		const form = experienceToForm(EXPERIENCE);

		// Act
		const payload = experienceToPayload(form);

		// Assert
		expect(payload).toEqual(EXPERIENCE);
	});

	it("Given el alta vacia When se construyen defaults Then opcionales en blanco y payload sin vacios", () => {
		// Arrange
		const form = experienceToForm(undefined);

		// Assert: defaults del alta.
		expect(form.slug).toBe("");
		expect(form.role).toEqual({ es: "", en: "" });
		expect(form.metricsEstimated).toBe(false);

		// Act: el payload omite companyUrl/end/summary vacios.
		const payload = experienceToPayload({
			...form,
			slug: "exp-min",
			role: { es: "a", en: "b" },
			company: "Acme",
			country: "Peru",
			start: "2024-01",
			seniority: "mid",
			niches: ["generic"],
		});

		// Assert
		expect(payload.companyUrl).toBeUndefined();
		expect(payload.end).toBeUndefined();
		expect(payload.summary).toBeUndefined();
	});
});

describe("project round-trip", () => {
	const PROJECT: CvProject = {
		slug: "proj-1",
		name: "Portfolio",
		summary: { es: "a", en: "b" },
		description: { es: "c", en: "d" },
		url: "https://x.test",
		links: [{ label: "Demo", url: "https://demo.test" }],
		repo: "https://gh.test",
		status: "active",
		projectType: "web",
		isConfidential: false,
		metricsEstimated: true,
		stack: ["Astro"],
		caseStudy: { es: "cs", en: "cs-en" },
		caseStudyDetailed: {
			problem: { es: "p", en: "p-en" },
			process: { es: "q", en: "q-en" },
			result: { es: "r", en: "r-en" },
		},
		metrics: { lighthouse: "100" },
		niches: ["generic"],
		priority: { generic: 4 },
	};

	it("Given un proyecto completo When form->payload Then reproduce el original", () => {
		// Arrange
		const form = projectToForm(PROJECT);

		// Act + Assert
		expect(projectToPayload(form)).toEqual(PROJECT);
	});

	it("Given un proyecto minimo When form->payload Then omite links/caseStudyDetailed vacios", () => {
		// Arrange
		const form = projectToForm(undefined);

		// Act
		const payload = projectToPayload({
			...form,
			slug: "proj-min",
			name: "Min",
			summary: { es: "a", en: "b" },
			status: "concept",
			projectType: "cli",
			niches: ["generic"],
		});

		// Assert
		expect(payload.links).toBeUndefined();
		expect(payload.caseStudyDetailed).toBeUndefined();
		expect(payload.description).toBeUndefined();
		expect(payload.url).toBeUndefined();
		expect(payload.repo).toBeUndefined();
		expect(payload.caseStudy).toBeUndefined();
		expect(payload.metrics).toEqual({});
	});

	it("Given solo el result del case study When form->payload Then caseStudyDetailed lleva solo result", () => {
		// Arrange
		const form = projectToForm(undefined);

		// Act
		const payload = projectToPayload({
			...form,
			slug: "proj-cs",
			name: "CS",
			summary: { es: "a", en: "b" },
			status: "active",
			projectType: "web",
			niches: ["generic"],
			caseStudyResult: { es: "r", en: "r-en" },
		});

		// Assert
		expect(payload.caseStudyDetailed).toEqual({
			problem: undefined,
			process: undefined,
			result: { es: "r", en: "r-en" },
		});
	});
});

describe("profile round-trip", () => {
	const PROFILE: CvProfile = {
		name: "Pablo",
		handle: "bypabloc",
		headline: { es: "a", en: "b" },
		summary: { es: "c", en: "d" },
		location: "Lima",
		availability: { es: "Disponible", en: "Available" },
		contacts: {
			email: "owner@test.com",
			phone: "+51 999",
			linkedin: "https://li.test",
			github: "https://gh.test",
			website: "https://web.test",
		},
		avatarUrl: "https://cdn.test/a.webp",
		niches: ["generic"],
		stats: {
			yearsExperience: 10,
			companies: 5,
			countries: 3,
			certifications: 7,
		},
	};

	it("Given un profile completo When form->payload Then reproduce el original", () => {
		// Arrange
		const form = profileToForm(PROFILE);

		// Act + Assert
		expect(profileToPayload(form)).toEqual(PROFILE);
	});

	it("Given un profile sin opcionales When form->payload Then omite phone/website/availability", () => {
		// Arrange
		const form = profileToForm(undefined);

		// Act
		const payload = profileToPayload({
			...form,
			name: "Pablo",
			handle: "bypabloc",
			headline: { es: "a", en: "b" },
			summary: { es: "c", en: "d" },
			location: "Lima",
			email: "owner@test.com",
			linkedin: "https://li.test",
			github: "https://gh.test",
			avatarUrl: "https://cdn.test/a.webp",
		});

		// Assert
		expect(payload.availability).toBeUndefined();
		expect(payload.contacts.phone).toBeUndefined();
		expect(payload.contacts.website).toBeUndefined();
		expect(payload.stats).toEqual({
			yearsExperience: 0,
			companies: 0,
			countries: 0,
			certifications: 0,
		});
	});
});

describe("skill category round-trip", () => {
	it("Given una categoria When form->payload Then preserva el orden de skills", () => {
		// Arrange
		const category = {
			slug: "backend",
			name: { es: "Backend", en: "Backend" },
			kind: "technical" as const,
			skills: ["Python", "SQL", "Go"],
			niches: ["generic"],
			priority: { generic: 2 },
		};

		// Act
		const payload = skillCategoryToPayload(skillCategoryToForm(category));

		// Assert
		expect(payload).toEqual(category);
	});
});

describe("simple entities", () => {
	it("Given un certificate crudo When ->form->payload Then reproduce el original", () => {
		// Arrange
		const certificate = {
			slug: "cert-1",
			title: "Cert",
			issuer: "AWS",
			date: "2024-01-01",
			url: "https://x.test",
			niches: ["generic"],
			priority: { generic: 1 },
		};

		// Act
		const form = simpleEntityToForm("certificate", certificate);
		const payload = simpleEntityToPayload("certificate", form);

		// Assert
		expect(payload).toEqual(certificate);
	});

	it("Given una education sin opcionales When ->payload Then omite end/url/degree vacios", () => {
		// Arrange
		const form = simpleEntityToForm("education", undefined);
		form.slug = "edu-1";
		form.institution = "Uni";
		form.start = "2015";
		form.description = { es: "a", en: "b" };
		form.niches = ["generic"];

		// Act
		const payload = simpleEntityToPayload("education", form);

		// Assert
		expect(payload).toEqual({
			slug: "edu-1",
			institution: "Uni",
			start: "2015",
			description: { es: "a", en: "b" },
			niches: ["generic"],
			priority: {},
		});
	});

	it("Given un award con bilang When ->form Then hidrata title/motivation como pares es/en", () => {
		// Arrange
		const award = {
			slug: "award-1",
			title: { es: "Premio", en: "Award" },
			issuer: "Org",
			date: "2023-05",
			motivation: { es: "m", en: "m-en" },
			niches: ["generic"],
			priority: {},
		};

		// Act
		const form = simpleEntityToForm("award", award);

		// Assert
		expect(form.title).toEqual({ es: "Premio", en: "Award" });
		expect(form.motivation).toEqual({ es: "m", en: "m-en" });
		expect(form.url).toBe("");
	});
});
