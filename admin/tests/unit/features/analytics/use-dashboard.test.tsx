import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { makeJwt } from "@tests/mocks/jwt";
import { renderHook, waitFor } from "@tests/utils/render";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it } from "vitest";
import { useDashboard } from "@/features/analytics/hooks/use-dashboard";
import { useAuthStore } from "@/features/auth/store/use-auth-store";

/**
 * @module tests/unit/features/analytics/use-dashboard
 * @description useDashboard: una sola query resuelve analytics/dashboard y
 *   devuelve las 7 vistas (overview/timeseries/top_pages/top_referrers/
 *   top_niches/active_now/retention) desempaquetadas del Envelope. La data
 *   sintetica del MSW handler de metrics combina los fixtures granulares.
 */

const PARAMS = { from: "2026-04-27", to: "2026-05-28", bucket: "day" } as const;

function makeWrapper() {
	const client = new QueryClient({
		defaultOptions: {
			queries: { retry: false, gcTime: 0, refetchInterval: false },
		},
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

describe("useDashboard", () => {
	it("Given un rango When la query resuelve Then devuelve las 7 vistas en un solo payload", async () => {
		// Arrange + Act
		const { result } = renderHook(() => useDashboard(PARAMS), {
			wrapper: makeWrapper(),
		});

		// Assert
		await waitFor(() => {
			expect(result.current.isSuccess).toBe(true);
		});
		const data = result.current.data;
		expect(data?.overview.sessions).toBe(100);
		expect(data?.timeseries.points).toHaveLength(2);
		expect(data?.top_pages.items[0]?.page_path).toBe("/");
		expect(data?.top_referrers.referrers[0]?.referrer).toBe("(direct)");
		expect(data?.top_niches.items[0]?.niche).toBe("fintech");
		expect(data?.active_now.active_sessions).toBe(3);
		expect(data?.retention.returning_rate).toBe(0.2);
	});
});
