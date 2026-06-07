import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import { server } from "@tests/mocks/server";
import { HttpResponse, http } from "msw";
import type { ReactNode } from "react";
import { describe, expect, it } from "vitest";
import { useIsAdmin } from "@/features/admin-shell/hooks/use-is-admin";

/**
 * @module tests/unit/features/admin-shell/hooks/use-is-admin
 * @description Sondeo del rol admin via users.admin.list-users. 200 -> admin;
 *   404 NOT_FOUND (anti-enumeration) -> no-admin (resuelve a false, NO error);
 *   otro error -> se propaga (isError).
 */

const API = "https://api.test.the-full-stack.com";

function wrapper({ children }: { children: ReactNode }) {
	const client = new QueryClient({
		defaultOptions: { queries: { retry: false } },
	});
	return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

describe("useIsAdmin", () => {
	it("Given el backend responde 200 a list-users When sondea Then isAdmin true", async () => {
		// Arrange: el MSW por defecto devuelve 200 con users.

		// Act
		const { result } = renderHook(() => useIsAdmin(), { wrapper });

		// Assert
		await waitFor(() => expect(result.current.isResolved).toBe(true));
		expect(result.current.isAdmin).toBe(true);
	});

	it("Given el backend responde 404 NOT_FOUND When sondea Then isAdmin false (no error)", async () => {
		// Arrange: simula no-admin
		server.use(
			http.post(`${API}/users`, () =>
				HttpResponse.json(
					{ error: "NOT_FOUND", code: "NOT_FOUND" },
					{ status: 404 },
				),
			),
		);

		// Act
		const { result } = renderHook(() => useIsAdmin(), { wrapper });

		// Assert
		await waitFor(() => expect(result.current.isResolved).toBe(true));
		expect(result.current.isAdmin).toBe(false);
	});

	it("Given un error 500 (no 404) When sondea Then NO resuelve a admin (isResolved false)", async () => {
		// Arrange
		server.use(
			http.post(`${API}/users`, () =>
				HttpResponse.json(
					{ error: "SERVER_ERROR", code: 5000 },
					{ status: 500 },
				),
			),
		);

		// Act
		const { result } = renderHook(() => useIsAdmin(), { wrapper });

		// Assert: el 500 se propaga -> la query queda en error, NO success
		await waitFor(() => expect(result.current.isResolved).toBe(false));
		expect(result.current.isAdmin).toBe(false);
	});
});
