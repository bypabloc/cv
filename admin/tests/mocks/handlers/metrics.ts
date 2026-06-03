import { HttpResponse, http } from "msw";

/**
 * @module tests/mocks/handlers/metrics
 * @description MSW handler del Lambda `analytics` (`GET /analytics?operation=
 *   ...&action=...`). Responde un payload FLAT por (operation, action) — el
 *   api-client lo re-envuelve en `{is_valid, code, data}`. Cubre las 20 actions
 *   de las 8 features de metricas con data sintetica determinista (incluye
 *   `analytics:dashboard`, que combina las 7 vistas del overview).
 */

const API = "https://api.test.the-full-stack.com";

const FIXTURES: Record<string, Record<string, unknown>> = {
	"analytics:overview": {
		sessions: 100,
		visits: 80,
		events: 500,
		contacts: 5,
		unique_visitors: 75,
		avg_visit_duration_sec: 45.5,
		bounce_rate: 0.15,
		from: "2026-04-27",
		to: "2026-05-28",
	},
	"analytics:timeseries": {
		bucket: "day",
		points: [
			{ timestamp: "2026-05-01", count: 10 },
			{ timestamp: "2026-05-02", count: 20 },
		],
		from: "2026-04-27",
		to: "2026-05-28",
		filters: { niche: null, event_type: null },
	},
	"analytics:top-pages": {
		items: [
			{ page_path: "/", events: 50, unique_visitors: 30, unique_visits: 40 },
		],
	},
	"analytics:top-referrers": {
		referrers: [{ referrer: "(direct)", visits: 40, unique_visitors: 30 }],
		utm_sources: [{ utm_source: "google", visits: 10 }],
		utm_mediums: [{ utm_medium: "cpc", visits: 5 }],
		utm_campaigns: [{ utm_campaign: "launch", visits: 3 }],
	},
	"analytics:top-niches": {
		items: [{ niche: "fintech", visits: 30, unique_visitors: 20 }],
	},
	"analytics:active-now": {
		active_sessions: 3,
		threshold_minutes: 5,
		as_of: "2026-05-28T12:00:00+00:00",
	},
	"analytics:retention": {
		new_visitors: 60,
		returning_visitors: 15,
		total: 75,
		returning_rate: 0.2,
	},
	"events:distribution": {
		items: [
			{ event_type: "page_view", count: 300, pct: 60.0 },
			{ event_type: "click", count: 200, pct: 40.0 },
		],
	},
	"events:list": {
		items: [
			{
				created_at: "2026-05-20T10:00:00Z",
				visit_id: "vis_1",
				page_id: "pg_1",
				session_id: "sess_1",
				page_path: "/",
				niche: "fintech",
				viewport_width: 1920,
				viewport_height: 1080,
				event_type: "page_view",
				event_props: {},
			},
		],
		page: 1,
		page_size: 50,
		total: 1,
		has_more: false,
	},
	"events:heatmap": {
		cells: [
			{ dow: 1, hour: 9, count: 12 },
			{ dow: 3, hour: 14, count: 8 },
		],
	},
	"sessions:list": {
		items: [
			{
				session_id: "sess_1",
				first_seen_at: "2026-05-01T10:00:00Z",
				last_seen_at: "2026-05-20T10:00:00Z",
				browser: "Chrome",
				browser_version: "120",
				os: "Linux",
				device_type: "desktop",
				visits_count: 4,
			},
		],
		page: 1,
		page_size: 20,
		total: 1,
		has_more: false,
	},
	"sessions:detail": {
		session: {
			session_id: "sess_1",
			first_seen_at: "2026-05-01T10:00:00Z",
			last_seen_at: "2026-05-20T10:00:00Z",
			browser: "Chrome",
			browser_version: "120",
			os: "Linux",
			device_type: "desktop",
			visits_count: 2,
		},
		visits: [
			{
				visit_id: "vis_1",
				started_at: "2026-05-01T10:00:00Z",
				ended_at: "2026-05-01T10:05:00Z",
				event_count: 3,
				ip: "1.2.3.4",
				country: "AR",
				utm_source: null,
				utm_medium: null,
				utm_campaign: null,
				referrer: null,
				landing_page_path: "/",
				niche: "fintech",
			},
		],
		events_count: 6,
	},
	"visits:list": {
		items: [
			{
				visit_id: "vis_1",
				session_id: "sess_1",
				started_at: "2026-05-01T10:00:00Z",
				ended_at: "2026-05-01T10:05:00Z",
				event_count: 3,
				ip: "1.2.3.4",
				country: "AR",
				utm_source: null,
				utm_medium: null,
				utm_campaign: null,
				referrer: "(direct)",
				landing_page_path: "/",
				niche: "fintech",
			},
		],
		page: 1,
		page_size: 20,
		total: 1,
		has_more: false,
	},
	"visits:landing-pages": {
		items: [{ landing_page_path: "/", visits: 40, unique_visitors: 30 }],
	},
	"geo:by-country": {
		items: [{ country: "AR", sessions: 30, visits: 40, events: 100 }],
		total: 30,
	},
	"devices:breakdown": {
		device_types: [{ device_type: "desktop", sessions: 50 }],
		browsers: [{ browser: "Chrome", sessions: 40 }],
		os: [{ os: "Linux", sessions: 35 }],
	},
	"funnel:conversion": {
		sessions: 100,
		visits: 80,
		contacts: 5,
		session_to_visit_rate: 0.8,
		visit_to_contact_rate: 0.063,
		session_to_contact_rate: 0.05,
	},
	"contacts:list": {
		items: [
			{
				id: "ct_1",
				created_at: "2026-05-20T10:00:00Z",
				name: "Ada",
				email: "ada@example.com",
				message: "Hola",
				company: "Acme",
				role: "CTO",
				service_type: "consulting",
				budget: "10k",
				timeline: "Q3",
				niche: "fintech",
				status: "new",
				session_id: "sess_1",
			},
		],
		page: 1,
		page_size: 50,
		total: 1,
		has_more: false,
	},
	"contacts:by-status": {
		items: [
			{ status: "new", count: 8, pct: 80.0 },
			{ status: "converted", count: 2, pct: 20.0 },
		],
	},
};

// La action `dashboard` combina las 7 vistas del overview en un solo payload
// (cada clave reusa el fixture homonimo, para que dashboard y las granulares
// no diverjan).
FIXTURES["analytics:dashboard"] = {
	overview: FIXTURES["analytics:overview"],
	timeseries: FIXTURES["analytics:timeseries"],
	top_pages: FIXTURES["analytics:top-pages"],
	top_referrers: FIXTURES["analytics:top-referrers"],
	top_niches: FIXTURES["analytics:top-niches"],
	active_now: FIXTURES["analytics:active-now"],
	retention: FIXTURES["analytics:retention"],
};

export const metricsHandlers = [
	http.get(`${API}/analytics`, ({ request }) => {
		const url = new URL(request.url);
		const operation = url.searchParams.get("operation") ?? "";
		const action = url.searchParams.get("action") ?? "";
		const fixture = FIXTURES[`${operation}:${action}`];
		if (fixture === undefined) {
			return HttpResponse.json(
				{ error: "unknown", code: 1000 },
				{ status: 400 },
			);
		}
		return HttpResponse.json(fixture, { status: 200 });
	}),
];
