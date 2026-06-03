import { render, screen } from "@tests/utils/render";
import { describe, expect, it } from "vitest";
import { LandingPagesTable } from "@/features/visits/components/LandingPagesTable";
import type { LandingPageItem } from "@/features/visits/types";

/**
 * @module tests/unit/features/visits/LandingPagesTable
 * @description Render del ranking de landing pages: path + visits +
 *   unique_visitors por fila, headers y mensaje vacio.
 */

const ITEMS: LandingPageItem[] = [
	{ landing_page_path: "/", visits: 40, unique_visitors: 30 },
	{ landing_page_path: "/projects", visits: 25, unique_visitors: 18 },
];

describe("LandingPagesTable", () => {
	it("Given un array vacio When se renderiza Then muestra el mensaje vacio", () => {
		// Arrange + Act
		render(<LandingPagesTable items={[]} />);

		// Assert
		expect(
			screen.getByText("Sin landing pages en el rango seleccionado."),
		).toBeInTheDocument();
	});

	it("Given dos landing pages When se renderiza Then muestra ambos paths", () => {
		// Arrange + Act
		render(<LandingPagesTable items={ITEMS} />);

		// Assert
		expect(screen.getByText("/")).toBeInTheDocument();
		expect(screen.getByText("/projects")).toBeInTheDocument();
	});

	it("Given una landing page When se renderiza Then muestra sus visits y unique_visitors", () => {
		// Arrange + Act
		render(<LandingPagesTable items={[ITEMS[0] as LandingPageItem]} />);

		// Assert
		expect(screen.getByText("40")).toBeInTheDocument();
		expect(screen.getByText("30")).toBeInTheDocument();
	});

	it("Given data When se renderiza Then muestra los headers de la tabla", () => {
		// Arrange + Act
		render(<LandingPagesTable items={ITEMS} />);

		// Assert
		expect(screen.getByText("Landing page")).toBeInTheDocument();
		expect(screen.getByText("Visitas")).toBeInTheDocument();
		expect(screen.getByText("Visitantes")).toBeInTheDocument();
	});
});
