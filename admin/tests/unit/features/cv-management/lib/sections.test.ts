import { describe, expect, it } from "vitest";
import {
	CV_SECTIONS,
	countEntries,
	SECTION_CONFIG,
	toListItem,
} from "@/features/cv-management/lib/sections";
import type { CvEntityRecord } from "@/features/cv-management/types";

/**
 * @module tests/unit/features/cv-management/lib/sections
 * @description Verifica la config por seccion (labels, read actions, entity
 *   types), la normalizacion a card (toListItem) por cada seccion y el
 *   conteo del overview (countEntries) con sus 3 ramas.
 */

describe("SECTION_CONFIG", () => {
	it("Given las 10 secciones When se inspeccionan Then el orden y labels son los del sub-nav", () => {
		// Arrange + Act + Assert
		expect(CV_SECTIONS).toEqual([
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
		]);
		expect(SECTION_CONFIG.endorsements.readAction).toBe("references");
		expect(SECTION_CONFIG.publications.readAction).toBeNull();
		expect(SECTION_CONFIG.skills.entityType).toBe("skill_category");
		expect(SECTION_CONFIG.profile.entityType).toBeNull();
	});
});

describe("toListItem", () => {
	it("Given una experiencia When se normaliza Then title=role.es y subtitle empresa+rango", () => {
		// Arrange
		const record = {
			slug: "exp-1",
			role: { es: "Arquitecto", en: "Architect" },
			company: "Acme",
			country: "Peru",
			start: "2021-03",
			end: "2024-01",
			seniority: "senior",
			skillsTechnical: [],
			skillsSoft: [],
			niches: ["generic"],
			priority: {},
		} as CvEntityRecord;

		// Act
		const item = toListItem("experiences", record);

		// Assert
		expect(item).toEqual({
			slug: "exp-1",
			title: "Arquitecto",
			subtitle: "Acme · 2021-03 — 2024-01",
			niches: ["generic"],
		});
	});

	it("Given una experiencia sin end When se normaliza Then subtitle dice Presente", () => {
		// Arrange
		const record = {
			slug: "exp-2",
			role: { en: "Lead" },
			company: "Beta",
			country: "Chile",
			start: "2024-02",
			seniority: "lead",
			skillsTechnical: [],
			skillsSoft: [],
			niches: [],
			priority: {},
		} as CvEntityRecord;

		// Act
		const item = toListItem("experiences", record);

		// Assert: sin es cae al en; niches ausentes -> [].
		expect(item.title).toBe("Lead");
		expect(item.subtitle).toBe("Beta · 2024-02 — Presente");
		expect(item.niches).toEqual([]);
	});

	it("Given un proyecto When se normaliza Then title=name y subtitle tipo+estado", () => {
		// Arrange
		const record = {
			slug: "proj-1",
			name: "Portfolio",
			summary: { es: "a", en: "b" },
			status: "active",
			projectType: "web",
			stack: [],
			metrics: {},
			niches: ["generic"],
			priority: {},
		} as CvEntityRecord;

		// Act + Assert
		expect(toListItem("projects", record)).toEqual({
			slug: "proj-1",
			title: "Portfolio",
			subtitle: "web · active",
			niches: ["generic"],
		});
	});

	it("Given las entidades restantes When se normalizan Then cada subtitle usa sus campos", () => {
		// Arrange + Act + Assert
		expect(
			toListItem("education", {
				slug: "edu-1",
				institution: "Uni",
				start: "2015",
				degree: { es: "Ing." },
				description: { es: "a", en: "b" },
			} as CvEntityRecord),
		).toEqual({
			slug: "edu-1",
			title: "Uni",
			subtitle: "Ing. · 2015",
			niches: [],
		});

		expect(
			toListItem("certificates", {
				slug: "cert-1",
				title: "Cert",
				issuer: "AWS",
				date: "2024-01-01",
				url: "https://x.test",
			} as CvEntityRecord),
		).toEqual({
			slug: "cert-1",
			title: "Cert",
			subtitle: "AWS · 2024-01-01",
			niches: [],
		});

		expect(
			toListItem("awards", {
				slug: "award-1",
				title: { es: "Premio", en: "Award" },
				issuer: "Org",
				date: "2023-05",
				motivation: { es: "a", en: "b" },
			} as CvEntityRecord),
		).toEqual({
			slug: "award-1",
			title: "Premio",
			subtitle: "Org · 2023-05",
			niches: [],
		});

		expect(
			toListItem("languages", {
				slug: "lang-1",
				name: { es: "Ingles", en: "English" },
				level: { es: "Avanzado", en: "Advanced" },
			} as CvEntityRecord),
		).toEqual({
			slug: "lang-1",
			title: "Ingles",
			subtitle: "Avanzado",
			niches: [],
		});

		expect(
			toListItem("endorsements", {
				slug: "endo-1",
				name: "Persona",
				role: "CTO",
				company: "Acme",
				relation: { es: "a", en: "b" },
				linkedin: "https://li.test",
			} as CvEntityRecord),
		).toEqual({
			slug: "endo-1",
			title: "Persona",
			subtitle: "CTO · Acme",
			niches: [],
		});

		expect(
			toListItem("publications", {
				slug: "pub-1",
				title: "Post",
				platform: "Dev.to",
				url: "https://pub.test",
				date: "2024-02",
				summary: { es: "a", en: "b" },
			} as CvEntityRecord),
		).toEqual({
			slug: "pub-1",
			title: "Post",
			subtitle: "Dev.to · 2024-02",
			niches: [],
		});

		expect(
			toListItem("skills", {
				slug: "cat-1",
				name: { es: "Backend", en: "Backend" },
				kind: "technical",
				skills: ["Python", "SQL"],
				niches: ["generic"],
			} as CvEntityRecord),
		).toEqual({
			slug: "cat-1",
			title: "Backend",
			subtitle: "technical · 2 skills",
			niches: ["generic"],
		});
	});

	it("Given un record sin titulo When se normaliza Then cae al slug", () => {
		// Arrange + Act
		const item = toListItem("languages", {
			slug: "lang-x",
			name: {},
			level: {},
		} as CvEntityRecord);

		// Assert
		expect(item.title).toBe("lang-x");
		expect(item.subtitle).toBe("");
	});
});

describe("countEntries", () => {
	it("Given un array When se cuenta Then devuelve el length", () => {
		// Arrange + Act + Assert
		expect(countEntries("experiences", [{}, {}])).toBe(2);
		expect(countEntries("projects", undefined)).toBe(0);
	});

	it("Given el profile When se cuenta Then 1 con datos y 0 vacio", () => {
		// Arrange + Act + Assert
		expect(countEntries("profile", { name: "Pablo" })).toBe(1);
		expect(countEntries("profile", {})).toBe(0);
		expect(countEntries("profile", undefined)).toBe(0);
	});

	it("Given publications (sin lectura) When se cuenta Then null", () => {
		// Arrange + Act + Assert
		expect(countEntries("publications", [])).toBeNull();
	});
});
