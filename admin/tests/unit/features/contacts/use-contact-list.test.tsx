import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { makeJwt } from "@tests/mocks/jwt";
import { renderHook, waitFor } from "@tests/utils/render";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it } from "vitest";
import { useAuthStore } from "@/features/auth/store/use-auth-store";
import { useContactList } from "@/features/contacts/hooks/use-contact-list";

/**
 * @module tests/unit/features/contacts/use-contact-list
 * @description useContactList: listado crudo paginado de contactos
 *   (contacts/list). Desempaqueta el envelope del Lambda `analytics` y devuelve
 *   la pagina del fixture MSW.
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

describe("useContactList", () => {
	it("Given un rango valido When la query resuelve Then devuelve la pagina de contactos", async () => {
		// Arrange + Act
		const { result } = renderHook(
			() => useContactList({ from: "2026-04-27", to: "2026-05-28" }),
			{ wrapper: makeWrapper() },
		);

		// Assert
		await waitFor(() => {
			expect(result.current.isSuccess).toBe(true);
		});
		expect(result.current.data?.total).toBe(1);
		expect(result.current.data?.items).toHaveLength(1);
		expect(result.current.data?.items[0]?.name).toBe("Ada");
		expect(result.current.data?.items[0]?.email).toBe("ada@example.com");
		expect(result.current.data?.items[0]?.status).toBe("new");
	});

	it("Given filtros status y niche When la query resuelve Then sigue devolviendo el data", async () => {
		// Arrange + Act
		const { result } = renderHook(
			() =>
				useContactList({
					from: "2026-04-27",
					to: "2026-05-28",
					status: "new",
					niche: "fintech",
				}),
			{ wrapper: makeWrapper() },
		);

		// Assert
		await waitFor(() => {
			expect(result.current.isSuccess).toBe(true);
		});
		expect(result.current.data?.has_more).toBe(false);
	});
});
