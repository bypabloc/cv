import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { makeJwt } from "@tests/mocks/jwt";
import { renderHook, waitFor } from "@tests/utils/render";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it } from "vitest";
import { useAuthStore } from "@/features/auth/store/use-auth-store";
import { useHeatmap } from "@/features/events/hooks/use-heatmap";

/**
 * @module tests/unit/features/events/use-heatmap
 * @description useHeatmap: distribucion de eventos por dia de semana x hora
 *   (events/heatmap). Desempaqueta el envelope y devuelve { cells } del fixture.
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

describe("useHeatmap", () => {
	it("Given un rango valido When la query resuelve Then devuelve las celdas del fixture", async () => {
		// Arrange + Act
		const { result } = renderHook(
			() => useHeatmap({ from: "2026-04-27", to: "2026-05-28" }),
			{ wrapper: makeWrapper() },
		);

		// Assert
		await waitFor(() => {
			expect(result.current.isSuccess).toBe(true);
		});
		expect(result.current.data?.cells).toHaveLength(2);
		expect(result.current.data?.cells[0]).toEqual({
			dow: 1,
			hour: 9,
			count: 12,
		});
		expect(result.current.data?.cells[1]).toEqual({
			dow: 3,
			hour: 14,
			count: 8,
		});
	});
});
