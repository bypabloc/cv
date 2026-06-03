import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { makeJwt } from "@tests/mocks/jwt";
import { renderHook, waitFor } from "@tests/utils/render";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it } from "vitest";
import { useAuthStore } from "@/features/auth/store/use-auth-store";
import { useContactsByStatus } from "@/features/contacts/hooks/use-contacts-by-status";

/**
 * @module tests/unit/features/contacts/use-contacts-by-status
 * @description useContactsByStatus: desglose de contactos por estado
 *   (contacts/by-status). Desempaqueta el envelope del Lambda `analytics` y
 *   devuelve los items del fixture MSW.
 */

function makeWrapper() {
	const client = new QueryClient({
		defaultOptions: { queries: { retry: false, gcTime: 0 } },
	});
	return function Wrapper({ children }: { children: ReactNode }) {
		return (
			<QueryClientProvider client={client}>{children}</QueryClientProvider>
		);
	};
}

beforeEach(() => {
	useAuthStore.setState({ accessToken: makeJwt({ sub: "usr_01" }) });
});

describe("useContactsByStatus", () => {
	it("Given un rango valido When la query resuelve Then devuelve el desglose por estado", async () => {
		// Arrange + Act
		const { result } = renderHook(
			() => useContactsByStatus({ from: "2026-04-27", to: "2026-05-28" }),
			{ wrapper: makeWrapper() },
		);

		// Assert
		await waitFor(() => {
			expect(result.current.isSuccess).toBe(true);
		});
		expect(result.current.data?.items).toHaveLength(2);
		expect(result.current.data?.items[0]).toEqual({
			status: "new",
			count: 8,
			pct: 80.0,
		});
		expect(result.current.data?.items[1]).toEqual({
			status: "converted",
			count: 2,
			pct: 20.0,
		});
	});
});
