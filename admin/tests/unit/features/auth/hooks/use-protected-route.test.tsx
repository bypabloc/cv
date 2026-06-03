import { renderHook, waitFor } from "@testing-library/react";
import { makeJwt, nowSec } from "@tests/mocks/jwt";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useProtectedRoute } from "@/features/auth/hooks/use-protected-route";
import { useAuthStore } from "@/features/auth/store/use-auth-store";

/**
 * @module tests/unit/features/auth/hooks/use-protected-route
 * @description Verifica que NO redirige mientras `bootstrapping` (gate del fix
 *   de persistencia de sesion), el redirect a /login?next= sin sesion una vez
 *   resuelto el bootstrap, y el true con sesion vigente.
 */

const { replaceMock } = vi.hoisted(() => ({ replaceMock: vi.fn() }));
vi.mock("next/navigation", () => ({
	useRouter: () => ({ push: vi.fn(), replace: replaceMock }),
	usePathname: () => "/users",
}));

beforeEach(() => {
	replaceMock.mockClear();
	useAuthStore.getState().reset();
	useAuthStore.getState().setBootstrapping(false);
});

describe("useProtectedRoute", () => {
	it("Given bootstrapping=true sin sesion When se monta Then NO redirige (espera el refresh)", async () => {
		// Arrange: simula el primer render post-reload (access aun no hidratado).
		useAuthStore.getState().setBootstrapping(true);

		// Act
		const { result } = renderHook(() => useProtectedRoute());

		// Assert: retiene el redirect mientras el bootstrap esta en curso.
		expect(result.current).toBe(false);
		await waitFor(() => {
			expect(replaceMock).not.toHaveBeenCalled();
		});
	});

	it("Given bootstrap resuelto sin sesion When se monta Then redirige a /login?next y devuelve false", async () => {
		// Act
		const { result } = renderHook(() => useProtectedRoute());

		// Assert
		expect(result.current).toBe(false);
		await waitFor(() => {
			expect(replaceMock).toHaveBeenCalledWith("/login?next=%2Fusers");
		});
	});

	it("Given bootstrap resuelto, sin access pero CON refresh vigente When se monta Then NO redirige (sesion recuperable)", async () => {
		// Arrange: la ventana de la race -> bootstrapping ya en false (commit
		// distinto al de setAccessToken) pero hay un refresh vivo: el bootstrap
		// aun puede hidratar el access. NO se debe redirigir.
		useAuthStore.setState({
			accessToken: null,
			refreshToken: makeJwt({ sub: "usr_01", exp: nowSec() + 2_592_000 }),
			refreshExpiry: (nowSec() + 2_592_000) * 1000,
		});

		// Act
		const { result } = renderHook(() => useProtectedRoute());

		// Assert
		expect(result.current).toBe(false);
		await waitFor(() => {
			expect(replaceMock).not.toHaveBeenCalled();
		});
	});

	it("Given bootstrap resuelto, sin access y con refresh EXPIRADO When se monta Then redirige (no recuperable)", async () => {
		// Arrange: refresh vencido -> no recuperable -> redirige.
		useAuthStore.setState({
			accessToken: null,
			refreshToken: "expirado",
			refreshExpiry: Date.now() - 1000,
		});

		// Act
		renderHook(() => useProtectedRoute());

		// Assert
		await waitFor(() => {
			expect(replaceMock).toHaveBeenCalledWith("/login?next=%2Fusers");
		});
	});

	it("Given sesion vigente When se monta Then devuelve true", () => {
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
		const { result } = renderHook(() => useProtectedRoute());

		// Assert
		expect(result.current).toBe(true);
	});
});
