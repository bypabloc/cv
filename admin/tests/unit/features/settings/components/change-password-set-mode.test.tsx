import { render, screen } from "@tests/utils/render";
import type { ReactElement } from "react";
import { describe, expect, it, vi } from "vitest";
import { ChangePasswordForm } from "@/features/settings/components/change-password-form";

/**
 * @module tests/unit/features/settings/components/change-password-set-mode
 * @description Verifica los dos modos del ChangePasswordForm: passwordless
 *   (`hasPassword=false` -> "Establecer contrasena", SIN campo "contrasena
 *   actual") y con contrasena (`hasPassword=true` -> SI muestra la actual).
 */

vi.mock("@/features/settings/hooks/use-change-password", () => ({
	useChangePassword: () => ({ mutate: vi.fn(), isPending: false }),
}));

describe("ChangePasswordForm modo establecer", () => {
	it("Given hasPassword false When render Then muestra Establecer contrasena SIN campo contrasena actual", () => {
		// Arrange + Act
		render((<ChangePasswordForm hasPassword={false} />) as ReactElement);

		// Assert: titulo + boton de set-mode (ambos dicen "Establecer
		// contrasena") + sin campo "contrasena actual" + campos nuevos.
		expect(screen.getAllByText("Establecer contrasena")).toHaveLength(2);
		expect(
			screen.getByRole("button", { name: /establecer contrasena/i }),
		).toBeInTheDocument();
		expect(screen.queryByLabelText(/contrasena actual/i)).toBeNull();
		expect(screen.getByLabelText(/^nueva contrasena$/i)).toBeInTheDocument();
		expect(
			screen.getByLabelText(/confirmar nueva contrasena/i),
		).toBeInTheDocument();
	});

	it("Given hasPassword true When render Then SI muestra el campo contrasena actual", () => {
		// Arrange + Act
		render((<ChangePasswordForm hasPassword={true} />) as ReactElement);

		// Assert: modo cambio -> campo de la contrasena actual presente
		expect(screen.getByLabelText(/contrasena actual/i)).toBeInTheDocument();
	});
});
