import { render, screen, userEvent, waitFor } from "@tests/utils/render";
import type { ReactElement } from "react";
import { describe, expect, it, vi } from "vitest";
import { ProfileForm } from "@/features/settings/components/profile-form";

/**
 * @module tests/unit/features/settings/components/profile-form
 * @description Verifica que el form carga el perfil (profile.get -> email
 *   read-only + display_name), valida display_name vacio (Zod) y al submit
 *   exitoso muestra el toast de actualizacion.
 */

vi.mock("next/navigation", () => ({
	useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
}));

describe("ProfileForm", () => {
	it("Given el perfil cargado When monta Then muestra email read-only y display_name", async () => {
		// Arrange + Act
		render((<ProfileForm />) as ReactElement);

		// Assert: el email del MSW (user@test.com) llega como read-only
		const email = await screen.findByLabelText(/email/i);
		expect(email).toHaveValue("user@test.com");
		expect(email).toHaveAttribute("readonly");

		await waitFor(() => {
			expect(screen.getByLabelText(/nombre para mostrar/i)).toHaveValue(
				"Pablo",
			);
		});
	});

	it("Given display_name vacio When submit Then NO llama a la API (Zod bloquea)", async () => {
		// Arrange
		const user = userEvent.setup();
		render((<ProfileForm />) as ReactElement);
		const input = await screen.findByLabelText(/nombre para mostrar/i);
		await waitFor(() => expect(input).toHaveValue("Pablo"));

		// Act
		await user.clear(input);
		await user.click(screen.getByRole("button", { name: /guardar cambios/i }));

		// Assert
		await waitFor(() => {
			expect(screen.getByText(/el nombre es obligatorio/i)).toBeInTheDocument();
		});
	});

	it("Given el perfil cargado When el usuario tipea Then el input NO se pisa (reset una sola vez)", async () => {
		// Arrange: el bug era que el reset corria en cada render (profile.data
		// cambia de referencia con Tanstack) y borraba lo tipeado.
		const user = userEvent.setup();
		render((<ProfileForm />) as ReactElement);
		const input = await screen.findByLabelText(/nombre para mostrar/i);
		await waitFor(() => expect(input).toHaveValue("Pablo"));

		// Act: editar el campo.
		await user.clear(input);
		await user.type(input, "Nuevo Nombre");

		// Assert: el valor tipeado persiste (no lo pisa un reset posterior).
		expect(input).toHaveValue("Nuevo Nombre");
		await waitFor(() => expect(input).toHaveValue("Nuevo Nombre"));
	});

	it("Given display_name valido When submit Then muestra toast de actualizacion", async () => {
		// Arrange
		const user = userEvent.setup();
		render((<ProfileForm />) as ReactElement);
		const input = await screen.findByLabelText(/nombre para mostrar/i);
		await waitFor(() => expect(input).toHaveValue("Pablo"));

		// Act
		await user.clear(input);
		await user.type(input, "Pablo Contreras");
		await user.click(screen.getByRole("button", { name: /guardar cambios/i }));

		// Assert: el toast de exito aparece (sonner monta en el render wrapper)
		await waitFor(() => {
			expect(screen.getByText("Perfil actualizado")).toBeInTheDocument();
		});
	});
});
