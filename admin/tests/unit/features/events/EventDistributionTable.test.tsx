import { render, screen } from "@tests/utils/render";
import { describe, expect, it } from "vitest";
import { EventDistributionTable } from "@/features/events/components/EventDistributionTable";
import type { EventDistributionItem } from "@/features/events/types";

/**
 * @module tests/unit/features/events/EventDistributionTable
 * @description Tabla del ranking de tipos de evento: event_type + count + pct.
 *   Cubre el branch vacio (mensaje) y el branch con filas (renderiza cada fila
 *   con el pct formateado a 1 decimal).
 */

const ITEMS: EventDistributionItem[] = [
	{ event_type: "page_view", count: 300, pct: 0.6 },
	{ event_type: "click", count: 200, pct: 0.401 },
];

describe("EventDistributionTable", () => {
	it("Given items vacios When se renderiza Then muestra el mensaje de vacio", () => {
		// Arrange + Act
		render(<EventDistributionTable items={[]} />);

		// Assert
		expect(
			screen.getByText("Sin eventos en el rango seleccionado."),
		).toBeInTheDocument();
	});

	it("Given 2 filas When se renderiza Then muestra los event_type y counts", () => {
		// Arrange + Act
		render(<EventDistributionTable items={ITEMS} />);

		// Assert
		expect(screen.getByText("page_view")).toBeInTheDocument();
		expect(screen.getByText("click")).toBeInTheDocument();
		expect(screen.getByText("300")).toBeInTheDocument();
		expect(screen.getByText("200")).toBeInTheDocument();
	});

	it("Given un pct 0.6 When se renderiza Then lo formatea como 60.0%", () => {
		// Arrange + Act
		render(<EventDistributionTable items={ITEMS} />);

		// Assert: pct * 100 con 1 decimal
		expect(screen.getByText("60.0%")).toBeInTheDocument();
		expect(screen.getByText("40.1%")).toBeInTheDocument();
	});
});
