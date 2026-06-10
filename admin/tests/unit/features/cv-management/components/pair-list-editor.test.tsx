import { render, screen, userEvent } from "@tests/utils/render";
import { describe, expect, it, vi } from "vitest";
import { PairListEditor } from "@/features/cv-management/components/pair-list-editor";

/**
 * @module tests/unit/features/cv-management/components/pair-list-editor
 * @description Verifica el editor de pares ordenados (links/metricas):
 *   agregar/editar/eliminar filas y el reorden (prefijo-up/down) cuando es
 *   reorderable.
 */

const PAIRS = [
	{ key: "lighthouse", value: "100" },
	{ key: "visitors", value: "5k" },
];

describe("PairListEditor", () => {
	it("Given pares When se renderiza Then una fila por par con el prefijo de testid", () => {
		// Arrange + Act
		render(
			<PairListEditor
				label="Metricas"
				keyLabel="Clave"
				valueLabel="Valor"
				value={PAIRS}
				onChange={vi.fn()}
				testIdPrefix="cv-metric"
			/>,
		);

		// Assert
		expect(screen.getAllByTestId("cv-metric-row")).toHaveLength(2);
		expect(screen.getAllByTestId("cv-metric-key")[0]).toHaveValue("lighthouse");
		expect(screen.getAllByTestId("cv-metric-value")[1]).toHaveValue("5k");
	});

	it("Given agregar When se clickea Then proyecta una fila vacia", async () => {
		// Arrange
		const user = userEvent.setup();
		const onChange = vi.fn();
		render(
			<PairListEditor
				label="Links"
				keyLabel="Etiqueta"
				valueLabel="URL"
				value={[]}
				onChange={onChange}
				testIdPrefix="cv-link"
			/>,
		);

		// Act
		await user.click(screen.getByTestId("cv-link-add"));

		// Assert
		expect(onChange).toHaveBeenCalledWith([{ key: "", value: "" }]);
	});

	it("Given una fila When se edita el value Then proyecta el par actualizado", async () => {
		// Arrange
		const user = userEvent.setup();
		const onChange = vi.fn();
		render(
			<PairListEditor
				label="Metricas"
				keyLabel="Clave"
				valueLabel="Valor"
				value={[{ key: "n", value: "1" }]}
				onChange={onChange}
				testIdPrefix="cv-metric"
			/>,
		);

		// Act
		await user.type(screen.getByTestId("cv-metric-value"), "0");

		// Assert
		expect(onChange).toHaveBeenLastCalledWith([{ key: "n", value: "10" }]);
	});

	it("Given eliminar de la fila 0 When se clickea Then proyecta sin esa fila", async () => {
		// Arrange
		const user = userEvent.setup();
		const onChange = vi.fn();
		render(
			<PairListEditor
				label="Metricas"
				keyLabel="Clave"
				valueLabel="Valor"
				value={PAIRS}
				onChange={onChange}
				testIdPrefix="cv-metric"
			/>,
		);

		// Act
		await user.click(
			screen.getAllByTestId("cv-metric-remove")[0] as HTMLElement,
		);

		// Assert
		expect(onChange).toHaveBeenCalledWith([{ key: "visitors", value: "5k" }]);
	});

	it("Given reorderable When se sube la fila 1 Then proyecta el orden invertido", async () => {
		// Arrange
		const user = userEvent.setup();
		const onChange = vi.fn();
		render(
			<PairListEditor
				label="Metricas"
				keyLabel="Clave"
				valueLabel="Valor"
				value={PAIRS}
				onChange={onChange}
				testIdPrefix="cv-metric"
				reorderable
			/>,
		);

		// Act
		await user.click(screen.getAllByTestId("cv-metric-up")[1] as HTMLElement);

		// Assert
		expect(onChange).toHaveBeenCalledWith([
			{ key: "visitors", value: "5k" },
			{ key: "lighthouse", value: "100" },
		]);
	});

	it("Given NO reorderable When se renderiza Then no hay botones up/down", () => {
		// Arrange + Act
		render(
			<PairListEditor
				label="Links"
				keyLabel="Etiqueta"
				valueLabel="URL"
				value={PAIRS}
				onChange={vi.fn()}
				testIdPrefix="cv-link"
			/>,
		);

		// Assert
		expect(screen.queryByTestId("cv-link-up")).not.toBeInTheDocument();
		expect(screen.queryByTestId("cv-link-down")).not.toBeInTheDocument();
	});

	it("Given un error del schema When se renderiza Then lo muestra como alert", () => {
		// Arrange + Act
		render(
			<PairListEditor
				label="Links"
				keyLabel="Etiqueta"
				valueLabel="URL"
				value={[]}
				onChange={vi.fn()}
				testIdPrefix="cv-link"
				error="Campo obligatorio"
			/>,
		);

		// Assert
		expect(screen.getByRole("alert")).toHaveTextContent("Campo obligatorio");
	});
});
