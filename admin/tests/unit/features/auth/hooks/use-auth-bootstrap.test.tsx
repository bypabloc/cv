import { renderHook } from "@testing-library/react";
import { makeJwt, nowSec } from "@tests/mocks/jwt";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useAuthBootstrap } from "@/features/auth/hooks/use-auth-bootstrap";
import { useAuthStore } from "@/features/auth/store/use-auth-store";

/**
 * @module tests/unit/features/auth/hooks/use-auth-bootstrap
 * @description Verifica el gate de hidratacion: con refresh vigente deja el
 *   flag (lo cierra useAuthTimer); sin refresh o con access ya presente lo
 *   apaga para permitir el redirect/render.
 */

beforeEach(() => {
	useAuthStore.getState().reset();
	useAuthStore.getState().setBootstrapping(true);
});

describe("useAuthBootstrap", () => {
	it("Given refresh vigente y access null When monta Then DEJA bootstrapping=true (lo cierra useAuthTimer)", () => {
		// Arrange
		useAuthStore.setState({
			accessToken: null,
			refreshToken: makeJwt({ sub: "usr_01", exp: nowSec() + 2_592_000 }),
			refreshExpiry: (nowSec() + 2_592_000) * 1000,
		});

		// Act
		renderHook(() => useAuthBootstrap());

		// Assert: hay algo que hidratar -> no apaga el flag.
		expect(useAuthStore.getState().bootstrapping).toBe(true);
	});

	it("Given sin refresh token When monta Then apaga bootstrapping (permite redirect)", () => {
		// Arrange: estado inicial (sin refresh) ya seteado por beforeEach.

		// Act
		renderHook(() => useAuthBootstrap());

		// Assert
		expect(useAuthStore.getState().bootstrapping).toBe(false);
	});

	it("Given refresh expirado When monta Then apaga bootstrapping", () => {
		// Arrange
		useAuthStore.setState({
			accessToken: null,
			refreshToken: "dead",
			refreshExpiry: Date.now() - 1000,
		});

		// Act
		renderHook(() => useAuthBootstrap());

		// Assert
		expect(useAuthStore.getState().bootstrapping).toBe(false);
	});

	it("Given access ya presente When monta Then apaga bootstrapping (sesion en curso)", () => {
		// Arrange
		useAuthStore.setState({
			accessToken: makeJwt({ sub: "usr_01", exp: nowSec() + 900 }),
			refreshToken: makeJwt({ sub: "usr_01", exp: nowSec() + 2_592_000 }),
			refreshExpiry: (nowSec() + 2_592_000) * 1000,
		});

		// Act
		renderHook(() => useAuthBootstrap());

		// Assert
		expect(useAuthStore.getState().bootstrapping).toBe(false);
	});

	it("Given storage aun no hidratado When termina la hidratacion Then resuelve (path onFinishHydration)", () => {
		// Arrange: simula un storage async (hasHydrated=false en el mount) y
		// captura el callback que el hook suscribe.
		let onFinish: (() => void) | null = null;
		const persist = useAuthStore.persist;
		const hasHydratedSpy = vi
			.spyOn(persist, "hasHydrated")
			.mockReturnValue(false);
		const onFinishSpy = vi
			.spyOn(persist, "onFinishHydration")
			.mockImplementation((cb) => {
				onFinish = cb as () => void;
				return () => {};
			});

		try {
			// Act: monta -> suscribe (no apaga aun), luego dispara la hidratacion.
			renderHook(() => useAuthBootstrap());
			expect(onFinish).not.toBe(null);
			expect(useAuthStore.getState().bootstrapping).toBe(true);
			(onFinish as unknown as () => void)();

			// Assert: sin refresh -> apaga el flag tras hidratar.
			expect(useAuthStore.getState().bootstrapping).toBe(false);
		} finally {
			hasHydratedSpy.mockRestore();
			onFinishSpy.mockRestore();
		}
	});
});
