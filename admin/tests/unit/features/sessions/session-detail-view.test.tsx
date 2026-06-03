import { makeJwt } from "@tests/mocks/jwt";
import { server } from "@tests/mocks/server";
import { render, screen, userEvent, waitFor } from "@tests/utils/render";
import { HttpResponse, http } from "msw";
import { beforeEach, describe, expect, it } from "vitest";
import { useAuthStore } from "@/features/auth/store/use-auth-store";
import { SessionDetailView } from "@/features/sessions/components/SessionDetailView";

/**
 * @module tests/unit/features/sessions/session-detail-view
 * @description Detalle de una sesion: con data muestra visitas/eventos/
 *   dispositivo + resumen + tabla de visitas; un 404 muestra el EmptyState; un
 *   error generico muestra el ErrorAlert. Usa el MSW handler de /analytics
 *   (override por caso para 404/500).
 */

const API = "https://api.test.the-full-stack.com";

beforeEach(() => {
	useAuthStore.setState({ accessToken: makeJwt({ sub: "usr_01" }) });
});

describe("SessionDetailView", () => {
	it("Given un sessionId valido When la query resuelve Then muestra eventos, dispositivo y resumen", async () => {
		// Arrange + Act
		render(<SessionDetailView sessionId="sess_1" />);

		// Assert: el header muestra el id desde el primer render
		expect(screen.getByRole("heading", { name: "sess_1" })).toBeInTheDocument();
		// events_count=6 del fixture
		await waitFor(() => {
			expect(screen.getByText("6")).toBeInTheDocument();
		});
		// visits_count=2 del fixture
		expect(screen.getByText("2")).toBeInTheDocument();
		expect(screen.getByText("Sistema operativo")).toBeInTheDocument();
		expect(screen.getByText("Linux")).toBeInTheDocument();
		// la tabla de visitas renderiza la unica visita (landing '/')
		expect(screen.getByText("/")).toBeInTheDocument();
	});

	it("Given un boton Volver When se renderiza Then enlaza al listado de sesiones", () => {
		// Arrange + Act
		render(<SessionDetailView sessionId="sess_1" />);

		// Assert
		const back = screen.getByRole("link", { name: /Volver/ });
		expect(back).toHaveAttribute("href", "/metrics/sessions");
	});

	it("Given un 404 del backend When la query falla Then muestra el EmptyState de sesion no encontrada", async () => {
		// Arrange: override -> 404
		server.use(
			http.get(`${API}/analytics`, () =>
				HttpResponse.json(
					{ error: "NOT_FOUND", code: 4040, message: "No existe" },
					{ status: 404 },
				),
			),
		);

		// Act
		render(<SessionDetailView sessionId="sess_missing" />);

		// Assert
		await waitFor(() => {
			expect(screen.getByText("Sesion no encontrada")).toBeInTheDocument();
		});
		expect(
			screen.getByRole("link", { name: "Ver todas las sesiones" }),
		).toBeInTheDocument();
	});

	it("Given un error 500 del backend When la query falla Then muestra el ErrorAlert con reintento", async () => {
		// Arrange: override -> 500
		server.use(
			http.get(`${API}/analytics`, () =>
				HttpResponse.json(
					{ error: "INTERNAL", code: 6000, message: "Error interno" },
					{ status: 500 },
				),
			),
		);

		// Act
		render(<SessionDetailView sessionId="sess_1" />);

		// Assert
		const alert = await screen.findByRole("alert");
		expect(alert).toHaveTextContent("Error interno");
		expect(
			screen.getByRole("button", { name: "Reintentar" }),
		).toBeInTheDocument();
	});

	it("Given el ErrorAlert con reintento When se clickea Reintentar Then refetch re-consulta y muestra la data", async () => {
		// Arrange: primer request 500, los siguientes 200 (la 2da consulta proviene
		// del refetch del onRetry inline -> invoca detail.refetch()).
		let calls = 0;
		server.use(
			http.get(`${API}/analytics`, () => {
				calls += 1;
				if (calls === 1) {
					return HttpResponse.json(
						{ error: "INTERNAL", code: 6000, message: "Error interno" },
						{ status: 500 },
					);
				}
				return HttpResponse.json(
					{
						session: {
							session_id: "sess_1",
							first_seen_at: "2026-05-01T10:00:00Z",
							last_seen_at: "2026-05-20T10:00:00Z",
							browser: "Chrome",
							browser_version: "120",
							os: "Linux",
							device_type: "desktop",
							visits_count: 2,
						},
						visits: [],
						events_count: 6,
					},
					{ status: 200 },
				);
			}),
		);
		const user = userEvent.setup();

		// Act: aparece el error -> click en Reintentar dispara el onRetry inline
		render(<SessionDetailView sessionId="sess_1" />);
		const retry = await screen.findByRole("button", { name: "Reintentar" });
		await user.click(retry);

		// Assert: tras el refetch exitoso desaparece el error y aparece la data
		await waitFor(() => {
			expect(screen.getByText("Sistema operativo")).toBeInTheDocument();
		});
		expect(screen.queryByRole("alert")).not.toBeInTheDocument();
		expect(calls).toBe(2);
	});

	it("Given la query en vuelo When aun no resuelve Then muestra los skeletons (sin error ni data)", () => {
		// Arrange: handler que nunca responde -> la query queda pending, forzando el
		// estado isLoading del primer render (skeletons).
		server.use(
			http.get(`${API}/analytics`, () => new Promise<Response>(() => {})),
		);

		// Act
		const { container } = render(
			<SessionDetailView sessionId="sess_pending" />,
		);

		// Assert: el header ya esta; los Skeleton (animate-pulse) se renderizan y no
		// hay error ni la data del fixture todavia.
		expect(
			screen.getByRole("heading", { name: "sess_pending" }),
		).toBeInTheDocument();
		expect(container.querySelectorAll(".animate-pulse").length).toBeGreaterThan(
			0,
		);
		expect(screen.queryByRole("alert")).not.toBeInTheDocument();
		expect(screen.queryByText("Sistema operativo")).not.toBeInTheDocument();
	});
});
