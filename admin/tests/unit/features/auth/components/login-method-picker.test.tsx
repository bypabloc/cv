import { render, screen, userEvent } from "@tests/utils/render";
import type { ReactElement } from "react";
import { describe, expect, it, vi } from "vitest";
import {
	LoginMethodPicker,
	type PickerMethod,
} from "@/features/auth/components/login-method-picker";

/**
 * @module tests/unit/features/auth/components/login-method-picker
 * @description Tests de la lista selectora de metodos de login: renderiza una
 *   fila por metodo (icono + titulo + descripcion + chevron), marca con check y
 *   deshabilita los completados, y emite onSelect al elegir un pendiente.
 */

const PASSWORD_TOTP: PickerMethod[] = [
	{ type: "password", satisfied: false },
	{ type: "totp", satisfied: false },
];

describe("LoginMethodPicker", () => {
	it("Given dos metodos pendientes When se monta Then una fila por metodo con su titulo", () => {
		// Arrange / Act
		render(
			(
				<LoginMethodPicker methods={PASSWORD_TOTP} onSelect={vi.fn()} />
			) as ReactElement,
		);

		// Assert: una fila por metodo, accionables
		expect(screen.getByTestId("picker-method-password")).toBeInTheDocument();
		expect(screen.getByTestId("picker-method-totp")).toBeInTheDocument();
		expect(screen.getByText("Contrasena")).toBeInTheDocument();
		expect(screen.getByText("Codigo TOTP")).toBeInTheDocument();
		expect(screen.getByText("Ingresaras tu contrasena.")).toBeInTheDocument();
	});

	it("Given click en una fila pendiente When se clickea Then onSelect recibe su type", async () => {
		// Arrange
		const user = userEvent.setup();
		const onSelect = vi.fn();
		render(
			(
				<LoginMethodPicker methods={PASSWORD_TOTP} onSelect={onSelect} />
			) as ReactElement,
		);

		// Act
		await user.click(screen.getByTestId("picker-method-totp"));

		// Assert
		expect(onSelect).toHaveBeenCalledTimes(1);
		expect(onSelect).toHaveBeenCalledWith("totp");
	});

	it("Given un metodo completado When se monta Then su fila esta deshabilitada y no llama onSelect", async () => {
		// Arrange
		const user = userEvent.setup();
		const onSelect = vi.fn();
		render(
			(
				<LoginMethodPicker
					methods={[
						{ type: "password", satisfied: true },
						{ type: "totp", satisfied: false },
					]}
					onSelect={onSelect}
				/>
			) as ReactElement,
		);

		// Act: el password completado esta disabled -> el click no dispara onSelect
		const passwordRow = screen.getByTestId("picker-method-password");
		expect(passwordRow).toBeDisabled();
		await user.click(passwordRow);

		// Assert: el completado muestra el check y NO llama onSelect
		expect(onSelect).not.toHaveBeenCalled();
		expect(screen.getByLabelText("Completado")).toBeInTheDocument();
	});

	it("Given un metodo passkey When se monta Then muestra el titulo y la descripcion de passkey", () => {
		// Arrange / Act
		render(
			(
				<LoginMethodPicker
					methods={[{ type: "webauthn", satisfied: false }]}
					onSelect={vi.fn()}
				/>
			) as ReactElement,
		);

		// Assert
		expect(screen.getByText("Passkey")).toBeInTheDocument();
		expect(
			screen.getByText("Usa tu huella, rostro o llave de seguridad."),
		).toBeInTheDocument();
	});
});
