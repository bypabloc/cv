import { render, screen, userEvent } from "@tests/utils/render";
import { describe, expect, it, vi } from "vitest";
import { DeleteEntityDialog } from "@/features/cv-management/components/delete-entity-dialog";

/**
 * @module tests/unit/features/cv-management/components/delete-entity-dialog
 * @description Verifica la confirmacion de borrado: abre con slug, confirma
 *   (onConfirm), cancela (onCancel) y deshabilita confirmar en vuelo.
 */

describe("DeleteEntityDialog", () => {
	it("Given un slug When se renderiza Then el dialog abre y lo menciona", () => {
		// Arrange + Act
		render(
			<DeleteEntityDialog
				slug="exp-a"
				pending={false}
				onConfirm={vi.fn()}
				onCancel={vi.fn()}
			/>,
		);

		// Assert
		expect(screen.getByText("Eliminar entrada")).toBeInTheDocument();
		expect(screen.getByText("exp-a")).toBeInTheDocument();
	});

	it("Given slug null When se renderiza Then el dialog no monta", () => {
		// Arrange + Act
		render(
			<DeleteEntityDialog
				slug={null}
				pending={false}
				onConfirm={vi.fn()}
				onCancel={vi.fn()}
			/>,
		);

		// Assert
		expect(screen.queryByText("Eliminar entrada")).not.toBeInTheDocument();
	});

	it("Given confirmar When se clickea Then dispara onConfirm", async () => {
		// Arrange
		const user = userEvent.setup();
		const onConfirm = vi.fn();
		render(
			<DeleteEntityDialog
				slug="exp-a"
				pending={false}
				onConfirm={onConfirm}
				onCancel={vi.fn()}
			/>,
		);

		// Act
		await user.click(screen.getByTestId("cv-entity-delete-confirm"));

		// Assert
		expect(onConfirm).toHaveBeenCalledTimes(1);
	});

	it("Given cancelar When se clickea Then dispara onCancel sin confirmar", async () => {
		// Arrange
		const user = userEvent.setup();
		const onConfirm = vi.fn();
		const onCancel = vi.fn();
		render(
			<DeleteEntityDialog
				slug="exp-a"
				pending={false}
				onConfirm={onConfirm}
				onCancel={onCancel}
			/>,
		);

		// Act
		await user.click(screen.getByTestId("cv-entity-delete-cancel"));

		// Assert
		expect(onCancel).toHaveBeenCalledTimes(1);
		expect(onConfirm).not.toHaveBeenCalled();
	});

	it("Given pending When se renderiza Then el boton confirmar esta deshabilitado", () => {
		// Arrange + Act
		render(
			<DeleteEntityDialog
				slug="exp-a"
				pending
				onConfirm={vi.fn()}
				onCancel={vi.fn()}
			/>,
		);

		// Assert
		expect(screen.getByTestId("cv-entity-delete-confirm")).toBeDisabled();
	});
});
