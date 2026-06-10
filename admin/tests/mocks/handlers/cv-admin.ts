import { HttpResponse, http } from "msw";

const API = "https://api.test.the-full-stack.com";

interface CvAdminBody {
	operation: string;
	action: string;
	[key: string]: unknown;
}

/**
 * @module tests/mocks/handlers/cv-admin
 * @description MSW handlers del dominio cv-management: POST /cv-admin
 *   (operations content + publish, contrato FLAT en el request + Envelope
 *   {is_valid, code, data} en la respuesta) y GET /cv publico (respuesta
 *   FLAT: el array/objeto de la seccion al nivel raiz) con fixtures.
 */

export const CV_PROFILE_FIXTURE = {
	name: "Pablo Contreras",
	handle: "bypabloc",
	headline: { es: "Full Stack Senior", en: "Senior Full Stack" },
	summary: { es: "Resumen es", en: "Summary en" },
	location: "Lima, Peru",
	contacts: {
		email: "owner@test.com",
		linkedin: "https://linkedin.com/in/bypabloc",
		github: "https://github.com/bypabloc",
	},
	avatarUrl: "https://cdn.test/avatar.webp",
	niches: ["generic"],
	stats: {
		yearsExperience: 10,
		companies: 5,
		countries: 3,
		certifications: 7,
	},
};

export const CV_EXPERIENCES_FIXTURE = [
	{
		slug: "destacame-architect",
		role: { es: "Arquitecto Frontend", en: "Frontend Architect" },
		company: "Destacame",
		country: "Chile",
		companyUrl: "https://destacame.cl",
		start: "2021-03",
		end: "2024-01",
		seniority: "senior",
		metricsEstimated: false,
		responsibilities: { es: ["Liderar equipo"], en: ["Lead team"] },
		achievements: { es: ["Reducir LCP"], en: ["Reduce LCP"] },
		skillsTechnical: ["Vue", "Python"],
		skillsSoft: ["Liderazgo"],
		niches: ["generic", "vibe"],
		priority: { generic: 5, vibe: 3 },
	},
	{
		slug: "acme-fullstack",
		role: { es: "Full Stack", en: "Full Stack" },
		company: "Acme",
		country: "Peru",
		start: "2024-02",
		seniority: "lead",
		metricsEstimated: true,
		responsibilities: { es: [], en: [] },
		achievements: { es: [], en: [] },
		skillsTechnical: ["Astro"],
		skillsSoft: [],
		niches: ["generic"],
		priority: { generic: 4 },
	},
];

export const CV_PROJECTS_FIXTURE = [
	{
		slug: "portfolio-monorepo",
		name: "Portfolio multi-niche",
		summary: { es: "Resumen es", en: "Summary en" },
		url: "https://the-full-stack.com",
		repo: "https://github.com/bypabloc/cv",
		links: [{ label: "Demo", url: "https://the-full-stack.com" }],
		status: "active",
		projectType: "web",
		isConfidential: false,
		metricsEstimated: true,
		stack: ["Astro", "Next.js"],
		caseStudy: { es: "Caso es", en: "Case en" },
		caseStudyDetailed: {
			problem: { es: "Problema", en: "Problem" },
			process: { es: "Proceso", en: "Process" },
			result: { es: "Resultado", en: "Result" },
		},
		metrics: { lighthouse: "100", visitors: "5k" },
		niches: ["generic"],
		priority: { generic: 4 },
	},
];

export const CV_CATALOGS_FIXTURE = {
	niches: ["generic", "vibe", "fintech"],
	skills: [
		{ slug: "python", name: "Python" },
		{ slug: "react", name: "React" },
		{ slug: "vue", name: "Vue" },
	],
	techTags: [
		{ slug: "astro", name: "Astro" },
		{ slug: "nextjs", name: "Next.js" },
	],
};

const EMPTY_SECTIONS = [
	"certificates",
	"awards",
	"education",
	"languages",
	"references",
	"skills",
];

function filterByNiche<T extends { niches?: string[] }>(
	items: T[],
	niche: string | null,
): T[] {
	if (!niche) return items;
	return items.filter((item) => (item.niches ?? []).includes(niche));
}

export const cvAdminHandlers = [
	http.get(`${API}/cv`, ({ request }) => {
		const url = new URL(request.url);
		const action = url.searchParams.get("action");
		const niche = url.searchParams.get("niche");

		if (action === "profile") {
			return HttpResponse.json(CV_PROFILE_FIXTURE);
		}
		if (action === "experiences") {
			return HttpResponse.json(filterByNiche(CV_EXPERIENCES_FIXTURE, niche));
		}
		if (action === "projects") {
			return HttpResponse.json(filterByNiche(CV_PROJECTS_FIXTURE, niche));
		}
		if (action !== null && EMPTY_SECTIONS.includes(action)) {
			return HttpResponse.json([]);
		}
		return HttpResponse.json(
			{ error: "UNKNOWN_ACTION", code: 1001 },
			{ status: 400 },
		);
	}),

	http.post(`${API}/cv-admin`, async ({ request }) => {
		const body = (await request.json()) as CvAdminBody;
		// Contrato FLAT del backend: campos al nivel raiz, no anidados en
		// `data`. `data` = todo menos operation/action.
		const { operation, action, ...data } = body;

		// --- operation publish ---
		if (operation === "publish" && action === "dispatch") {
			return HttpResponse.json({
				is_valid: true,
				code: 0,
				data: {
					dispatched: true,
					ref: "dev",
					actions_url:
						"https://github.com/bypabloc/cv/actions/workflows/deploy-apps.yml",
				},
			});
		}
		if (operation === "publish" && action === "status") {
			return HttpResponse.json({
				is_valid: true,
				code: 0,
				data: {
					status: "queued",
					conclusion: null,
					url: "https://github.com/bypabloc/cv/actions/runs/123",
					created_at: "2026-06-01T10:00:00Z",
					ref: "dev",
				},
			});
		}

		// --- operation content ---
		if (operation === "content" && action === "catalogs") {
			return HttpResponse.json({
				is_valid: true,
				code: 0,
				data: CV_CATALOGS_FIXTURE,
			});
		}
		if (operation === "content" && action === "reorder") {
			const orderedSlugs = data.ordered_slugs as string[];
			return HttpResponse.json({
				is_valid: true,
				code: 0,
				data: {
					entity_type: data.entity_type,
					niche: data.niche,
					reordered: orderedSlugs.length,
				},
			});
		}
		if (operation === "content" && action.startsWith("upsert-")) {
			const naturalKey = (data.slug ?? data.handle) as string;
			return HttpResponse.json({
				is_valid: true,
				code: 0,
				data: { entity: naturalKey, id: "ent_01" },
			});
		}
		if (operation === "content" && action.startsWith("delete-")) {
			return HttpResponse.json({
				is_valid: true,
				code: 0,
				data: { entity: data.slug, deleted: true },
			});
		}

		return HttpResponse.json(
			{ error: "NOT_IMPLEMENTED", code: 5010 },
			{ status: 501 },
		);
	}),
];
