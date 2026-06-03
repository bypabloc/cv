import { render } from "@tests/utils/render";
import { describe, expect, it } from "vitest";
import { RetentionChart } from "@/features/analytics/components/RetentionChart";
import type { RetentionResponse } from "@/features/analytics/types";

/**
 * @module tests/unit/features/analytics/RetentionChart
 * @description PieChart de Recharts + tasa de retorno. Cubre el branch loading
 *   (skeleton) y el de data (arma los slices + monta el ResponsiveContainer +
 *   formatea la tasa). El label "Tasa de retorno:" comparte <p> con el <span>
 *   del valor: el valor SI es su propio elemento, el label se valida por
 *   substring del container. SVG no se asserta (happy-dom).
 */

const DATA: RetentionResponse = {
	new_visitors: 60,
	returning_visitors: 15,
	total: 75,
	returning_rate: 0.2,
};

describe("RetentionChart", () => {
	it("Given isLoading true When se renderiza Then muestra el skeleton sin la tasa", () => {
		// Arrange + Act
		const { container } = render(
			<RetentionChart isLoading={true} data={undefined} />,
		);

		// Assert
		expect(container.querySelector(".h-64")).not.toBeNull();
		expect(container.textContent).not.toContain("Tasa de retorno:");
	});

	it("Given data undefined y isLoading false When se renderiza Then sigue mostrando skeleton", () => {
		// Arrange + Act
		const { container } = render(
			<RetentionChart isLoading={false} data={undefined} />,
		);

		// Assert
		expect(container.querySelector(".h-64")).not.toBeNull();
	});

	it("Given data When se renderiza Then monta el chart y muestra la tasa formateada", () => {
		// Arrange + Act
		const { container, getByText } = render(
			<RetentionChart isLoading={false} data={DATA} />,
		);

		// Assert: 0.2 -> 20.0% (el valor es su propio <span>) + wrapper Recharts
		expect(container.textContent).toContain("Tasa de retorno:");
		expect(getByText("20.0%")).toBeInTheDocument();
		expect(
			container.querySelector(".recharts-responsive-container"),
		).not.toBeNull();
	});
});
