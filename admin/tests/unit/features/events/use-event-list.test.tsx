import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { makeJwt } from "@tests/mocks/jwt";
import { renderHook, waitFor } from "@tests/utils/render";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it } from "vitest";
import { useAuthStore } from "@/features/auth/store/use-auth-store";
import { useEventList } from "@/features/events/hooks/use-event-list";

/**
 * @module tests/unit/features/events/use-event-list
 * @description useEventList: listado crudo paginado de eventos (events/list).
 *   Desempaqueta el envelope y devuelve la pagina del fixture MSW.
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

describe("useEventList", () => {
	it("Given un rango + paginacion When la query resuelve Then devuelve la pagina del fixture", async () => {
		// Arrange + Act
		const { result } = renderHook(
			() =>
				useEventList({
					from: "2026-04-27",
					to: "2026-05-28",
					page: 1,
					page_size: 50,
				}),
			{ wrapper: makeWrapper() },
		);

		// Assert
		await waitFor(() => {
			expect(result.current.isSuccess).toBe(true);
		});
		expect(result.current.data?.items).toHaveLength(1);
		expect(result.current.data?.items[0]?.visit_id).toBe("vis_1");
		expect(result.current.data?.page).toBe(1);
		expect(result.current.data?.page_size).toBe(50);
		expect(result.current.data?.total).toBe(1);
		expect(result.current.data?.has_more).toBe(false);
	});
});
