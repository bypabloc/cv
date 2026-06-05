import { renderHook, waitFor } from "@testing-library/react";
import { makeJwt, nowSec } from "@tests/mocks/jwt";
import { server } from "@tests/mocks/server";
import { HttpResponse, http } from "msw";
import { beforeEach, describe, expect, it } from "vitest";
import { useSessionRehydrate } from "@/features/auth/hooks/use-session-rehydrate";
import { useAuthStore } from "@/features/auth/store/use-auth-store";

/**
 * @module tests/unit/features/auth/hooks/use-session-rehydrate
 * @description Lazy auth: al montar, si access===null pero hay un refresh
 *   vigente, hace UN refresh silencioso (bajo el mutex) para hidratar el access;
 *   en fallo resetea el store. Devuelve `rehydrating` (true mientras ese refresh
 *   inicial esta in-flight). Sin timer, sin visibility, sin validar el access.
 */

const API = "https://api.test.the-full-stack.com";

beforeEach(() => {
	useAuthStore.getState().reset();
});

describe("useSessionRehydrate", () => {
	it("Given access=null + refresh vigente When monta Then rehydrating=true al inicio, hace 1 refresh, setea access nuevo y rehydrating pasa a false", async () => {
		// Arrange: estado post-reload (access null, refresh persistido vigente).
		useAuthStore.setState({
			accessToken: null,
			refreshToken: makeJwt({ sub: "usr_01", exp: nowSec() + 2_592_000 }),
			refreshExpiry: (nowSec() + 2_592_000) * 1000,
		});

		// Act
		const { result } = renderHook(() => useSessionRehydrate());

		// Assert: arranca rehidratando; tras el refresh (MSW default) hidrata el
		// access y baja el flag.
		expect(result.current).toBe(true);
		await waitFor(() => {
			expect(result.current).toBe(false);
		});
		expect(useAuthStore.getState().accessToken).not.toBe(null);
	});

	it("Given access=null + SIN refresh token When monta Then rehydrating=false desde el inicio (no hace refresh)", async () => {
		// Arrange: sin refresh no hay nada que rehidratar.

		// Act
		const { result } = renderHook(() => useSessionRehydrate());

		// Assert
		expect(result.current).toBe(false);
		await waitFor(() => {
			expect(result.current).toBe(false);
		});
		expect(useAuthStore.getState().accessToken).toBe(null);
	});

	it("Given access=null + refresh EXPIRADO When monta Then rehydrating=false desde el inicio (no hace refresh)", async () => {
		// Arrange: refresh vencido -> no se rehidrata.
		useAuthStore.setState({
			accessToken: null,
			refreshToken: "expirado",
			refreshExpiry: Date.now() - 1000,
		});

		// Act
		const { result } = renderHook(() => useSessionRehydrate());

		// Assert
		expect(result.current).toBe(false);
		expect(useAuthStore.getState().accessToken).toBe(null);
	});

	it("Given access ya presente When monta Then rehydrating=false (no rehidrata)", async () => {
		// Arrange: access vivo en memoria (login en curso / multi-tab).
		const access = makeJwt({ sub: "usr_01", exp: nowSec() + 900 });
		useAuthStore.setState({
			accessToken: access,
			refreshToken: makeJwt({ sub: "usr_01", exp: nowSec() + 2_592_000 }),
			refreshExpiry: (nowSec() + 2_592_000) * 1000,
		});

		// Act
		const { result } = renderHook(() => useSessionRehydrate());

		// Assert: no rehidrata y conserva el access actual.
		expect(result.current).toBe(false);
		expect(useAuthStore.getState().accessToken).toBe(access);
	});

	it("Given refresh falla (401) When monta Then store.reset() y rehydrating=false", async () => {
		// Arrange: refresh vigente, pero el backend lo rechaza.
		useAuthStore.setState({
			accessToken: null,
			refreshToken: makeJwt({ sub: "usr_01", exp: nowSec() + 2_592_000 }),
			refreshExpiry: (nowSec() + 2_592_000) * 1000,
		});
		server.use(
			http.post(`${API}/auth`, () =>
				HttpResponse.json(
					{ error: "TOKEN_REUSE_DETECTED", code: 4011 },
					{ status: 401 },
				),
			),
		);

		// Act
		const { result } = renderHook(() => useSessionRehydrate());

		// Assert: arranca rehidratando; el fallo resetea el store y baja el flag.
		expect(result.current).toBe(true);
		await waitFor(() => {
			expect(result.current).toBe(false);
		});
		const state = useAuthStore.getState();
		expect(state.accessToken).toBe(null);
		expect(state.refreshToken).toBe(null);
	});
});
