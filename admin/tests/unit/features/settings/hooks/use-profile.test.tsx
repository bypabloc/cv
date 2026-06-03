import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import { server } from "@tests/mocks/server";
import { HttpResponse, http } from "msw";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";
import { useProfile } from "@/features/settings/hooks/use-profile";

/**
 * @module tests/unit/features/settings/hooks/use-profile
 * @description Regresion del bug "['settings','profile'] data is undefined": el
 *   backend responde el perfil FLAT (campos de UserProfile al nivel raiz de
 *   `data`, NO anidados en `profile`). El hook debe devolver ese `data` tal
 *   cual. Antes el hook leia `data.profile` (== undefined) y el form caia en
 *   estado de error.
 */

vi.mock("next/navigation", () => ({
	useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
}));

const API = "https://api.test.the-full-stack.com";

function wrapper({ children }: { children: ReactNode }) {
	const client = new QueryClient({
		defaultOptions: { queries: { retry: false } },
	});
	return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

describe("useProfile", () => {
	it("Given el backend responde el perfil FLAT When la query resuelve Then devuelve el UserProfile desempaquetado", async () => {
		// Arrange: el MSW por defecto devuelve PROFILE flat (user@test.com).

		// Act
		const { result } = renderHook(() => useProfile(), { wrapper });

		// Assert: data ES el UserProfile (no undefined, no anidado en .profile)
		await waitFor(() => expect(result.current.isSuccess).toBe(true));
		expect(result.current.data).toEqual({
			id: "usr_01",
			email: "user@test.com",
			display_name: "Pablo",
			status: "active",
			locale: "es",
			timezone: "America/Santiago",
			marketing_consent: false,
			created_at: "2026-01-01T00:00:00Z",
		});
	});

	it("Given un perfil con email distinto When resuelve Then expone el email al nivel raiz (no en data.profile)", async () => {
		// Arrange: override flat con otro email
		server.use(
			http.post(`${API}/users`, () =>
				HttpResponse.json({
					is_valid: true,
					code: 0,
					data: {
						id: "usr_99",
						email: "real@test.com",
						display_name: null,
						status: "active",
						locale: "en",
						timezone: "UTC",
						marketing_consent: false,
						created_at: "2026-06-03T00:00:00Z",
					},
				}),
			),
		);

		// Act
		const { result } = renderHook(() => useProfile(), { wrapper });

		// Assert
		await waitFor(() => expect(result.current.isSuccess).toBe(true));
		expect(result.current.data?.email).toBe("real@test.com");
		expect(result.current.data?.display_name).toBe(null);
	});
});
