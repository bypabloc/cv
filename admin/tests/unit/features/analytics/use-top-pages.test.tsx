import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { makeJwt } from "@tests/mocks/jwt";
import { renderHook, waitFor } from "@tests/utils/render";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it } from "vitest";
import { useTopPages } from "@/features/analytics/hooks/use-top-pages";
import { useAuthStore } from "@/features/auth/store/use-auth-store";

/**
 * @module tests/unit/features/analytics/use-top-pages
 * @description useTopPages: resuelve analytics/top-pages y devuelve el ranking
 *   de paginas del fixture MSW.
 */

const PARAMS = { from: "2026-04-27", to: "2026-05-28", limit: 10 };

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

describe("useTopPages", () => {
	it("Given un rango + limit When la query resuelve Then devuelve el item del ranking", async () => {
		// Arrange + Act
		const { result } = renderHook(() => useTopPages(PARAMS), {
			wrapper: makeWrapper(),
		});

		// Assert
		await waitFor(() => {
			expect(result.current.isSuccess).toBe(true);
		});
		expect(result.current.data?.items).toHaveLength(1);
		expect(result.current.data?.items[0]?.page_path).toBe("/");
		expect(result.current.data?.items[0]?.events).toBe(50);
	});
});
