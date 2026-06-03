import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { makeJwt } from "@tests/mocks/jwt";
import { renderHook, waitFor } from "@tests/utils/render";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it } from "vitest";
import { useTimeseries } from "@/features/analytics/hooks/use-timeseries";
import { useAuthStore } from "@/features/auth/store/use-auth-store";

/**
 * @module tests/unit/features/analytics/use-timeseries
 * @description useTimeseries: resuelve analytics/timeseries y devuelve la serie
 *   de puntos del fixture MSW.
 */

const PARAMS = {
	from: "2026-04-27",
	to: "2026-05-28",
	bucket: "day" as const,
};

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

describe("useTimeseries", () => {
	it("Given un rango + bucket When la query resuelve Then devuelve los 2 puntos", async () => {
		// Arrange + Act
		const { result } = renderHook(() => useTimeseries(PARAMS), {
			wrapper: makeWrapper(),
		});

		// Assert
		await waitFor(() => {
			expect(result.current.isSuccess).toBe(true);
		});
		expect(result.current.data?.bucket).toBe("day");
		expect(result.current.data?.points).toHaveLength(2);
		expect(result.current.data?.points[0]?.count).toBe(10);
	});
});
