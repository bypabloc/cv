import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { makeJwt } from "@tests/mocks/jwt";
import { renderHook, waitFor } from "@tests/utils/render";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it } from "vitest";
import { useAuthStore } from "@/features/auth/store/use-auth-store";
import { useDistribution } from "@/features/events/hooks/use-distribution";

/**
 * @module tests/unit/features/events/use-distribution
 * @description useDistribution: ranking de tipos de evento (events/distribution).
 *   Desempaqueta el envelope y devuelve { items } del fixture MSW.
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

describe("useDistribution", () => {
	it("Given un rango valido When la query resuelve Then devuelve el ranking del fixture", async () => {
		// Arrange + Act
		const { result } = renderHook(
			() => useDistribution({ from: "2026-04-27", to: "2026-05-28" }),
			{ wrapper: makeWrapper() },
		);

		// Assert
		await waitFor(() => {
			expect(result.current.isSuccess).toBe(true);
		});
		expect(result.current.data?.items).toHaveLength(2);
		expect(result.current.data?.items[0]?.event_type).toBe("page_view");
		expect(result.current.data?.items[0]?.count).toBe(300);
		expect(result.current.data?.items[1]?.event_type).toBe("click");
	});
});
