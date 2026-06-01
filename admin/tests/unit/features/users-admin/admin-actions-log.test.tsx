import { server } from "@tests/mocks/server";
import { render, screen, waitFor } from "@tests/utils/render";
import { HttpResponse, http } from "msw";
import { describe, expect, it } from "vitest";
import { AdminActionsLog } from "@/features/users-admin/components/admin-actions-log";

/**
 * @module tests/unit/features/users-admin/admin-actions-log
 * @description Verifica que el log de acciones admin renderiza la fila del
 *   handler MSW (action disable-user del actor usr_01) y el ErrorAlert si falla.
 */

const API = "https://api.test.the-full-stack.com";

describe("AdminActionsLog", () => {
	it("Given el log de acciones When render Then muestra la accion y el actor", async () => {
		// Arrange + Act
		render(<AdminActionsLog />);

		// Assert
		await waitFor(() => {
			expect(screen.getByText("disable-user")).toBeInTheDocument();
		});
		expect(screen.getByText("usr_01")).toBeInTheDocument();
	});

	it("Given un 500 del backend When render Then muestra el ErrorAlert", async () => {
		// Arrange
		server.use(
			http.post(`${API}/users`, () =>
				HttpResponse.json(
					{ error: "SERVER_ERROR", code: 6000, message: "Error interno" },
					{ status: 500 },
				),
			),
		);

		// Act
		render(<AdminActionsLog />);

		// Assert
		await waitFor(() => {
			expect(screen.getByText("Error interno")).toBeInTheDocument();
		});
	});
});
