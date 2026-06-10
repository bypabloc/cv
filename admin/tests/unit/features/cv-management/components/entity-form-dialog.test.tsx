import { render, screen, userEvent } from "@tests/utils/render";
import { describe, expect, it, vi } from "vitest";
import { EntityFormDialog } from "@/features/cv-management/components/entity-form-dialog";

/**
 * @module tests/unit/features/cv-management/components/entity-form-dialog
 * @description Verifica el dialog generico: render del titulo/descripcion y
 *   children cuando abre, nada cuando cierra, y onOpenChange al cerrar.
 */

describe("EntityFormDialog", () => {
	it("Given open When se renderiza Then muestra titulo, descripcion y children", () => {
		// Arrange + Act
		render(
			<EntityFormDialog
				open
				onOpenChange={vi.fn()}
				title="Nueva entrada"
				description="Experiencias"
			>
				<p>contenido del form</p>
			</EntityFormDialog>,
		);

		// Assert
		expect(screen.getByTestId("cv-entity-form-dialog")).toBeInTheDocument();
		expect(screen.getByText("Nueva entrada")).toBeInTheDocument();
		expect(screen.getByText("Experiencias")).toBeInTheDocument();
		expect(screen.getByText("contenido del form")).toBeInTheDocument();
	});

	it("Given open=false When se renderiza Then no monta el contenido", () => {
		// Arrange + Act
		render(
			<EntityFormDialog
				open={false}
				onOpenChange={vi.fn()}
				title="Nueva entrada"
			>
				<p>contenido del form</p>
			</EntityFormDialog>,
		);

		// Assert
		expect(
			screen.queryByTestId("cv-entity-form-dialog"),
		).not.toBeInTheDocument();
	});

	it("Given el dialog abierto When se presiona Escape Then emite onOpenChange(false)", async () => {
		// Arrange
		const user = userEvent.setup();
		const onOpenChange = vi.fn();
		render(
			<EntityFormDialog open onOpenChange={onOpenChange} title="Editar">
				<p>contenido</p>
			</EntityFormDialog>,
		);

		// Act
		await user.keyboard("{Escape}");

		// Assert
		expect(onOpenChange).toHaveBeenCalledWith(false);
	});
});
