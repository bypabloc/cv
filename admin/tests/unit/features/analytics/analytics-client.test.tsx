import { makeJwt } from "@tests/mocks/jwt";
import { beforeEach, describe, expect, it } from "vitest";
import { analyticsClient } from "@/features/analytics/api/analytics-client";
import { useAuthStore } from "@/features/auth/store/use-auth-store";

/**
 * @module tests/unit/features/analytics/analytics-client
 * @description analyticsClient: cada fn hace GET /analytics?operation=analytics
 *   &action=... via fetchMetric y devuelve el `data` desempaquetado del
 *   Envelope. Los asserts usan la data sintetica del MSW handler de metrics.
 */

const RANGE = { from: "2026-04-27", to: "2026-05-28" };

beforeEach(() => {
	useAuthStore.setState({ accessToken: makeJwt({ sub: "usr_01" }) });
});

describe("analyticsClient.overview", () => {
	it("Given un rango When overview Then devuelve los 7 KPIs del fixture", async () => {
		// Act
		const data = await analyticsClient.overview(RANGE);

		// Assert
		expect(data).toEqual({
			sessions: 100,
			visits: 80,
			events: 500,
			contacts: 5,
			unique_visitors: 75,
			avg_visit_duration_sec: 45.5,
			bounce_rate: 0.15,
			from: "2026-04-27",
			to: "2026-05-28",
		});
	});
});

describe("analyticsClient.timeseries", () => {
	it("Given un rango + bucket When timeseries Then devuelve bucket day + 2 puntos", async () => {
		// Act
		const data = await analyticsClient.timeseries({ ...RANGE, bucket: "day" });

		// Assert
		expect(data.bucket).toBe("day");
		expect(data.points).toEqual([
			{ timestamp: "2026-05-01", count: 10 },
			{ timestamp: "2026-05-02", count: 20 },
		]);
		expect(data.filters).toEqual({ niche: null, event_type: null });
	});
});

describe("analyticsClient.topPages", () => {
	it("Given un rango + limit When topPages Then devuelve el item del fixture", async () => {
		// Act
		const data = await analyticsClient.topPages({ ...RANGE, limit: 10 });

		// Assert
		expect(data.items).toEqual([
			{ page_path: "/", events: 50, unique_visitors: 30, unique_visits: 40 },
		]);
	});
});

describe("analyticsClient.topReferrers", () => {
	it("Given un rango When topReferrers Then devuelve referrers + UTM rankings", async () => {
		// Act
		const data = await analyticsClient.topReferrers(RANGE);

		// Assert
		expect(data.referrers).toEqual([
			{ referrer: "(direct)", visits: 40, unique_visitors: 30 },
		]);
		expect(data.utm_sources).toEqual([{ utm_source: "google", visits: 10 }]);
		expect(data.utm_mediums).toEqual([{ utm_medium: "cpc", visits: 5 }]);
		expect(data.utm_campaigns).toEqual([{ utm_campaign: "launch", visits: 3 }]);
	});
});

describe("analyticsClient.topNiches", () => {
	it("Given un rango When topNiches Then devuelve el ranking de niches", async () => {
		// Act
		const data = await analyticsClient.topNiches(RANGE);

		// Assert
		expect(data.items).toEqual([
			{ niche: "fintech", visits: 30, unique_visitors: 20 },
		]);
	});
});

describe("analyticsClient.activeNow", () => {
	it("Given sin params When activeNow Then devuelve el contador live", async () => {
		// Act
		const data = await analyticsClient.activeNow();

		// Assert
		expect(data).toEqual({
			active_sessions: 3,
			threshold_minutes: 5,
			as_of: "2026-05-28T12:00:00+00:00",
		});
	});
});

describe("analyticsClient.retention", () => {
	it("Given un rango When retention Then devuelve new vs returning", async () => {
		// Act
		const data = await analyticsClient.retention(RANGE);

		// Assert
		expect(data).toEqual({
			new_visitors: 60,
			returning_visitors: 15,
			total: 75,
			returning_rate: 0.2,
		});
	});
});
