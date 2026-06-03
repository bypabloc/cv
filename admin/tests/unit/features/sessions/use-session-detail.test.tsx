import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { makeJwt } from "@tests/mocks/jwt";
import { renderHook, waitFor } from "@tests/utils/render";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it } from "vitest";
import { useAuthStore } from "@/features/auth/store/use-auth-store";
import { useSessionDetail } from "@/features/sessions/hooks/use-session-detail";

/**
 * @module tests/unit/features/sessions/use-session-detail
 * @description useSessionDetail: detalle de una sesion de visitante
 *   (sessions/detail). Solo dispara con un session_id no vacio (enabled). El
 *   MSW handler de /analytics provee el `data`.
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

describe("useSessionDetail", () => {
	it("Given un session_id valido When la query resuelve Then devuelve sesion + visitas + events_count", async () => {
		// Arrange + Act
		const { result } = renderHook(
			() => useSessionDetail({ session_id: "sess_1" }),
			{ wrapper: makeWrapper() },
		);

		// Assert
		await waitFor(() => {
			expect(result.current.isSuccess).toBe(true);
		});
		expect(result.current.data?.session.session_id).toBe("sess_1");
		expect(result.current.data?.events_count).toBe(6);
		expect(result.current.data?.visits).toHaveLength(1);
	});

	it("Given un session_id vacio When se monta Then la query queda deshabilitada (no dispara)", () => {
		// Arrange + Act
		const { result } = renderHook(() => useSessionDetail({ session_id: "" }), {
			wrapper: makeWrapper(),
		});

		// Assert: enabled=false (Tanstack v5) -> fetchStatus idle, status
		// pending, NO isLoading (no hay fetch en vuelo), sin data.
		expect(result.current.fetchStatus).toBe("idle");
		expect(result.current.isPending).toBe(true);
		expect(result.current.isLoading).toBe(false);
		expect(result.current.data).toBeUndefined();
	});
});
