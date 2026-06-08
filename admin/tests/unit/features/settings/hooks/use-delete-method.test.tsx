import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import { server } from "@tests/mocks/server";
import { HttpResponse, http } from "msw";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";
import { useDeleteMethod } from "@/features/settings/hooks/use-delete-method";

/**
 * @module tests/unit/features/settings/hooks/use-delete-method
 * @description Cubre el hook que hace hard-delete de un metodo MFA via
 *   mfa.delete: el camino feliz (204) y el error 409 (MUST_KEEP_ONE) que
 *   muestra un toast sin invalidar.
 */

vi.mock("next/navigation", () => ({
	useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
}));

const API = "https://api.test.the-full-stack.com";

function wrapper({ children }: { children: ReactNode }) {
	const client = new QueryClient({
		defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
	});
	return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

describe("useDeleteMethod", () => {
	it("Given mfa.delete responde 204 When mutate Then la mutation queda success", async () => {
		// Arrange: el MSW por defecto responde 204 a mfa.delete.

		// Act
		const { result } = renderHook(() => useDeleteMethod(), { wrapper });
		result.current.mutate({ kind: "totp" });

		// Assert
		await waitFor(() => expect(result.current.isSuccess).toBe(true));
	});

	it("Given mfa.delete responde 409 When mutate Then la mutation queda error", async () => {
		// Arrange: override -> 409 MUST_KEEP_ONE_MFA_METHOD.
		server.use(
			http.post(`${API}/auth`, () =>
				HttpResponse.json(
					{
						error: "MUST_KEEP_ONE_MFA_METHOD",
						code: 4000,
						message: "Debes conservar al menos un metodo",
					},
					{ status: 409 },
				),
			),
		);

		// Act
		const { result } = renderHook(() => useDeleteMethod(), { wrapper });
		result.current.mutate({ kind: "totp" });

		// Assert
		await waitFor(() => expect(result.current.isError).toBe(true));
	});

	it("Given mfa.delete responde 500 When mutate Then la mutation queda error (rama no-409)", async () => {
		// Arrange: override -> 500 (cubre la rama del toast generico, no el 409).
		server.use(
			http.post(`${API}/auth`, () =>
				HttpResponse.json(
					{ error: "SERVER_ERROR", code: 5000, message: "fallo interno" },
					{ status: 500 },
				),
			),
		);

		// Act
		const { result } = renderHook(() => useDeleteMethod(), { wrapper });
		result.current.mutate({ kind: "email_code" });

		// Assert
		await waitFor(() => expect(result.current.isError).toBe(true));
	});
});
