import { makeJwt } from "@tests/mocks/jwt";
import { beforeEach, describe, expect, it } from "vitest";
import { useAuthStore } from "@/features/auth/store/use-auth-store";
import { funnelClient } from "@/features/funnel/api/funnel-client";

/**
 * @module tests/unit/features/funnel/funnel-client
 * @description funnelClient.conversion: hace GET /analytics?operation=funnel&
 *   action=conversion via fetchMetric y devuelve el data. Usa el MSW handler
 *   de /analytics (fixture funnel:conversion).
 */

beforeEach(() => {
	useAuthStore.setState({ accessToken: makeJwt({ sub: "usr_01" }) });
});

describe("funnelClient.conversion", () => {
	it("Given un rango valido When conversion Then devuelve el embudo del fixture", async () => {
		// Act
		const data = await funnelClient.conversion({
			from: "2026-04-27",
			to: "2026-05-27",
		});

		// Assert
		expect(data).toEqual({
			sessions: 100,
			visits: 80,
			contacts: 5,
			session_to_visit_rate: 0.8,
			visit_to_contact_rate: 0.063,
			session_to_contact_rate: 0.05,
		});
	});

	it("Given params vacios When conversion Then sigue devolviendo el shape del fixture", async () => {
		// Act
		const data = await funnelClient.conversion({});

		// Assert
		expect(data.sessions).toBe(100);
		expect(data.session_to_contact_rate).toBe(0.05);
	});
});
