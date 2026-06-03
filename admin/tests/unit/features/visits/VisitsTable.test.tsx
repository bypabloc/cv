import { render, screen, within } from "@tests/utils/render";
import { describe, expect, it } from "vitest";
import { VisitsTable } from "@/features/visits/components/VisitsTable";
import type { VisitRow } from "@/features/visits/types";

/**
 * @module tests/unit/features/visits/VisitsTable
 * @description Render de la tabla de visitas: filas con country/niche/referrer/
 *   landing/event_count, fallback "-" en nullables y mensaje vacio.
 */

const ROW: VisitRow = {
	visit_id: "vis_1",
	session_id: "sess_1",
	started_at: "2026-05-01T10:00:00Z",
	ended_at: "2026-05-01T10:05:00Z",
	event_count: 3,
	ip: "1.2.3.4",
	country: "AR",
	utm_source: null,
	utm_medium: null,
	utm_campaign: null,
	referrer: "(direct)",
	landing_page_path: "/blog",
	niche: "fintech",
};

describe("VisitsTable", () => {
	it("Given un array vacio When se renderiza Then muestra el mensaje vacio", () => {
		// Arrange + Act
		render(<VisitsTable items={[]} />);

		// Assert
		expect(
			screen.getByText("Sin visitas en el rango seleccionado."),
		).toBeInTheDocument();
	});

	it("Given una visita When se renderiza Then muestra sus columnas con data", () => {
		// Arrange + Act
		render(<VisitsTable items={[ROW]} />);

		// Assert
		expect(screen.getByText("AR")).toBeInTheDocument();
		expect(screen.getByText("fintech")).toBeInTheDocument();
		expect(screen.getByText("(direct)")).toBeInTheDocument();
		expect(screen.getByText("/blog")).toBeInTheDocument();
		expect(screen.getByText("3")).toBeInTheDocument();
	});

	it("Given los headers de la tabla When se renderiza con data Then los muestra", () => {
		// Arrange + Act
		render(<VisitsTable items={[ROW]} />);

		// Assert
		expect(screen.getByText("Inicio")).toBeInTheDocument();
		expect(screen.getByText("Pais")).toBeInTheDocument();
		expect(screen.getByText("Niche")).toBeInTheDocument();
		expect(screen.getByText("Referrer")).toBeInTheDocument();
		expect(screen.getByText("Landing")).toBeInTheDocument();
		expect(screen.getByText("Eventos")).toBeInTheDocument();
	});

	it('Given una visita con country/niche/referrer/landing nulos When se renderiza Then muestra "-" en esas celdas', () => {
		// Arrange
		const nullRow: VisitRow = {
			...ROW,
			visit_id: "vis_null",
			country: null,
			niche: null,
			referrer: null,
			landing_page_path: null,
		};

		// Act
		render(<VisitsTable items={[nullRow]} />);
		const row = screen.getByText("3").closest("tr");
		if (!row) throw new Error("fila de la visita null no encontrada");

		// Assert: country, niche, referrer, landing caen al fallback "-"
		const dashes = within(row).getAllByText("-");
		expect(dashes).toHaveLength(4);
	});
});
