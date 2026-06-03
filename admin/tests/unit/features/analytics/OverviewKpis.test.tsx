import { render, screen } from "@tests/utils/render";
import { describe, expect, it } from "vitest";
import { OverviewKpis } from "@/features/analytics/components/OverviewKpis";
import type { OverviewResponse } from "@/features/analytics/types";

/**
 * @module tests/unit/features/analytics/OverviewKpis
 * @description OverviewKpis: grid de 7 KPI cards. Skeleton mientras carga;
 *   con data formatea int / duracion / porcentaje.
 */

const DATA: OverviewResponse = {
	sessions: 12345,
	visits: 80,
	events: 500,
	contacts: 5,
	unique_visitors: 75,
	avg_visit_duration_sec: 3725, // 1h 2m
	bounce_rate: 0.156,
	from: "2026-04-27",
	to: "2026-05-28",
};

describe("OverviewKpis", () => {
	it("Given isLoading true When se renderiza Then muestra las 7 etiquetas (estado skeleton)", () => {
		// Arrange + Act
		render(<OverviewKpis isLoading={true} />);

		// Assert: las etiquetas siempre se renderizan; el valor es skeleton
		expect(screen.getByText("Sesiones")).toBeInTheDocument();
		expect(screen.getByText("Tasa de rebote")).toBeInTheDocument();
		expect(screen.queryByText("12.345")).not.toBeInTheDocument();
	});

	it("Given data sin loading When se renderiza Then formatea los enteros con separador de miles", () => {
		// Arrange + Act
		render(<OverviewKpis data={DATA} isLoading={false} />);

		// Assert: 12345 -> "12.345" (grouping es a partir de 5 digitos)
		expect(screen.getByText("12.345")).toBeInTheDocument();
		expect(screen.getByText("75")).toBeInTheDocument();
	});

	it("Given una duracion > 1h When se renderiza Then la formatea como horas y minutos", () => {
		// Arrange + Act
		render(<OverviewKpis data={DATA} isLoading={false} />);

		// Assert: 3725s -> 1h 2m
		expect(screen.getByText("1h 2m")).toBeInTheDocument();
	});

	it("Given un bounce_rate When se renderiza Then lo formatea como porcentaje", () => {
		// Arrange + Act
		render(<OverviewKpis data={DATA} isLoading={false} />);

		// Assert: 0.156 -> 15.6%
		expect(screen.getByText("15.6%")).toBeInTheDocument();
	});

	it("Given una duracion < 1m When se renderiza Then la formatea en segundos", () => {
		// Arrange
		const data: OverviewResponse = { ...DATA, avg_visit_duration_sec: 45 };

		// Act
		render(<OverviewKpis data={data} isLoading={false} />);

		// Assert
		expect(screen.getByText("45s")).toBeInTheDocument();
	});

	it("Given una duracion de minutos When se renderiza Then la formatea en minutos y segundos", () => {
		// Arrange
		const data: OverviewResponse = { ...DATA, avg_visit_duration_sec: 125 };

		// Act
		render(<OverviewKpis data={data} isLoading={false} />);

		// Assert: 125s -> 2m 5s
		expect(screen.getByText("2m 5s")).toBeInTheDocument();
	});
});
