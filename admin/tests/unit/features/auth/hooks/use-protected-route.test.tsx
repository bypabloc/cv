import { renderHook, waitFor } from "@testing-library/react";
import { makeJwt, nowSec } from "@tests/mocks/jwt";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useProtectedRoute } from "@/features/auth/hooks/use-protected-route";
import { useAuthStore } from "@/features/auth/store/use-auth-store";

/**
 * @module tests/unit/features/auth/hooks/use-protected-route
 * @description Lazy auth: el hook recibe `rehydrating` por parametro. NO redirige
 *   mientras `rehydrating` (el refresh-en-reload aun puede hidratar el access);
 *   redirige a /login?next= sin sesion una vez resuelto; true con sesion vigente.
 */

const { replaceMock } = vi.hoisted(() => ({ replaceMock: vi.fn() }));
vi.mock("next/navigation", () => ({
	useRouter: () => ({ push: vi.fn(), replace: replaceMock }),
	usePathname: () => "/users",
}));

beforeEach(() => {
	replaceMock.mockClear();
	useAuthStore.getState().reset();
});

describe("useProtectedRoute", () => {
	it("Given rehydrating=true sin sesion When se monta Then NO redirige (espera el refresh)", async () => {
		// Arrange: primer render post-reload (access aun no hidratado), el
		// refresh-en-reload todavia esta in-flight.

		// Act
		const { result } = renderHook(() => useProtectedRoute(true));

		// Assert: retiene el redirect mientras el rehydrate esta en curso.
		expect(result.current).toBe(false);
		await waitFor(() => {
			expect(replaceMock).not.toHaveBeenCalled();
		});
	});

	it("Given rehydrating=false sin sesion When se monta Then redirige a /login?next y devuelve false", async () => {
		// Act
		const { result } = renderHook(() => useProtectedRoute(false));

		// Assert
		expect(result.current).toBe(false);
		await waitFor(() => {
			expect(replaceMock).toHaveBeenCalledWith("/login?next=%2Fusers");
		});
	});

	it("Given sesion vigente When se monta Then devuelve true y NO redirige", () => {
		// Arrange
		useAuthStore.setState({
			accessToken: makeJwt({ sub: "usr_01", exp: nowSec() + 900 }),
			user: {
				id: "usr_01",
				email: "u@t.com",
				status: "active",
				has_password: false,
				mfa_methods: [],
			},
		});

		// Act
		const { result } = renderHook(() => useProtectedRoute(false));

		// Assert
		expect(result.current).toBe(true);
		expect(replaceMock).not.toHaveBeenCalled();
	});

	it("Given un access EXPIRADO When se monta Then authed=false y redirige", async () => {
		// Arrange: access presente pero vencido -> no autenticado.
		useAuthStore.setState({
			accessToken: makeJwt({ sub: "usr_01", exp: nowSec() - 10 }),
		});

		// Act
		const { result } = renderHook(() => useProtectedRoute(false));

		// Assert
		expect(result.current).toBe(false);
		await waitFor(() => {
			expect(replaceMock).toHaveBeenCalledWith("/login?next=%2Fusers");
		});
	});

	it("Given monta con rehydrating=true y luego se hidrata el access When cambia el store Then authed pasa a true reactivamente (sin user)", async () => {
		// Arrange: estado post-reload (rehydrating, sin access). authed se DERIVA
		// del accessToken reactivo, no de la fn estable: asi el hook re-renderiza
		// cuando el refresh-en-reload hidrata el access.
		useAuthStore.setState({
			accessToken: null,
			refreshToken: makeJwt({ sub: "usr_01", exp: nowSec() + 2_592_000 }),
			refreshExpiry: (nowSec() + 2_592_000) * 1000,
		});
		const { result, rerender } = renderHook(
			({ rehydrating }: { rehydrating: boolean }) =>
				useProtectedRoute(rehydrating),
			{ initialProps: { rehydrating: true } },
		);
		expect(result.current).toBe(false);

		// Act: el refresh-en-reload hidrata el access y baja rehydrating.
		useAuthStore
			.getState()
			.setAccessToken(makeJwt({ sub: "usr_01", exp: nowSec() + 900 }));
		rerender({ rehydrating: false });

		// Assert: authed reactivo pasa a true; no redirige.
		await waitFor(() => {
			expect(result.current).toBe(true);
		});
		expect(replaceMock).not.toHaveBeenCalled();
	});
});
