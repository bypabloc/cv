import { makeJwt } from "@tests/mocks/jwt";
import { server } from "@tests/mocks/server";
import { HttpResponse, http } from "msw";
import { beforeEach, describe, expect, it } from "vitest";
import { useAuthStore } from "@/features/auth/store/use-auth-store";
import { sessionsClient } from "@/features/sessions/api/sessions-client";

/**
 * @module tests/unit/features/sessions/sessions-client
 * @description sessionsClient.list y .detail: GET /analytics?operation=sessions
 *   &action=... via fetchMetric (Bearer + envelope) y devuelven el `data`. Los
 *   asserts usan el fixture MSW (tests/mocks/handlers/metrics).
 */

const API = "https://api.test.the-full-stack.com";

beforeEach(() => {
	useAuthStore.setState({ accessToken: makeJwt({ sub: "usr_01" }) });
});

describe("sessionsClient.list", () => {
	it("Given params validos When list Then devuelve el listado paginado del fixture", async () => {
		// Act
		const data = await sessionsClient.list({
			from: "2026-05-01",
			to: "2026-05-28",
			page: 1,
			page_size: 20,
		});

		// Assert
		expect(data.total).toBe(1);
		expect(data.page).toBe(1);
		expect(data.page_size).toBe(20);
		expect(data.has_more).toBe(false);
		expect(data.items).toHaveLength(1);
		expect(data.items[0]?.session_id).toBe("sess_1");
		expect(data.items[0]?.browser).toBe("Chrome");
		expect(data.items[0]?.visits_count).toBe(4);
	});

	it("Given operation+action=sessions:list When list Then llama el endpoint con esos query params", async () => {
		// Arrange: captura los query params que recibe el handler
		let captured: { operation: string | null; action: string | null } = {
			operation: null,
			action: null,
		};
		server.use(
			http.get(`${API}/analytics`, ({ request }) => {
				const url = new URL(request.url);
				captured = {
					operation: url.searchParams.get("operation"),
					action: url.searchParams.get("action"),
				};
				return HttpResponse.json(
					{ items: [], page: 2, page_size: 20, total: 0, has_more: false },
					{ status: 200 },
				);
			}),
		);

		// Act
		const data = await sessionsClient.list({ page: 2, device_type: "mobile" });

		// Assert
		expect(captured.operation).toBe("sessions");
		expect(captured.action).toBe("list");
		expect(data.page).toBe(2);
	});
});

describe("sessionsClient.detail", () => {
	it("Given un session_id When detail Then devuelve sesion + visitas + events_count del fixture", async () => {
		// Act
		const data = await sessionsClient.detail({ session_id: "sess_1" });

		// Assert
		expect(data.session.session_id).toBe("sess_1");
		expect(data.session.visits_count).toBe(2);
		expect(data.events_count).toBe(6);
		expect(data.visits).toHaveLength(1);
		expect(data.visits[0]?.visit_id).toBe("vis_1");
		expect(data.visits[0]?.country).toBe("AR");
	});
});
