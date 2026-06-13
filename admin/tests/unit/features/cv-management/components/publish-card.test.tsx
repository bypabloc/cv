import { server } from "@tests/mocks/server";
import {
	render,
	screen,
	userEvent,
	waitFor,
	within,
} from "@tests/utils/render";
import { HttpResponse, http } from "msw";
import { describe, expect, it } from "vitest";
import { PublishCard } from "@/features/cv-management/components/publish-card";

/**
 * @module tests/unit/features/cv-management/components/publish-card
 * @description Verifica la card de publicacion: estado del ultimo run,
 *   AlertDialog de confirmacion (aviso de deploy de 6 apps), cancelar sin
 *   request y confirmar -> dispatch + toast con link a Actions.
 */

const API = "https://api.test.the-full-stack.com";

describe("PublishCard", () => {
	it("Given el ultimo run When la query resuelve Then muestra estado y link al run", async () => {
		// Arrange + Act
		render(<PublishCard />);

		// Assert
		await waitFor(() => {
			expect(screen.getByTestId("cv-publish-status")).toHaveTextContent(
				"queued · 2026-06-01T10:00:00Z",
			);
		});
		expect(screen.getByRole("link", { name: "Ver run" })).toHaveAttribute(
			"href",
			"https://github.com/bypabloc/cv/actions/runs/123",
		);
	});

	it("Given sin runs When la query resuelve Then dice Sin publicaciones recientes", async () => {
		// Arrange
		server.use(
			http.post(`${API}/cv`, () =>
				HttpResponse.json({
					is_valid: true,
					code: 0,
					data: { status: "none", ref: "dev" },
				}),
			),
		);

		// Act
		render(<PublishCard />);

		// Assert
		await waitFor(() => {
			expect(screen.getByTestId("cv-publish-status")).toHaveTextContent(
				"Sin publicaciones recientes",
			);
		});
	});

	it("Given el boton publicar When se clickea Then abre el AlertDialog con el aviso de deploy", async () => {
		// Arrange
		const user = userEvent.setup();
		render(<PublishCard />);

		// Act
		await user.click(screen.getByTestId("cv-publish-button"));

		// Assert: el aviso vive DENTRO del alertdialog (la CardDescription
		// tambien menciona el deploy).
		const dialog = screen.getByRole("alertdialog");
		expect(within(dialog).getByText("Publicar el CV")).toBeInTheDocument();
		expect(
			within(dialog).getByText(/deploy de las 6 apps del entorno/),
		).toBeInTheDocument();
	});

	it("Given el dialog abierto When se cancela Then NO sale ningun dispatch", async () => {
		// Arrange: contar los dispatch reales.
		let dispatchCount = 0;
		server.use(
			http.post(`${API}/cv`, async ({ request }) => {
				const body = (await request.json()) as { action: string };
				if (body.action === "dispatch") {
					dispatchCount += 1;
				}
				return HttpResponse.json({
					is_valid: true,
					code: 0,
					data: { status: "none", ref: "dev" },
				});
			}),
		);
		const user = userEvent.setup();
		render(<PublishCard />);

		// Act
		await user.click(screen.getByTestId("cv-publish-button"));
		await user.click(screen.getByTestId("cv-publish-cancel"));

		// Assert
		expect(dispatchCount).toBe(0);
		expect(screen.queryByText("Publicar el CV")).not.toBeInTheDocument();
	});

	it("Given la confirmacion When se publica Then toastea con el link a Actions", async () => {
		// Arrange
		const user = userEvent.setup();
		render(<PublishCard />);

		// Act
		await user.click(screen.getByTestId("cv-publish-button"));
		await user.click(screen.getByTestId("cv-publish-confirm"));

		// Assert: el toast (sonner) renderiza el link con la url del dispatch.
		await waitFor(() => {
			expect(screen.getByTestId("cv-publish-actions-link")).toHaveAttribute(
				"href",
				"https://github.com/bypabloc/cv/actions/workflows/deploy-apps.yml",
			);
		});
		expect(screen.getByText("Ver en Actions")).toBeInTheDocument();
	});
});
