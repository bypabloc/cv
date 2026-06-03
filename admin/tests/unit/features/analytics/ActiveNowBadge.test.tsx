import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, waitFor } from "@testing-library/react";
import { makeJwt } from "@tests/mocks/jwt";
import { server } from "@tests/mocks/server";
import { HttpResponse, http } from "msw";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it } from "vitest";
import { ActiveNowBadge } from "@/features/analytics/components/ActiveNowBadge";
import { useAuthStore } from "@/features/auth/store/use-auth-store";

/**
 * @module tests/unit/features/analytics/ActiveNowBadge
 * @description ActiveNowBadge: contador live (useActiveNow). Muestra un guion
 *   mientras carga o si falla; el conteo + plural/singular cuando hay data.
 *   Wrapper propio con retry:false + refetchInterval off para que el branch
 *   de error resuelva sin esperar reintentos. El conteo y el plural viven en
 *   el mismo <span>, por eso se asertan contra el textContent normalizado.
 */

const API = "https://api.test.the-full-stack.com";

function Wrapper({ children }: { children: ReactNode }) {
	const client = new QueryClient({
		defaultOptions: {
			queries: { retry: false, gcTime: 0, refetchInterval: false },
		},
	});
	return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

beforeEach(() => {
	useAuthStore.setState({ accessToken: makeJwt({ sub: "usr_01" }) });
});

describe("ActiveNowBadge", () => {
	it("Given el render inicial When aun no resolvio Then muestra un guion en plural", () => {
		// Arrange + Act
		const { container } = render(<ActiveNowBadge />, { wrapper: Wrapper });

		// Assert: estado loading -> "– activos"
		expect(container.textContent?.replace(/\s+/g, " ")).toContain("– activos");
	});

	it("Given el fixture (3 sesiones) When la query resuelve Then muestra el conteo en plural", async () => {
		// Arrange + Act
		const { container } = render(<ActiveNowBadge />, { wrapper: Wrapper });

		// Assert
		await waitFor(() => {
			expect(container.textContent?.replace(/\s+/g, " ")).toContain(
				"3 activos",
			);
		});
	});

	it("Given exactamente 1 sesion activa When la query resuelve Then usa el singular", async () => {
		// Arrange
		server.use(
			http.get(`${API}/analytics`, () =>
				HttpResponse.json(
					{ active_sessions: 1, threshold_minutes: 5, as_of: "x" },
					{ status: 200 },
				),
			),
		);

		// Act
		const { container } = render(<ActiveNowBadge />, { wrapper: Wrapper });

		// Assert
		await waitFor(() => {
			expect(container.textContent?.replace(/\s+/g, " ")).toContain("1 activo");
		});
		expect(container.textContent?.replace(/\s+/g, " ")).not.toContain(
			"1 activos",
		);
	});

	it("Given un error del backend When la query falla Then muestra un guion", async () => {
		// Arrange
		server.use(
			http.get(`${API}/analytics`, () =>
				HttpResponse.json({ error: "boom", code: 5000 }, { status: 500 }),
			),
		);

		// Act
		const { container } = render(<ActiveNowBadge />, { wrapper: Wrapper });

		// Assert
		await waitFor(() => {
			expect(container.textContent?.replace(/\s+/g, " ")).toContain(
				"– activos",
			);
		});
	});
});
