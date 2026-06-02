import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";
import { useLoginStart } from "@/features/auth/hooks/use-login-start";
import { useAuthStore } from "@/features/auth/store/use-auth-store";
import { ApiError } from "@/lib/api-client";

/**
 * @module tests/unit/features/auth/hooks/use-login-start
 * @description Verifica login.start: 404 EMAIL_NOT_FOUND (suggest_register) y
 *   200 con methods (setea tempToken).
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
	it("Given email inexistente When mutate Then lanza ApiError 404 con suggest_register", async () => {
		// Arrange
		const { result } = renderHook(() => useLoginStart(), { wrapper });

		// Act
		const error = await act(async () =>
			result.current
				.mutateAsync({
					email: "unknown@test.com",
					cf_turnstile_response: "tok",
				})
				.catch((e: unknown) => e),
		);

		// Assert
		expect(error).toBeInstanceOf(ApiError);
		expect((error as ApiError).status).toBe(404);
		// Error FLAT del backend: suggest_register al nivel raiz de error.data.
		const data = (error as ApiError).data as {
			suggest_register?: boolean;
		};
		expect(data.suggest_register).toBe(true);
		expect(useAuthStore.getState().tempToken).toBe(null);
	});

	it("Given email con MFA When mutate Then setea tempToken y devuelve methods", async () => {
		// Arrange
		const { result } = renderHook(() => useLoginStart(), { wrapper });

		// Act
		const response = await act(async () =>
			result.current.mutateAsync({
				email: "mfa@test.com",
				cf_turnstile_response: "tok",
			}),
		);

		// Assert
		expect(response.data.methods).toEqual(["totp"]);
		expect(useAuthStore.getState().tempToken).toBe("mock-temp-mfa");
	});
});
