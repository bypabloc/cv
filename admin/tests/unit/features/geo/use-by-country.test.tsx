import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { makeJwt } from "@tests/mocks/jwt";
import { renderHook, waitFor } from "@tests/utils/render";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it } from "vitest";
import { useAuthStore } from "@/features/auth/store/use-auth-store";
import { useByCountry } from "@/features/geo/hooks/use-by-country";

/**
 * @module tests/unit/features/geo/use-by-country
 * @description useByCountry: useQuery contra geo/by-country. Resuelve con el
 *   data del Lambda `analytics` (fixture MSW geo:by-country).
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

describe("useByCountry", () => {
	it("Given un rango valido When la query resuelve Then devuelve items + total", async () => {
		// Arrange + Act
		const { result } = renderHook(
			() => useByCountry({ from: "2026-04-27", to: "2026-05-27" }),
			{ wrapper: makeWrapper() },
		);

		// Assert
		await waitFor(() => {
			expect(result.current.isSuccess).toBe(true);
		});
		expect(result.current.data).toEqual({
			items: [{ country: "AR", sessions: 30, visits: 40, events: 100 }],
			total: 30,
		});
	});

	it("Given un limit explicito When la query resuelve Then devuelve el ranking", async () => {
		// Arrange + Act
		const { result } = renderHook(
			() => useByCountry({ from: "2026-04-27", to: "2026-05-27", limit: 5 }),
			{ wrapper: makeWrapper() },
		);

		// Assert
		await waitFor(() => {
			expect(result.current.isSuccess).toBe(true);
		});
		expect(result.current.data?.items[0]?.country).toBe("AR");
	});
});
