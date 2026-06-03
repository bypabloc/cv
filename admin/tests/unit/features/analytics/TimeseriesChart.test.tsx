import { render } from "@tests/utils/render";
import { describe, expect, it } from "vitest";
import { TimeseriesChart } from "@/features/analytics/components/TimeseriesChart";
import type { TimeseriesResponse } from "@/features/analytics/types";

/**
 * @module tests/unit/features/analytics/TimeseriesChart
 * @description LineChart de Recharts. Cubre los 3 branches: loading (skeleton),
 *   vacio (mensaje) y con data (monta el ResponsiveContainer + ejecuta la
 *   transformacion de puntos). En happy-dom el SVG no se pinta con dimensiones
 *   reales -> no se asserta sobre el SVG, solo el contenedor / branches.
 */

const DATA: TimeseriesResponse = {
	bucket: "day",
	points: [
		{ timestamp: "2026-05-01T00:00:00Z", count: 10 },
		{ timestamp: "2026-05-02T00:00:00Z", count: 20 },
	],
	from: "2026-04-27",
	to: "2026-05-28",
	filters: { niche: null, event_type: null },
};

describe("TimeseriesChart", () => {
	it("Given isLoading true When se renderiza Then muestra el skeleton (sin mensaje vacio)", () => {
		// Arrange + Act
		const { container, queryByText } = render(
			<TimeseriesChart isLoading={true} data={undefined} />,
		);

		// Assert
		expect(container.querySelector(".h-72")).not.toBeNull();
		expect(queryByText("Sin datos en el rango seleccionado.")).toBeNull();
	});

	it("Given data undefined y isLoading false When se renderiza Then sigue mostrando skeleton", () => {
		// Arrange + Act
		const { container } = render(
			<TimeseriesChart isLoading={false} data={undefined} />,
		);

		// Assert
		expect(container.querySelector(".h-72")).not.toBeNull();
	});

	it("Given data con 0 puntos When se renderiza Then muestra el mensaje vacio", () => {
		// Arrange
		const empty: TimeseriesResponse = { ...DATA, points: [] };

		// Act
		const { getByText } = render(
			<TimeseriesChart isLoading={false} data={empty} />,
		);

		// Assert
		expect(
			getByText("Sin datos en el rango seleccionado."),
		).toBeInTheDocument();
	});

	it("Given data con puntos When se renderiza Then monta el ResponsiveContainer sin crashear", () => {
		// Arrange + Act
		const { container } = render(
			<TimeseriesChart isLoading={false} data={DATA} />,
		);

		// Assert: el wrapper de Recharts existe (la transformacion .map ya corrio)
		expect(
			container.querySelector(".recharts-responsive-container"),
		).not.toBeNull();
	});
});
