import { render } from "@tests/utils/render";
import { describe, expect, it } from "vitest";
import { EventHeatmap } from "@/features/events/components/EventHeatmap";
import type { HeatmapResponse } from "@/features/events/types";

/**
 * @module tests/unit/features/events/EventHeatmap
 * @description Grilla 7x24 de eventos (events/heatmap). Cubre loading (skeleton),
 *   vacio (mensaje), con data (calcula intensidad por celda) y el caso borde
 *   max=0 (todas las celdas con count 0 -> opacidad 0).
 */

const DATA: HeatmapResponse = {
	cells: [
		{ dow: 1, hour: 9, count: 12 },
		{ dow: 3, hour: 14, count: 8 },
	],
};

describe("EventHeatmap", () => {
	it("Given isLoading true When se renderiza Then muestra el skeleton", () => {
		// Arrange + Act
		const { container, queryByText } = render(
			<EventHeatmap isLoading={true} />,
		);

		// Assert
		expect(container.querySelector(".h-72")).not.toBeNull();
		expect(queryByText("Sin eventos en el rango seleccionado.")).toBeNull();
	});

	it("Given data undefined y isLoading false When se renderiza Then sigue mostrando skeleton", () => {
		// Arrange + Act
		const { container } = render(
			<EventHeatmap isLoading={false} data={undefined} />,
		);

		// Assert
		expect(container.querySelector(".h-72")).not.toBeNull();
	});

	it("Given celdas vacias When se renderiza Then muestra el mensaje de vacio", () => {
		// Arrange + Act
		const { getByText } = render(
			<EventHeatmap isLoading={false} data={{ cells: [] }} />,
		);

		// Assert
		expect(
			getByText("Sin eventos en el rango seleccionado."),
		).toBeInTheDocument();
	});

	it("Given celdas con data When se renderiza Then muestra los 7 labels de dia", () => {
		// Arrange + Act
		const { getByText } = render(
			<EventHeatmap isLoading={false} data={DATA} />,
		);

		// Assert: los labels de dia de semana
		for (const label of ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom"]) {
			expect(getByText(label)).toBeInTheDocument();
		}
	});

	it("Given una celda con count When se renderiza Then su title incluye el conteo de eventos", () => {
		// Arrange + Act
		const { getByTitle } = render(
			<EventHeatmap isLoading={false} data={DATA} />,
		);

		// Assert: la celda (dow=1=Lun, hour=9) lleva su title con el count
		expect(getByTitle("Lun 09:00 — 12 eventos")).toBeInTheDocument();
		// Y una celda sin dato cae al fallback count 0
		expect(getByTitle("Lun 00:00 — 0 eventos")).toBeInTheDocument();
	});

	it("Given todas las celdas con count 0 When se renderiza Then no crashea (max=0 -> opacidad 0)", () => {
		// Arrange: cells presentes (no vacio) pero todas con count 0 -> branch max=0
		const zeros: HeatmapResponse = {
			cells: [
				{ dow: 1, hour: 0, count: 0 },
				{ dow: 2, hour: 1, count: 0 },
			],
		};

		// Act
		const { getByTitle } = render(
			<EventHeatmap isLoading={false} data={zeros} />,
		);

		// Assert: la grilla se monta y la celda con count 0 lleva opacidad 0
		const cell = getByTitle("Lun 00:00 — 0 eventos");
		expect(cell).toHaveStyle({ opacity: "0" });
	});
});
