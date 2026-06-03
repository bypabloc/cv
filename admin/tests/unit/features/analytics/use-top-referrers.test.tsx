import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { makeJwt } from "@tests/mocks/jwt";
import { renderHook, waitFor } from "@tests/utils/render";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it } from "vitest";
import { useTopReferrers } from "@/features/analytics/hooks/use-top-referrers";
import { useAuthStore } from "@/features/auth/store/use-auth-store";

/**
 * @module tests/unit/features/analytics/use-top-referrers
 * @description useTopReferrers: resuelve analytics/top-referrers y devuelve los
 *   rankings de referrers + UTM del fixture MSW.
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

describe("useTopReferrers", () => {
	it("Given un rango When la query resuelve Then devuelve referrers + UTM", async () => {
		// Arrange + Act
		const { result } = renderHook(() => useTopReferrers(RANGE), {
			wrapper: makeWrapper(),
		});

		// Assert
		await waitFor(() => {
			expect(result.current.isSuccess).toBe(true);
		});
		expect(result.current.data?.referrers[0]?.referrer).toBe("(direct)");
		expect(result.current.data?.utm_sources[0]?.utm_source).toBe("google");
	});
});
