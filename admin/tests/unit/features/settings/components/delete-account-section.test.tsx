import { server } from "@tests/mocks/server";
import { render, screen, userEvent, waitFor } from "@tests/utils/render";
import { HttpResponse, http } from "msw";
import type { ReactElement } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useAuthStore } from "@/features/auth/store/use-auth-store";
import { DeleteAccountSection } from "@/features/settings/components/delete-account-section";

/**
 * @module tests/unit/features/settings/components/delete-account-section
 * @description Verifica que la accion exige re-tipear el email exacto (boton
 *   deshabilitado hasta que coincide), el camino feliz (redirect /login) y el
 *   409 CANNOT_DELETE_ADMIN_ACCOUNT (no redirige, toast).
 */

const API = "https://api.test.the-full-stack.com";

const { replaceMock } = vi.hoisted(() => ({ replaceMock: vi.fn() }));
vi.mock("next/navigation", () => ({
	useRouter: () => ({ replace: replaceMock, push: vi.fn() }),
}));

beforeEach(() => {
	replaceMock.mockClear();
	useAuthStore.setState({
		user: {
			id: "usr_01",
			email: "user@test.com",
			status: "active",
			has_password: true,
			mfa_methods: [],
		},
	});
});

async function openDialog(user: ReturnType<typeof userEvent.setup>) {
	await user.click(
		screen.getByRole("button", { name: /^eliminar mi cuenta$/i }),
	);
}

describe("DeleteAccountSection", () => {
	it("Given email no coincide When abre el dialog Then el boton Eliminar cuenta esta deshabilitado", async () => {
		// Arrange
		const user = userEvent.setup();
		render((<DeleteAccountSection />) as ReactElement);

		// Act
		await openDialog(user);
		await user.type(screen.getByLabelText(/tu email/i), "otro@test.com");

		// Assert
		expect(
			screen.getByRole("button", { name: /eliminar cuenta/i }),
		).toBeDisabled();
	});

	it("Given email coincide When confirma Then redirige a /login", async () => {
		// Arrange
		const user = userEvent.setup();
		render((<DeleteAccountSection />) as ReactElement);

		// Act
		await openDialog(user);
		await user.type(screen.getByLabelText(/tu email/i), "user@test.com");
		await user.click(screen.getByRole("button", { name: /eliminar cuenta/i }));

		// Assert
		await waitFor(() => {
			expect(replaceMock).toHaveBeenCalledWith("/login");
		});
	});

	it("Given admin account When confirma Then 409 muestra error y NO redirige", async () => {
		// Arrange: forzar 409 CANNOT_DELETE_ADMIN_ACCOUNT
		server.use(
			http.post(`${API}/users`, () =>
				HttpResponse.json(
					{
						error: "CANNOT_DELETE_ADMIN_ACCOUNT",
						code: 4091,
						message: "No puedes eliminar una cuenta de administrador",
					},
					{ status: 409 },
				),
			),
		);
		const user = userEvent.setup();
		render((<DeleteAccountSection />) as ReactElement);

		// Act
		await openDialog(user);
		await user.type(screen.getByLabelText(/tu email/i), "user@test.com");
		await user.click(screen.getByRole("button", { name: /eliminar cuenta/i }));

		// Assert
		await waitFor(() => {
			expect(
				screen.getByText(/no puedes eliminar una cuenta de administrador/i),
			).toBeInTheDocument();
		});
		expect(replaceMock).not.toHaveBeenCalled();
	});
});
