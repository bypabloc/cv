import { server } from "@tests/mocks/server";
import { render, screen, userEvent, waitFor } from "@tests/utils/render";
import { HttpResponse, http } from "msw";
import { describe, expect, it, vi } from "vitest";
import UsersAdminPage from "@/app/(admin)/users/page";

/**
 * @module tests/unit/features/users-admin/users-page-gate
 * @description Verifica el gate anti-enumeration: list-users 404 (caller no
 *   admin) -> "No tienes acceso a esta seccion"; el camino admin muestra la
 *   tabla; y el click en una fila hace deep-link `?user=<id>`.
 */

const API = "https://api.test.the-full-stack.com";

const { replaceMock } = vi.hoisted(() => ({ replaceMock: vi.fn() }));

vi.mock("next/navigation", () => ({
	useRouter: () => ({ replace: replaceMock, push: vi.fn() }),
	useSearchParams: () => new URLSearchParams(),
}));

describe("UsersAdminPage (gate 404)", () => {
	it("Given list-users 404 When render Then muestra el estado de acceso denegado", async () => {
		// Arrange: forzar 404 NOT_FOUND para admin.list-users (caller no admin)
		server.use(
			http.post(`${API}/users`, () =>
				HttpResponse.json({ error: "NOT_FOUND", code: 4040 }, { status: 404 }),
			),
		);

		// Act
		render(<UsersAdminPage />);

		// Assert
		expect(
			await screen.findByText("No tienes acceso a esta seccion"),
		).toBeInTheDocument();
	});

	it("Given caller admin When render Then muestra los usuarios del listado", async () => {
		// Arrange: el handler por defecto devuelve 2 usuarios

		// Act
		render(<UsersAdminPage />);

		// Assert
		await waitFor(() => {
			expect(screen.getByText("user@test.com")).toBeInTheDocument();
		});
		expect(screen.getByText("other@test.com")).toBeInTheDocument();
	});

	it("Given click en una fila When seleccionar Then hace deep-link ?user=<id>", async () => {
		// Arrange
		render(<UsersAdminPage />);
		await waitFor(() => {
			expect(screen.getByText("user@test.com")).toBeInTheDocument();
		});

		// Act
		await userEvent.click(screen.getByText("user@test.com"));

		// Assert
		expect(replaceMock).toHaveBeenCalledWith("/users?user=usr_01");
	});
});
