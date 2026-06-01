import { renderHook, waitFor } from "@testing-library/react";
import { makeJwt, nowSec } from "@tests/mocks/jwt";
import { server } from "@tests/mocks/server";
import { HttpResponse, http } from "msw";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useAuthTimer } from "@/features/auth/hooks/use-auth-timer";
import { useAuthStore } from "@/features/auth/store/use-auth-store";

/**
 * @module tests/unit/features/auth/hooks/use-auth-timer-branches
 * @description Cubre las ramas faltantes de useAuthTimer: el catch de
 *   doRefresh (refresh falla -> reset), el callback del setTimeout, y la
 *   visibilidad con un access invalido (getJwtExpiry null -> reset).
 */

const API = "https://api.test.the-full-stack.com";

beforeEach(() => {
	useAuthStore.getState().reset();
});

afterEach(() => {
	vi.useRealTimers();
	vi.unstubAllGlobals();
});

function forceRefresh500() {
	server.use(
		http.post(`${API}/auth`, () =>
			HttpResponse.json({ error: "BOOM", code: 5000 }, { status: 500 }),
		),
	);
}

describe("useAuthTimer doRefresh falla", () => {
	it("Given un access casi vencido y refresh que falla When monta Then resetea (catch)", async () => {
		// Arrange: access dentro del lead -> refresh inmediato; el refresh da 500.
		forceRefresh500();
		useAuthStore.setState({
			accessToken: makeJwt({ sub: "usr_01", exp: nowSec() + 5 }),
			refreshToken: makeJwt({ sub: "usr_01", exp: nowSec() + 2_592_000 }),
			refreshExpiry: (nowSec() + 2_592_000) * 1000,
		});

		// Act
		renderHook(() => useAuthTimer());

		// Assert: el catch de doRefresh devuelve false -> reset()
		await waitFor(() => {
			expect(useAuthStore.getState().accessToken).toBe(null);
		});
	});

	it("Given bootstrap con refresh que falla When monta Then resetea", async () => {
		// Arrange: access null + refresh vigente -> bootstrap dispara refresh (falla)
		forceRefresh500();
		useAuthStore.setState({
			accessToken: null,
			refreshToken: makeJwt({ sub: "usr_01", exp: nowSec() + 2_592_000 }),
			refreshExpiry: (nowSec() + 2_592_000) * 1000,
		});

		// Act
		renderHook(() => useAuthTimer());

		// Assert
		await waitFor(() => {
			expect(useAuthStore.getState().refreshToken).toBe(null);
		});
	});
});

describe("useAuthTimer setTimeout programado", () => {
	it("Given un access lejos del lead When vence el timer Then refresca (callback)", async () => {
		// Arrange: fake timers; access vence en ~31s -> msUntilRefresh ~1s > 0
		vi.useFakeTimers();
		const access = makeJwt({ sub: "usr_01", exp: nowSec() + 31 });
		useAuthStore.setState({
			accessToken: access,
			refreshToken: makeJwt({ sub: "usr_01", exp: nowSec() + 2_592_000 }),
			refreshExpiry: (nowSec() + 2_592_000) * 1000,
		});
		renderHook(() => useAuthTimer());

		// Act: avanzar el reloj para disparar el setTimeout (lineas 81-82)
		await vi.advanceTimersByTimeAsync(2000);

		// Assert: el access se rota (el MSW default responde 200)
		expect(useAuthStore.getState().accessToken).not.toBe(access);
	});
});

describe("useAuthTimer visibility con access invalido", () => {
	it("Given un access invalido al volver el foco When visible Then resetea", async () => {
		// Arrange: monta con un access valido (no dispara reset inmediato), luego
		// lo cambia a invalido y simula el foco -> getJwtExpiry null -> reset.
		useAuthStore.setState({
			accessToken: makeJwt({ sub: "usr_01", exp: nowSec() + 3600 }),
			refreshToken: makeJwt({ sub: "usr_01", exp: nowSec() + 2_592_000 }),
			refreshExpiry: (nowSec() + 2_592_000) * 1000,
		});
		renderHook(() => useAuthTimer());
		useAuthStore.setState({ accessToken: "not-a-jwt" });
		Object.defineProperty(document, "visibilityState", {
			configurable: true,
			get: () => "visible",
		});

		// Act
		document.dispatchEvent(new Event("visibilitychange"));

		// Assert
		await waitFor(() => {
			expect(useAuthStore.getState().accessToken).toBe(null);
		});
	});

	it("Given foco con la tab oculta When visibilitychange Then no hace nada", () => {
		// Arrange
		useAuthStore.setState({
			accessToken: makeJwt({ sub: "usr_01", exp: nowSec() + 3600 }),
		});
		renderHook(() => useAuthTimer());
		Object.defineProperty(document, "visibilityState", {
			configurable: true,
			get: () => "hidden",
		});
		const before = useAuthStore.getState().accessToken;

		// Act: rama `visibilityState !== 'visible'` -> return temprano
		document.dispatchEvent(new Event("visibilitychange"));

		// Assert
		expect(useAuthStore.getState().accessToken).toBe(before);
	});
});
