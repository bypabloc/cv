import { render, screen } from "@tests/utils/render";
import { describe, expect, it } from "vitest";
import { TopPagesTable } from "@/features/analytics/components/TopPagesTable";
import type { TopPageItem } from "@/features/analytics/types";

/**
 * @module tests/unit/features/analytics/TopPagesTable
 * @description TopPagesTable: tabla de ranking de paginas. Mensaje vacio si no
 *   hay items; una fila por pagina con sus 3 metricas.
 */

const ITEMS: TopPageItem[] = [
	{ page_path: "/", events: 50, unique_visitors: 30, unique_visits: 40 },
	{
		page_path: "/projects",
		events: 25,
		unique_visitors: 18,
		unique_visits: 20,
	},
];

describe("TopPagesTable", () => {
	it("Given items When se renderiza Then muestra una fila por pagina con sus metricas", () => {
		// Arrange + Act
		render(<TopPagesTable items={ITEMS} />);

		// Assert
		expect(screen.getByText("/")).toBeInTheDocument();
		expect(screen.getByText("/projects")).toBeInTheDocument();
		expect(screen.getByText("50")).toBeInTheDocument();
		expect(screen.getByText("18")).toBeInTheDocument();
	});

	it("Given items When se renderiza Then muestra los encabezados de columna", () => {
		// Arrange + Act
		render(<TopPagesTable items={ITEMS} />);

		// Assert
		expect(screen.getByText("Pagina")).toBeInTheDocument();
		expect(screen.getByText("Eventos")).toBeInTheDocument();
		expect(screen.getByText("Visitantes")).toBeInTheDocument();
		expect(screen.getByText("Visitas")).toBeInTheDocument();
	});

	it("Given items vacios When se renderiza Then muestra el mensaje vacio y ninguna tabla", () => {
		// Arrange + Act
		render(<TopPagesTable items={[]} />);

		// Assert
		expect(
			screen.getByText("Sin paginas en el rango seleccionado."),
		).toBeInTheDocument();
		expect(screen.queryByRole("table")).not.toBeInTheDocument();
	});
});
