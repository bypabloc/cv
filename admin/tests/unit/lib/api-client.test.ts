import { makeJwt, nowSec } from "@tests/mocks/jwt";
import { server } from "@tests/mocks/server";
import { HttpResponse, http } from "msw";
import { beforeEach, describe, expect, it } from "vitest";
import { useAuthStore } from "@/features/auth/store/use-auth-store";
import { ApiError, apiFetch } from "@/lib/api-client";

/**
 * @module tests/unit/lib/api-client
 * @description Verifica el mutex de refresh y el manejo de error de apiFetch.
 */

const API = "https://api.test.the-full-stack.com";

beforeEach(() => {
	useAuthStore.setState({
		accessToken: "expired-token",
		refreshToken: makeJwt({ sub: "usr_01", exp: nowSec() + 2_592_000 }),
	});
});

describe("apiFetch + mutex refresh", () => {
	it("Given 5 requests concurrentes con 401 When se procesan Then solo 1 /session/refresh se dispara", async () => {
		// Arrange
		let refreshCount = 0;
		server.use(
			http.get(`${API}/analytics`, () => {
				if (useAuthStore.getState().accessToken === "expired-token") {
					return new HttpResponse(null, { status: 401 });
				}
				return HttpResponse.json({
					is_valid: true,
					code: 0,
					data: { ok: true },
				});
			}),
			http.post(`${API}/auth`, async ({ request }) => {
				const body = (await request.json()) as {
					operation?: string;
					action?: string;
				};
				if (body.operation === "session" && body.action === "refresh") {
					refreshCount += 1;
					await new Promise((resolve) => setTimeout(resolve, 50));
					// Respuesta FLAT del backend (performRefresh lee json.access_token
					// directo, no .data.access_token).
					return HttpResponse.json({
						access_token: "fresh-token",
						refresh_token: makeJwt({
							sub: "usr_01",
							exp: nowSec() + 2_592_000,
						}),
						expires_in: 900,
					});
				}
				return new HttpResponse(null, { status: 501 });
			}),
		);

		// Act
		const results = await Promise.all([
			apiFetch("/analytics?operation=analytics&action=overview"),
			apiFetch("/analytics?operation=analytics&action=timeseries"),
			apiFetch("/analytics?operation=analytics&action=top-pages"),
			apiFetch("/analytics?operation=analytics&action=top-niches"),
			apiFetch("/analytics?operation=analytics&action=active-now"),
		]);

		// Assert
		expect(refreshCount).toBe(1);
		expect(results).toHaveLength(5);
		expect(useAuthStore.getState().accessToken).toBe("fresh-token");
	});

	it("Given un 401 y sin refresh token When apiFetch Then resetea y lanza ApiError 401", async () => {
		// Arrange
		useAuthStore.setState({ accessToken: "expired-token", refreshToken: null });
		server.use(
			http.get(
				`${API}/analytics`,
				() => new HttpResponse(null, { status: 401 }),
			),
		);

		// Act + Assert
		await expect(
			apiFetch("/analytics?operation=analytics&action=overview"),
		).rejects.toBeInstanceOf(ApiError);
		expect(useAuthStore.getState().accessToken).toBe(null);
	});

	it("Given un endpoint que responde error When apiFetch Then lanza ApiError con status y code del payload", async () => {
		// Arrange
		server.use(
			http.get(`${API}/analytics`, () =>
				HttpResponse.json(
					{ error: "BAD", code: 4001, message: "mal" },
					{ status: 400 },
				),
			),
		);

		// Act
		const error = await apiFetch(
			"/analytics?operation=analytics&action=overview",
			{ skipAuth: true },
		).catch((e: unknown) => e);

		// Assert
		expect(error).toBeInstanceOf(ApiError);
		expect((error as ApiError).status).toBe(400);
		expect((error as ApiError).code).toBe(4001);
		expect((error as ApiError).message).toBe("mal");
	});

	it("Given un body SIN operation/action When apiFetch Then NO lo aplana (viaja tal cual)", async () => {
		// Arrange: flattenBody solo aplana el shape {operation, action, data}.
		let capturedBody: Record<string, unknown> | null = null;
		server.use(
			http.post(`${API}/custom`, async ({ request }) => {
				capturedBody = (await request.json()) as Record<string, unknown>;
				return HttpResponse.json({ is_valid: true, code: 0, data: null });
			}),
		);

		// Act
		await apiFetch("/custom", {
			method: "POST",
			skipAuth: true,
			body: { foo: "bar" },
		});

		// Assert
		expect(capturedBody).toEqual({ foo: "bar" });
	});

	it("Given un body con data null When apiFetch Then aplana a {operation, action} sin campos", async () => {
		// Arrange: la rama data no-objeto de flattenBody cae a {}.
		let capturedBody: Record<string, unknown> | null = null;
		server.use(
			http.post(`${API}/custom`, async ({ request }) => {
				capturedBody = (await request.json()) as Record<string, unknown>;
				return HttpResponse.json({ is_valid: true, code: 0, data: null });
			}),
		);

		// Act
		await apiFetch("/custom", {
			method: "POST",
			skipAuth: true,
			body: { operation: "x", action: "y", data: null },
		});

		// Assert
		expect(capturedBody).toEqual({ operation: "x", action: "y" });
	});
});
