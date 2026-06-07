import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { makeJwt } from "@tests/mocks/jwt";
import { renderHook, waitFor } from "@tests/utils/render";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it } from "vitest";
import { useOverview } from "@/features/analytics/hooks/use-overview";
import { useAuthStore } from "@/features/auth/store/use-auth-store";

/**
 * @module tests/unit/features/analytics/use-overview
 * @description useOverview: resuelve analytics/overview y devuelve los 7 KPIs
 *   desempaquetados del Envelope (data sintetica del MSW handler de metrics).
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

describe("useOverview", () => {
	it("Given un rango When la query resuelve Then devuelve los KPIs del fixture", async () => {
		// Arrange + Act
		const { result } = renderHook(() => useOverview(RANGE), {
			wrapper: makeWrapper(),
		});

		// Assert
		await waitFor(() => {
			expect(result.current.isSuccess).toBe(true);
		});
		expect(result.current.data?.sessions).toBe(100);
		expect(result.current.data?.bounce_rate).toBe(0.15);
	});
});
