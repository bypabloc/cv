import { renderHook, waitFor } from "@testing-library/react";
import { makeJwt, nowSec } from "@tests/mocks/jwt";
import { describe, expect, it, vi } from "vitest";
import { useProtectedRoute } from "@/features/auth/hooks/use-protected-route";
import { useAuthStore } from "@/features/auth/store/use-auth-store";

/**
 * @module tests/unit/features/auth/hooks/use-protected-route
 * @description Verifica el redirect a /login?next= sin sesion y el true con
 *   sesion vigente.
 */

const { replaceMock } = vi.hoisted(() => ({ replaceMock: vi.fn() }));
vi.mock("next/navigation", () => ({
	useRouter: () => ({ push: vi.fn(), replace: replaceMock }),
	usePathname: () => "/users",
}));

describe("useProtectedRoute", () => {
	it("Given sin sesion When se monta Then redirige a /login?next y devuelve false", async () => {
		// Act
		const { result } = renderHook(() => useProtectedRoute());

		// Assert
		expect(result.current).toBe(false);
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
