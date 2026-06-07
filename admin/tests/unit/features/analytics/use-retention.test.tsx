import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { makeJwt } from "@tests/mocks/jwt";
import { renderHook, waitFor } from "@tests/utils/render";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it } from "vitest";
import { useRetention } from "@/features/analytics/hooks/use-retention";
import { useAuthStore } from "@/features/auth/store/use-auth-store";

/**
 * @module tests/unit/features/analytics/use-retention
 * @description useRetention: resuelve analytics/retention y devuelve new vs
 *   returning del fixture MSW.
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

describe("useRetention", () => {
	it("Given un rango When la query resuelve Then devuelve new vs returning", async () => {
		// Arrange + Act
		const { result } = renderHook(() => useRetention(RANGE), {
			wrapper: makeWrapper(),
		});

		// Assert
		await waitFor(() => {
			expect(result.current.isSuccess).toBe(true);
		});
		expect(result.current.data?.new_visitors).toBe(60);
		expect(result.current.data?.returning_rate).toBe(0.2);
	});
});
