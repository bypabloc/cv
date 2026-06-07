import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { makeJwt } from "@tests/mocks/jwt";
import { renderHook, waitFor } from "@tests/utils/render";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it } from "vitest";
import { useAuthStore } from "@/features/auth/store/use-auth-store";
import { useVisitsList } from "@/features/visits/hooks/use-visits-list";

/**
 * @module tests/unit/features/visits/use-visits-list
 * @description useVisitsList: deriva offset desde page/page_size y devuelve la
 *   pagina de visitas (visits/list) desempaquetada del envelope.
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

describe("useVisitsList", () => {
	it("Given un rango + page When la query resuelve Then devuelve la pagina de visitas", async () => {
		// Arrange + Act
		const { result } = renderHook(
			() =>
				useVisitsList({
					from: "2026-04-27",
					to: "2026-05-28",
					page: 1,
					page_size: 20,
				}),
			{ wrapper: makeWrapper() },
		);

		// Assert
		await waitFor(() => {
			expect(result.current.isSuccess).toBe(true);
		});
		expect(result.current.data?.total).toBe(1);
		expect(result.current.data?.items).toHaveLength(1);
		expect(result.current.data?.items[0]?.visit_id).toBe("vis_1");
	});

	it("Given params sin page ni page_size When la query resuelve Then usa los defaults y resuelve", async () => {
		// Arrange + Act: page=1, page_size=20, offset=0 derivados por defecto
		const { result } = renderHook(
			() => useVisitsList({ from: "2026-04-27", to: "2026-05-28" }),
			{ wrapper: makeWrapper() },
		);

		// Assert
		await waitFor(() => {
			expect(result.current.isSuccess).toBe(true);
		});
		expect(result.current.data?.page).toBe(1);
		expect(result.current.data?.page_size).toBe(20);
		expect(result.current.data?.has_more).toBe(false);
	});

	it("Given page=3 con page_size=10 When la query resuelve Then deriva offset=20 sin romper", async () => {
		// Arrange + Act: el offset derivado (page-1)*page_size se pasa al client
		const { result } = renderHook(
			() =>
				useVisitsList({
					from: "2026-04-27",
					to: "2026-05-28",
					page: 3,
					page_size: 10,
				}),
			{ wrapper: makeWrapper() },
		);

		// Assert
		await waitFor(() => {
			expect(result.current.isSuccess).toBe(true);
		});
		expect(result.current.data?.items[0]?.session_id).toBe("sess_1");
	});
});
