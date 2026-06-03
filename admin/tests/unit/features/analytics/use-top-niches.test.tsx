import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { makeJwt } from "@tests/mocks/jwt";
import { renderHook, waitFor } from "@tests/utils/render";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it } from "vitest";
import { useTopNiches } from "@/features/analytics/hooks/use-top-niches";
import { useAuthStore } from "@/features/auth/store/use-auth-store";

/**
 * @module tests/unit/features/analytics/use-top-niches
 * @description useTopNiches: resuelve analytics/top-niches y devuelve el ranking
 *   de niches del fixture MSW.
 */

const RANGE = { from: "2026-04-27", to: "2026-05-28" };

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

describe("useTopNiches", () => {
	it("Given un rango When la query resuelve Then devuelve el ranking de niches", async () => {
		// Arrange + Act
		const { result } = renderHook(() => useTopNiches(RANGE), {
			wrapper: makeWrapper(),
		});

		// Assert
		await waitFor(() => {
			expect(result.current.isSuccess).toBe(true);
		});
		expect(result.current.data?.items).toHaveLength(1);
		expect(result.current.data?.items[0]?.niche).toBe("fintech");
		expect(result.current.data?.items[0]?.visits).toBe(30);
	});
});
