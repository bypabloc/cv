import { makeJwt } from "@tests/mocks/jwt";
import { beforeEach, describe, expect, it } from "vitest";
import { useAuthStore } from "@/features/auth/store/use-auth-store";
import { geoClient } from "@/features/geo/api/geo-client";

/**
 * @module tests/unit/features/geo/geo-client
 * @description geoClient.byCountry: hace GET /analytics?operation=geo&
 *   action=by-country via fetchMetric y devuelve el data. Usa el MSW handler
 *   de /analytics (fixture geo:by-country).
 */

beforeEach(() => {
	useAuthStore.setState({ accessToken: makeJwt({ sub: "usr_01" }) });
});

describe("geoClient.byCountry", () => {
	it("Given un rango valido When byCountry Then devuelve items + total del fixture", async () => {
		// Act
		const data = await geoClient.byCountry({
			from: "2026-04-27",
			to: "2026-05-27",
		});

		// Assert
		expect(data.total).toBe(30);
		expect(data.items).toHaveLength(1);
		expect(data.items[0]).toEqual({
			country: "AR",
			sessions: 30,
			visits: 40,
			events: 100,
		});
	});

	it("Given un limit explicito When byCountry Then sigue devolviendo el shape del fixture", async () => {
		// Act
		const data = await geoClient.byCountry({
			from: "2026-04-27",
			to: "2026-05-27",
			limit: 10,
		});

		// Assert
		expect(data.items[0]?.country).toBe("AR");
		expect(data.total).toBe(30);
	});
});
