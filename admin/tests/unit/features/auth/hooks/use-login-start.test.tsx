import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";
import { useLoginStart } from "@/features/auth/hooks/use-login-start";
import { useAuthStore } from "@/features/auth/store/use-auth-store";

/**
 * @module tests/unit/features/auth/hooks/use-login-start
 * @description Verifica login.start: email inexistente -> 200 con `created`
 *   (registro fusionado, ya NO 404) y email con MFA -> 200 con methods. Ambos
 *   setean el tempToken.
 */

vi.mock("next/navigation", () => ({
	useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
}));

function wrapper({ children }: { children: ReactNode }) {
	const client = new QueryClient({
		defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
	});
	return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

describe("useLoginStart", () => {
	it("Given email inexistente + precheck When mutate Then crea el user (created) y setea tempToken", async () => {
		// Arrange
		const { result } = renderHook(() => useLoginStart(), { wrapper });

		// Act: el precheckToken viaja en Authorization (no Turnstile). El alta
		// fusionada manda el email; el user existente NO (lo resuelve el precheck).
		const response = await act(async () =>
			result.current.mutateAsync({
				email: "unknown@test.com",
				precheckToken: "mock-precheck-token",
			}),
		);

		// Assert: el 404 EMAIL_NOT_FOUND ya NO ocurre; login.start crea el user.
		expect(response.data.created).toBe(true);
		expect(useAuthStore.getState().tempToken).toBe("mock-temp-created");
	});

	it("Given email con MFA + precheck When mutate Then setea tempToken y devuelve methods", async () => {
		// Arrange
		const { result } = renderHook(() => useLoginStart(), { wrapper });

		// Act
		const response = await act(async () =>
			result.current.mutateAsync({
				email: "mfa@test.com",
				precheckToken: "mock-precheck-token",
			}),
		);

		// Assert
		expect(response.data.methods).toEqual(["totp"]);
		expect(useAuthStore.getState().tempToken).toBe("mock-temp-mfa");
	});

	it("Given login.start SIN precheck When el header falta Then 401 MISSING_PRECHECK", async () => {
		// Arrange
		const { result } = renderHook(() => useLoginStart(), { wrapper });

		// Act / Assert: un precheck vacio -> Authorization sin Bearer -> 401.
		await expect(
			act(async () =>
				result.current.mutateAsync({
					email: "mfa@test.com",
					precheckToken: "",
				}),
			),
		).rejects.toMatchObject({ status: 401 });
	});
});
