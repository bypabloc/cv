import { makeJwt } from "@tests/mocks/jwt";
import { server } from "@tests/mocks/server";
import { render, screen, waitFor } from "@tests/utils/render";
import { beforeEach, describe, expect, it, vi } from "vitest";
import MetricsOverviewPage from "@/app/(admin)/metrics/page";
import { useAuthStore } from "@/features/auth/store/use-auth-store";

/**
 * @module tests/unit/app/metrics/page
 * @description Regresion del fan-out de /metrics: la page debe disparar UNA
 *   sola request a `/analytics` (action=dashboard) en vez de 7 (overview +
 *   timeseries + top-pages + top-referrers + top-niches + active-now +
 *   retention). Cuenta las requests GET interceptadas por MSW y asserta que
 *   todas son `action=dashboard`.
 */

vi.mock("next/navigation", () => ({
	useSearchParams: () => new URLSearchParams(),
	useRouter: () => ({ replace: vi.fn(), push: vi.fn() }),
	usePathname: () => "/metrics",
}));

beforeEach(() => {
	useAuthStore.setState({ accessToken: makeJwt({ sub: "usr_01" }) });
});

describe("MetricsOverviewPage", () => {
	it("Given la page When monta Then dispara UNA sola request action=dashboard (no 7)", async () => {
		// Arrange: cuento las acciones de cada GET a /analytics.
		const actions: string[] = [];
		server.events.on("request:start", ({ request }) => {
			const url = new URL(request.url);
			if (request.method === "GET" && url.pathname.endsWith("/analytics")) {
				actions.push(url.searchParams.get("action") ?? "");
			}
		});

		// Act
		render(<MetricsOverviewPage />);

		// Assert: espera a que resuelva (los KPIs del fixture aparecen).
		await waitFor(() => {
			expect(screen.getByText("Metricas")).toBeInTheDocument();
		});
		await waitFor(() => {
			// El conteo del badge live viene del dashboard (3 activos del fixture).
			expect(screen.getByText(/3 activos/)).toBeInTheDocument();
		});

		// Toda request a /analytics fue action=dashboard, y ninguna granular.
		expect(actions.length).toBeGreaterThanOrEqual(1);
		expect([...new Set(actions)]).toEqual(["dashboard"]);
		expect(actions).not.toContain("overview");
		expect(actions).not.toContain("active-now");

		server.events.removeAllListeners("request:start");
	});

	it("Given el dashboard resuelto When render Then muestra los KPIs del overview", async () => {
		// Arrange + Act
		render(<MetricsOverviewPage />);

		// Assert: el KPI Sesiones del fixture (100) se renderiza.
		await waitFor(() => {
			expect(screen.getByText("Sesiones")).toBeInTheDocument();
		});
		await waitFor(() => {
			expect(screen.getByText("100")).toBeInTheDocument();
		});
	});
});
