import { render } from "@tests/utils/render";
import { describe, expect, it } from "vitest";
import { TopNichesChart } from "@/features/analytics/components/TopNichesChart";
import type { TopNichesResponse } from "@/features/analytics/types";

/**
 * @module tests/unit/features/analytics/TopNichesChart
 * @description BarChart de Recharts. Cubre los 3 branches: loading (skeleton),
 *   vacio (mensaje) y con data (monta el ResponsiveContainer). En happy-dom el
 *   SVG no se pinta con dimensiones reales -> no se asserta sobre el SVG.
 */

const DATA: TopNichesResponse = {
	items: [
		{ niche: "fintech", visits: 30, unique_visitors: 20 },
		{ niche: "architect", visits: 15, unique_visitors: 10 },
	],
};

describe("TopNichesChart", () => {
	it("Given isLoading true When se renderiza Then muestra el skeleton (sin mensaje vacio)", () => {
		// Arrange + Act
		const { container, queryByText } = render(
			<TopNichesChart isLoading={true} data={undefined} />,
		);

		// Assert
		expect(container.querySelector(".h-64")).not.toBeNull();
		expect(queryByText("Sin datos en el rango seleccionado.")).toBeNull();
	});

	it("Given data undefined y isLoading false When se renderiza Then sigue mostrando skeleton", () => {
		// Arrange + Act
		const { container } = render(
			<TopNichesChart isLoading={false} data={undefined} />,
		);

		// Assert
		expect(container.querySelector(".h-64")).not.toBeNull();
	});

	it("Given items vacios When se renderiza Then muestra el mensaje vacio", () => {
		// Arrange + Act
		const { getByText } = render(
			<TopNichesChart isLoading={false} data={{ items: [] }} />,
		);

		// Assert
		expect(
			getByText("Sin datos en el rango seleccionado."),
		).toBeInTheDocument();
	});

	it("Given items con data When se renderiza Then monta el ResponsiveContainer sin crashear", () => {
		// Arrange + Act
		const { container } = render(
			<TopNichesChart isLoading={false} data={DATA} />,
		);

		// Assert
		expect(
			container.querySelector(".recharts-responsive-container"),
		).not.toBeNull();
	});
});
