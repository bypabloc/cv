import { render } from "@tests/utils/render";
import { describe, expect, it } from "vitest";
import { EventDistributionChart } from "@/features/events/components/EventDistributionChart";
import type { EventDistributionResponse } from "@/features/events/types";

/**
 * @module tests/unit/features/events/EventDistributionChart
 * @description BarChart de Recharts del ranking de tipos de evento. Cubre los 3
 *   branches: loading (skeleton), vacio (mensaje) y con data (no crashea +
 *   ejecuta la transformacion). En happy-dom el SVG no renderiza con dimensiones
 *   reales -> no se asserta sobre el SVG, solo el contenedor / branches.
 */

const DATA: EventDistributionResponse = {
	items: [
		{ event_type: "page_view", count: 300, pct: 0.6 },
		{ event_type: "click", count: 200, pct: 0.4 },
	],
};

describe("EventDistributionChart", () => {
	it("Given isLoading true When se renderiza Then muestra el skeleton (sin mensaje vacio)", () => {
		// Arrange + Act
		const { container, queryByText } = render(
			<EventDistributionChart isLoading={true} />,
		);

		// Assert: el skeleton es un div con la clase de tamano; no hay mensaje vacio
		expect(container.querySelector(".h-64")).not.toBeNull();
		expect(queryByText("Sin eventos en el rango seleccionado.")).toBeNull();
	});

	it("Given data undefined y isLoading false When se renderiza Then sigue mostrando skeleton", () => {
		// Arrange + Act
		const { container } = render(
			<EventDistributionChart isLoading={false} data={undefined} />,
		);

		// Assert
		expect(container.querySelector(".h-64")).not.toBeNull();
	});

	it("Given items vacios When se renderiza Then muestra el mensaje de vacio", () => {
		// Arrange + Act
		const { getByText } = render(
			<EventDistributionChart isLoading={false} data={{ items: [] }} />,
		);

		// Assert
		expect(
			getByText("Sin eventos en el rango seleccionado."),
		).toBeInTheDocument();
	});

	it("Given items con data When se renderiza Then monta el ResponsiveContainer sin crashear", () => {
		// Arrange + Act
		const { container } = render(
			<EventDistributionChart isLoading={false} data={DATA} />,
		);

		// Assert: el wrapper de Recharts existe; no se assertan paths del SVG
		expect(
			container.querySelector(".recharts-responsive-container"),
		).not.toBeNull();
	});
});
