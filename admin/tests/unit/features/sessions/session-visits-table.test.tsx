import { render, screen, within } from "@tests/utils/render";
import { describe, expect, it } from "vitest";
import { SessionVisitsTable } from "@/features/sessions/components/SessionVisitsTable";
import type { VisitRow } from "@/features/sessions/types";

/**
 * @module tests/unit/features/sessions/session-visits-table
 * @description Render de la tabla de visitas de una sesion: mensaje vacio sin
 *   visitas; con visitas muestra landing, niche, pais y la combinacion UTM
 *   (source/medium/campaign). Cubre los fallbacks "-" de campos vacios.
 */

const VISIT: VisitRow = {
	visit_id: "vis_1",
	started_at: "2026-05-01T10:00:00Z",
	ended_at: "2026-05-01T10:05:00Z",
	event_count: 3,
	ip: "1.2.3.4",
	country: "AR",
	utm_source: "google",
	utm_medium: "cpc",
	utm_campaign: "launch",
	referrer: "https://google.com",
	landing_page_path: "/",
	niche: "fintech",
};

describe("SessionVisitsTable", () => {
	it("Given sin visitas When se renderiza Then muestra el mensaje vacio", () => {
		// Arrange + Act
		render(<SessionVisitsTable visits={[]} />);

		// Assert
		expect(
			screen.getByText("Esta sesion no tiene visitas registradas."),
		).toBeInTheDocument();
	});

	it("Given una visita con UTM completos When se renderiza Then muestra landing, niche, pais y UTM unidos", () => {
		// Arrange + Act
		render(<SessionVisitsTable visits={[VISIT]} />);

		// Assert
		expect(screen.getByText("/")).toBeInTheDocument();
		expect(screen.getByText("fintech")).toBeInTheDocument();
		expect(screen.getByText("AR")).toBeInTheDocument();
		expect(screen.getByText("google / cpc / launch")).toBeInTheDocument();
		expect(screen.getByText("3")).toBeInTheDocument();
	});

	it("Given una visita sin UTM, niche ni landing When se renderiza Then esos campos caen al fallback '-'", () => {
		// Arrange: landing, niche, referrer, country y los 3 utm vacios
		const empty: VisitRow = {
			...VISIT,
			landing_page_path: "",
			niche: "",
			referrer: "",
			country: "",
			utm_source: "",
			utm_medium: "",
			utm_campaign: "",
		};

		// Act
		render(<SessionVisitsTable visits={[empty]} />);
		const row = screen.getByText("3").closest("tr");
		if (!row) throw new Error("fila de la visita vacia no encontrada");

		// Assert: landing, niche, referrer, pais y UTM -> 5 celdas con "-"
		const dashes = within(row).getAllByText("-");
		expect(dashes).toHaveLength(5);
	});
});
