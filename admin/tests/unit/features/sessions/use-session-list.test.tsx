import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { makeJwt } from "@tests/mocks/jwt";
import { renderHook, waitFor } from "@tests/utils/render";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it } from "vitest";
import { useAuthStore } from "@/features/auth/store/use-auth-store";
import { useSessionList } from "@/features/sessions/hooks/use-session-list";

/**
 * @module tests/unit/features/sessions/use-session-list
 * @description useSessionList: listado paginado de sesiones de visitantes
 *   (sessions/list). Resuelve via el MSW handler de /analytics y devuelve el
 *   `data` desempaquetado.
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

describe("useSessionList", () => {
	it("Given params validos When la query resuelve Then devuelve el listado paginado del fixture", async () => {
		// Arrange + Act
		const { result } = renderHook(
			() => useSessionList({ from: "2026-05-01", to: "2026-05-28", page: 1 }),
			{ wrapper: makeWrapper() },
		);

		// Assert
		await waitFor(() => {
			expect(result.current.isSuccess).toBe(true);
		});
		expect(result.current.data?.total).toBe(1);
		expect(result.current.data?.items).toHaveLength(1);
		expect(result.current.data?.items[0]?.session_id).toBe("sess_1");
		expect(result.current.data?.items[0]?.visits_count).toBe(4);
	});
});
