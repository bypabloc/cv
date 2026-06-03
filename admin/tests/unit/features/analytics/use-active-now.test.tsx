import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { makeJwt } from "@tests/mocks/jwt";
import { renderHook, waitFor } from "@tests/utils/render";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it } from "vitest";
import { useActiveNow } from "@/features/analytics/hooks/use-active-now";
import { useAuthStore } from "@/features/auth/store/use-auth-store";

/**
 * @module tests/unit/features/analytics/use-active-now
 * @description useActiveNow: resuelve analytics/active-now (live, sin rango) y
 *   devuelve el contador de sesiones activas del fixture MSW.
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

describe("useActiveNow", () => {
	it("Given sin params When la query resuelve Then devuelve el contador live", async () => {
		// Arrange + Act
		const { result } = renderHook(() => useActiveNow(), {
			wrapper: makeWrapper(),
		});

		// Assert
		await waitFor(() => {
			expect(result.current.isSuccess).toBe(true);
		});
		expect(result.current.data?.active_sessions).toBe(3);
		expect(result.current.data?.threshold_minutes).toBe(5);
	});
});
