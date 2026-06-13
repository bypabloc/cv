import { describe, expect, it } from "vitest";
import {
	cvAdminClient,
	deleteEntity,
	upsertEntity,
} from "@/features/cv-management/api/cv-admin-client";
import type {
	CvEntitySectionKind,
	CvExperience,
} from "@/features/cv-management/types";

/**
 * @module tests/unit/features/cv-management/api/cv-admin-client
 * @description Verifica las 24 actions del cliente admin del Lambda `cv`
 *   (POST /cv) contra MSW (contrato FLAT del request + Envelope en la
 *   respuesta): upserts por entidad, deletes por slug, reorder, catalogs,
 *   get-all y publish.
 */

const EXPERIENCE: CvExperience = {
	slug: "exp-test",
	role: { es: "Rol", en: "Role" },
	company: "Acme",
	country: "Peru",
	start: "2024-01",
	seniority: "senior",
	skillsTechnical: [],
	skillsSoft: [],
	niches: ["generic"],
	priority: { generic: 1 },
};

describe("cvAdminClient", () => {
	it("Given los 10 upserts When se invocan Then cada uno responde Envelope con entity+id", async () => {
		// Arrange: un payload minimo con slug por upsert (profile usa handle).
		const upserts = [
			cvAdminClient.upsertExperience(EXPERIENCE),
			cvAdminClient.upsertProject({
				slug: "proj-test",
				name: "Proyecto",
				summary: { es: "a", en: "b" },
				status: "active",
				projectType: "web",
				stack: [],
				metrics: {},
				niches: ["generic"],
				priority: {},
			}),
			cvAdminClient.upsertEducation({
				slug: "edu-test",
				institution: "Uni",
				start: "2015",
				description: { es: "a", en: "b" },
			}),
			cvAdminClient.upsertCertificate({
				slug: "cert-test",
				title: "Cert",
				issuer: "AWS",
				date: "2024-01-01",
				url: "https://x.test",
			}),
			cvAdminClient.upsertAward({
				slug: "award-test",
				title: { es: "a", en: "b" },
				issuer: "Org",
				date: "2024-01",
				motivation: { es: "a", en: "b" },
			}),
			cvAdminClient.upsertLanguage({
				slug: "lang-test",
				name: { es: "Ingles", en: "English" },
				level: { es: "Avanzado", en: "Advanced" },
			}),
			cvAdminClient.upsertEndorsement({
				slug: "endo-test",
				name: "Persona",
				role: "CTO",
				relation: { es: "a", en: "b" },
				linkedin: "https://linkedin.test",
			}),
			cvAdminClient.upsertPublication({
				slug: "pub-test",
				title: "Post",
				platform: "Dev.to",
				url: "https://pub.test",
				date: "2024-02",
				summary: { es: "a", en: "b" },
			}),
			cvAdminClient.upsertSkillCategory({
				slug: "cat-test",
				name: { es: "a", en: "b" },
				kind: "technical",
				skills: ["Python"],
				niches: ["generic"],
			}),
		];

		// Act
		const results = await Promise.all(upserts);

		// Assert: cada upsert devuelve el slug como entity.
		expect(results.map((envelope) => envelope.data.entity)).toEqual([
			"exp-test",
			"proj-test",
			"edu-test",
			"cert-test",
			"award-test",
			"lang-test",
			"endo-test",
			"pub-test",
			"cat-test",
		]);
		expect(results.every((envelope) => envelope.is_valid)).toBe(true);
	});

	it("Given upsert-profile When se invoca Then responde entity=handle", async () => {
		// Arrange + Act
		const envelope = await cvAdminClient.upsertProfile({
			name: "Pablo",
			handle: "bypabloc",
			headline: { es: "a", en: "b" },
			summary: { es: "a", en: "b" },
			location: "Lima",
			contacts: {
				email: "owner@test.com",
				linkedin: "https://li.test",
				github: "https://gh.test",
			},
			avatarUrl: "https://cdn.test/a.webp",
			niches: ["generic"],
		});

		// Assert
		expect(envelope.data).toEqual({ entity: "bypabloc", id: "ent_01" });
	});

	it("Given los 9 deletes When se invocan Then cada uno responde deleted true", async () => {
		// Arrange
		const deletes = [
			cvAdminClient.deleteExperience({ slug: "exp-test" }),
			cvAdminClient.deleteProject({ slug: "proj-test" }),
			cvAdminClient.deleteEducation({ slug: "edu-test" }),
			cvAdminClient.deleteCertificate({ slug: "cert-test" }),
			cvAdminClient.deleteAward({ slug: "award-test" }),
			cvAdminClient.deleteLanguage({ slug: "lang-test" }),
			cvAdminClient.deleteEndorsement({ slug: "endo-test" }),
			cvAdminClient.deletePublication({ slug: "pub-test" }),
			cvAdminClient.deleteSkillCategory({ slug: "cat-test" }),
		];

		// Act
		const results = await Promise.all(deletes);

		// Assert
		expect(results.map((envelope) => envelope.data.deleted)).toEqual([
			true,
			true,
			true,
			true,
			true,
			true,
			true,
			true,
			true,
		]);
	});

	it("Given reorder When se invoca Then responde reordered con el largo de la lista", async () => {
		// Arrange + Act
		const envelope = await cvAdminClient.reorder({
			entity_type: "experience",
			niche: "generic",
			ordered_slugs: ["a", "b", "c"],
		});

		// Assert
		expect(envelope.data).toEqual({
			entity_type: "experience",
			niche: "generic",
			reordered: 3,
		});
	});

	it("Given catalogs When se invoca Then responde niches+skills+techTags", async () => {
		// Arrange + Act
		const envelope = await cvAdminClient.catalogs();

		// Assert
		expect(envelope.data.niches).toEqual(["generic", "vibe", "fintech"]);
		expect(envelope.data.skills).toEqual([
			{ slug: "python", name: "Python" },
			{ slug: "react", name: "React" },
			{ slug: "vue", name: "Vue" },
		]);
		expect(envelope.data.techTags).toEqual([
			{ slug: "astro", name: "Astro" },
			{ slug: "nextjs", name: "Next.js" },
		]);
	});

	it("Given get-all When se invoca Then responde las 10 claves del CV completo", async () => {
		// Arrange + Act
		const envelope = await cvAdminClient.getAll();

		// Assert: las 10 claves exactas del shape de edicion + datos sin
		// filtrar por niche.
		expect(Object.keys(envelope.data).sort()).toEqual([
			"awards",
			"certificates",
			"education",
			"endorsements",
			"experiences",
			"languages",
			"profile",
			"projects",
			"publications",
			"skills",
		]);
		expect(envelope.is_valid).toBe(true);
		expect(envelope.data.profile.handle).toBe("bypabloc");
		expect(envelope.data.experiences).toHaveLength(2);
		expect(envelope.data.projects).toHaveLength(1);
		expect(envelope.data.publications.map((pub) => pub.slug)).toEqual([
			"post-astro-portfolio",
			"post-lambda-coldstart",
		]);
		expect(envelope.data.skills).toEqual([]);
	});

	it("Given publish dispatch + status When se invocan Then responden run url y estado", async () => {
		// Arrange + Act
		const dispatch = await cvAdminClient.publishDispatch();
		const status = await cvAdminClient.publishStatus();

		// Assert
		expect(dispatch.data).toEqual({
			dispatched: true,
			ref: "dev",
			actions_url:
				"https://github.com/bypabloc/cv/actions/workflows/deploy-apps.yml",
		});
		expect(status.data).toEqual({
			status: "queued",
			conclusion: null,
			url: "https://github.com/bypabloc/cv/actions/runs/123",
			created_at: "2026-06-01T10:00:00Z",
			ref: "dev",
		});
	});

	it("Given upsertEntity/deleteEntity genericos When se despachan por seccion Then usan la action correcta", async () => {
		// Arrange
		const sections: CvEntitySectionKind[] = [
			"experiences",
			"projects",
			"education",
			"certificates",
			"awards",
			"languages",
			"endorsements",
			"publications",
			"skills",
		];

		// Act
		const upsert = await upsertEntity("experiences", EXPERIENCE);
		const deletes = await Promise.all(
			sections.map((section) => deleteEntity(section, { slug: "x-test" })),
		);

		// Assert
		expect(upsert.data).toEqual({ entity: "exp-test", id: "ent_01" });
		expect(deletes.every((envelope) => envelope.data.deleted === true)).toBe(
			true,
		);
	});
});
