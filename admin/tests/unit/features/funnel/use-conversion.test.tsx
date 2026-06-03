import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { makeJwt } from "@tests/mocks/jwt";
import { renderHook, waitFor } from "@tests/utils/render";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it } from "vitest";
import { useAuthStore } from "@/features/auth/store/use-auth-store";
import { useConversion } from "@/features/funnel/hooks/use-conversion";

/**
 * @module tests/unit/features/funnel/use-conversion
 * @description useConversion: useQuery contra funnel/conversion. Resuelve con el
 *   data del Lambda `analytics` (fixture MSW funnel:conversion).
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

describe("useConversion", () => {
	it("Given un rango valido When la query resuelve Then devuelve el embudo de conversion", async () => {
		// Arrange + Act
		const { result } = renderHook(
			() => useConversion({ from: "2026-04-27", to: "2026-05-27" }),
			{ wrapper: makeWrapper() },
		);

		// Assert
		await waitFor(() => {
			expect(result.current.isSuccess).toBe(true);
		});
		expect(result.current.data).toEqual({
			sessions: 100,
			visits: 80,
			contacts: 5,
			session_to_visit_rate: 0.8,
			visit_to_contact_rate: 0.063,
			session_to_contact_rate: 0.05,
		});
	});

	it("Given un rango sin parametros When la query resuelve Then devuelve las tasas", async () => {
		// Arrange + Act
		const { result } = renderHook(() => useConversion({}), {
			wrapper: makeWrapper(),
		});

		// Assert
		await waitFor(() => {
			expect(result.current.isSuccess).toBe(true);
		});
		expect(result.current.data?.session_to_visit_rate).toBe(0.8);
	});
});
