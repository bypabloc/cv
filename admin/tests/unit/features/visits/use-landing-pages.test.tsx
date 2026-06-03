import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { makeJwt } from "@tests/mocks/jwt";
import { renderHook, waitFor } from "@tests/utils/render";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it } from "vitest";
import { useAuthStore } from "@/features/auth/store/use-auth-store";
import { useLandingPages } from "@/features/visits/hooks/use-landing-pages";

/**
 * @module tests/unit/features/visits/use-landing-pages
 * @description useLandingPages: devuelve el ranking de landing pages
 *   (visits/landing-pages) desempaquetado del envelope.
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

describe("useLandingPages", () => {
	it("Given un rango + limit When la query resuelve Then devuelve el ranking de landing pages", async () => {
		// Arrange + Act
		const { result } = renderHook(
			() =>
				useLandingPages({
					from: "2026-04-27",
					to: "2026-05-28",
					limit: 10,
				}),
			{ wrapper: makeWrapper() },
		);

		// Assert
		await waitFor(() => {
			expect(result.current.isSuccess).toBe(true);
		});
		expect(result.current.data?.items).toHaveLength(1);
		expect(result.current.data?.items[0]?.landing_page_path).toBe("/");
		expect(result.current.data?.items[0]?.visits).toBe(40);
		expect(result.current.data?.items[0]?.unique_visitors).toBe(30);
	});

	it("Given solo el rango sin limit When la query resuelve Then resuelve igual", async () => {
		// Arrange + Act
		const { result } = renderHook(
			() => useLandingPages({ from: "2026-04-27", to: "2026-05-28" }),
			{ wrapper: makeWrapper() },
		);

		// Assert
		await waitFor(() => {
			expect(result.current.isSuccess).toBe(true);
		});
		expect(result.current.data?.items[0]?.visits).toBe(40);
	});
});
