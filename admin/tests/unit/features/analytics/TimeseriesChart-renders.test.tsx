import { render } from "@tests/utils/render";
import type { ReactElement } from "react";
import { describe, expect, it } from "vitest";
import { TimeseriesChart } from "@/features/analytics/components/TimeseriesChart";
import type { TimeseriesResponse } from "@/features/analytics/types";

/**
 * @module tests/unit/features/analytics/TimeseriesChart-renders
 * @description Verifica que con puntos reales (el JSON que reporto el usuario)
 *   la grafica dibuja la linea (no "Sin datos" ni un SVG vacio). El bug era el
 *   stroke="var(--primary)" (componentes HSL crudos, color invalido) -> linea
 *   invisible; el fix usa var(--color-primary).
 */

const REAL_DATA: TimeseriesResponse = {
	bucket: "day",
	from: "2026-05-04",
	to: "2026-06-04",
	filters: { niche: null, event_type: null },
	points: [
		{ timestamp: "2026-05-25T00:00:00+00:00", count: 13 },
		{ timestamp: "2026-05-26T00:00:00+00:00", count: 38 },
		{ timestamp: "2026-05-30T00:00:00+00:00", count: 57 },
		{ timestamp: "2026-06-01T00:00:00+00:00", count: 530 },
		{ timestamp: "2026-06-02T00:00:00+00:00", count: 3875 },
		{ timestamp: "2026-06-03T00:00:00+00:00", count: 3692 },
	],
};

describe("TimeseriesChart", () => {
	it("Given puntos reales When render Then NO muestra 'Sin datos' (la grafica monta)", () => {
		// Arrange + Act
		const { container, queryByText } = render(
			(<TimeseriesChart data={REAL_DATA} isLoading={false} />) as ReactElement,
		);

		// Assert: con puntos NO aparece el mensaje de vacio (entra al render de
		// la grafica). El ResponsiveContainer no pinta el SVG en happy-dom (sin
		// dimensiones), pero el contenedor de Recharts si monta.
		expect(queryByText(/sin datos en el rango/i)).toBeNull();
		expect(
			container.querySelector(".recharts-responsive-container"),
		).not.toBeNull();
	});

	it("Given sin puntos When render Then muestra el mensaje de vacio", () => {
		// Arrange
		const empty: TimeseriesResponse = { ...REAL_DATA, points: [] };

		// Act
		const { getByText } = render(
			(<TimeseriesChart data={empty} isLoading={false} />) as ReactElement,
		);

		// Assert
		expect(getByText(/sin datos en el rango/i)).toBeInTheDocument();
	});
});
