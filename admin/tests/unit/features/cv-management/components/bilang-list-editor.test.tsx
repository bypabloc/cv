import { render, screen, userEvent } from "@tests/utils/render";
import { describe, expect, it, vi } from "vitest";
import { BiLangListEditor } from "@/features/cv-management/components/bilang-list-editor";

/**
 * @module tests/unit/features/cv-management/components/bilang-list-editor
 * @description Verifica el editor de listas paralelas es/en: agregar,
 *   eliminar, editar y reordenar items (bilang-item-up/down) proyectando
 *   {es: [], en: []} en cada cambio.
 */

const TWO_ROWS = { es: ["uno", "dos"], en: ["one", "two"] };

describe("BiLangListEditor", () => {
	it("Given listas paralelas When se renderiza Then muestra una fila por par", () => {
		// Arrange + Act
		render(
			<BiLangListEditor
				name="responsibilities"
				label="Responsabilidades"
				value={TWO_ROWS}
				onChange={vi.fn()}
			/>,
		);

		// Assert
		expect(screen.getAllByTestId("bilang-item-row")).toHaveLength(2);
		const esInputs = screen.getAllByTestId("bilang-item-es");
		expect(esInputs[0]).toHaveValue("uno");
		expect(esInputs[1]).toHaveValue("dos");
	});

	it("Given el boton agregar When se clickea Then proyecta una fila vacia nueva", async () => {
		// Arrange
		const user = userEvent.setup();
		const onChange = vi.fn();
		render(
			<BiLangListEditor
				name="responsibilities"
				label="Responsabilidades"
				value={TWO_ROWS}
				onChange={onChange}
			/>,
		);

		// Act
		await user.click(screen.getByTestId("bilang-item-add"));

		// Assert
		expect(onChange).toHaveBeenCalledWith({
			es: ["uno", "dos", ""],
			en: ["one", "two", ""],
		});
		expect(screen.getAllByTestId("bilang-item-row")).toHaveLength(3);
	});

	it("Given el boton eliminar de la fila 0 When se clickea Then proyecta sin esa fila", async () => {
		// Arrange
		const user = userEvent.setup();
		const onChange = vi.fn();
		render(
			<BiLangListEditor
				name="responsibilities"
				label="Responsabilidades"
				value={TWO_ROWS}
				onChange={onChange}
			/>,
		);

		// Act
		const removeButtons = screen.getAllByTestId("bilang-item-remove");
		await user.click(removeButtons[0] as HTMLElement);

		// Assert
		expect(onChange).toHaveBeenCalledWith({ es: ["dos"], en: ["two"] });
	});

	it("Given bilang-item-up de la fila 1 When se clickea Then sube el item a la posicion 0", async () => {
		// Arrange
		const user = userEvent.setup();
		const onChange = vi.fn();
		render(
			<BiLangListEditor
				name="achievements"
				label="Logros"
				value={TWO_ROWS}
				onChange={onChange}
			/>,
		);

		// Act
		const upButtons = screen.getAllByTestId("bilang-item-up");
		await user.click(upButtons[1] as HTMLElement);

		// Assert: orden visual y proyeccion invertidos.
		expect(onChange).toHaveBeenCalledWith({
			es: ["dos", "uno"],
			en: ["two", "one"],
		});
		const esInputs = screen.getAllByTestId("bilang-item-es");
		expect(esInputs[0]).toHaveValue("dos");
	});

	it("Given bilang-item-down de la fila 0 When se clickea Then baja el item", async () => {
		// Arrange
		const user = userEvent.setup();
		const onChange = vi.fn();
		render(
			<BiLangListEditor
				name="achievements"
				label="Logros"
				value={TWO_ROWS}
				onChange={onChange}
			/>,
		);

		// Act
		const downButtons = screen.getAllByTestId("bilang-item-down");
		await user.click(downButtons[0] as HTMLElement);

		// Assert
		expect(onChange).toHaveBeenCalledWith({
			es: ["dos", "uno"],
			en: ["two", "one"],
		});
	});

	it("Given los extremos When se inspeccionan Then up de la fila 0 y down de la ultima estan deshabilitados", () => {
		// Arrange + Act
		render(
			<BiLangListEditor
				name="achievements"
				label="Logros"
				value={TWO_ROWS}
				onChange={vi.fn()}
			/>,
		);

		// Assert
		expect(screen.getAllByTestId("bilang-item-up")[0]).toBeDisabled();
		expect(screen.getAllByTestId("bilang-item-down")[1]).toBeDisabled();
	});

	it("Given un input es When se tipea Then proyecta el texto solo en esa fila", async () => {
		// Arrange: 2 filas para verificar que la otra no cambia.
		const user = userEvent.setup();
		const onChange = vi.fn();
		render(
			<BiLangListEditor
				name="responsibilities"
				label="Responsabilidades"
				value={TWO_ROWS}
				onChange={onChange}
			/>,
		);

		// Act
		await user.type(
			screen.getAllByTestId("bilang-item-es")[0] as HTMLElement,
			"!",
		);

		// Assert
		expect(onChange).toHaveBeenLastCalledWith({
			es: ["uno!", "dos"],
			en: ["one", "two"],
		});
	});

	it("Given un input en When se tipea Then proyecta el texto en la posicion correcta", async () => {
		// Arrange
		const user = userEvent.setup();
		const onChange = vi.fn();
		render(
			<BiLangListEditor
				name="responsibilities"
				label="Responsabilidades"
				value={{ es: ["uno"], en: ["one"] }}
				onChange={onChange}
			/>,
		);

		// Act
		await user.type(screen.getByTestId("bilang-item-en"), "!");

		// Assert
		expect(onChange).toHaveBeenLastCalledWith({ es: ["uno"], en: ["one!"] });
	});

	it("Given listas desparejas When se renderiza Then completa la fila corta con vacio", () => {
		// Arrange + Act: es trae 2 items, en solo 1 -> la fila 1 muestra en="".
		render(
			<BiLangListEditor
				name="responsibilities"
				label="Responsabilidades"
				value={{ es: ["uno", "dos"], en: ["one"] }}
				onChange={vi.fn()}
			/>,
		);

		// Assert
		const enInputs = screen.getAllByTestId("bilang-item-en");
		expect(enInputs[0]).toHaveValue("one");
		expect(enInputs[1]).toHaveValue("");
	});

	it("Given un error del schema When se renderiza Then lo muestra como alert", () => {
		// Arrange + Act
		render(
			<BiLangListEditor
				name="responsibilities"
				label="Responsabilidades"
				value={{ es: [], en: [] }}
				onChange={vi.fn()}
				error="Completa ambos idiomas en cada bullet"
			/>,
		);

		// Assert
		expect(screen.getByRole("alert")).toHaveTextContent(
			"Completa ambos idiomas en cada bullet",
		);
	});
});
