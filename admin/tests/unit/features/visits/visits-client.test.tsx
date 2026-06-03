import { makeJwt } from "@tests/mocks/jwt";
import { beforeEach, describe, expect, it } from "vitest";
import { useAuthStore } from "@/features/auth/store/use-auth-store";
import { visitsClient } from "@/features/visits/api/visits-client";

/**
 * @module tests/unit/features/visits/visits-client
 * @description visitsClient.list y visitsClient.landingPages: cada fn hace
 *   `GET /analytics?operation=visits&action=...` via fetchMetric y devuelve el
 *   `data`. Usa el MSW handler de /analytics (tests/mocks/handlers/metrics).
 */

beforeEach(() => {
	useAuthStore.setState({ accessToken: makeJwt({ sub: "usr_01" }) });
});

describe("visitsClient.list", () => {
	it("Given un rango + paginacion When list Then devuelve la pagina de visitas", async () => {
		// Act
		const data = await visitsClient.list({
			from: "2026-04-27",
			to: "2026-05-28",
			page: 1,
			page_size: 20,
			offset: 0,
		});

		// Assert
		expect(data.total).toBe(1);
		expect(data.page).toBe(1);
		expect(data.page_size).toBe(20);
		expect(data.has_more).toBe(false);
		expect(data.items).toHaveLength(1);
	});

	it("Given el fixture de visits/list When list Then la fila tiene el shape esperado", async () => {
		// Act
		const data = await visitsClient.list({
			from: "2026-04-27",
			to: "2026-05-28",
		});

		// Assert
		const row = data.items[0];
		expect(row?.visit_id).toBe("vis_1");
		expect(row?.session_id).toBe("sess_1");
		expect(row?.started_at).toBe("2026-05-01T10:00:00Z");
		expect(row?.event_count).toBe(3);
		expect(row?.country).toBe("AR");
		expect(row?.referrer).toBe("(direct)");
		expect(row?.landing_page_path).toBe("/");
		expect(row?.niche).toBe("fintech");
	});
});

describe("visitsClient.landingPages", () => {
	it("Given un rango When landingPages Then devuelve el ranking de landing pages", async () => {
		// Act
		const data = await visitsClient.landingPages({
			from: "2026-04-27",
			to: "2026-05-28",
			limit: 10,
		});

		// Assert
		expect(data.items).toHaveLength(1);
		expect(data.items[0]?.landing_page_path).toBe("/");
		expect(data.items[0]?.visits).toBe(40);
		expect(data.items[0]?.unique_visitors).toBe(30);
	});
});
