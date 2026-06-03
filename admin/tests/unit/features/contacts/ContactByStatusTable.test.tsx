import { render, screen } from "@tests/utils/render";
import { describe, expect, it } from "vitest";
import { ContactByStatusTable } from "@/features/contacts/components/ContactByStatusTable";
import type { ContactStatusItem } from "@/features/contacts/types";

/**
 * @module tests/unit/features/contacts/ContactByStatusTable
 * @description ContactByStatusTable: render del desglose por estado (status +
 *   count + pct formateado a 1 decimal). Cubre estado vacio y con data.
 */

const ITEMS: ContactStatusItem[] = [
	{ status: "new", count: 8, pct: 0.8 },
	{ status: "converted", count: 2, pct: 0.2 },
];

describe("ContactByStatusTable", () => {
	it("Given items vacios When se renderiza Then muestra el mensaje vacio", () => {
		// Arrange + Act
		render(<ContactByStatusTable items={[]} />);

		// Assert
		expect(
			screen.getByText("Sin contactos en el rango seleccionado."),
		).toBeInTheDocument();
	});

	it("Given items When se renderiza Then muestra una fila por estado", () => {
		// Arrange + Act
		render(<ContactByStatusTable items={ITEMS} />);

		// Assert
		expect(screen.getByText("new")).toBeInTheDocument();
		expect(screen.getByText("converted")).toBeInTheDocument();
		expect(screen.getByText("8")).toBeInTheDocument();
		expect(screen.getByText("2")).toBeInTheDocument();
	});

	it("Given un pct de 0.8 When se renderiza Then muestra 80.0%", () => {
		// Arrange + Act
		render(<ContactByStatusTable items={ITEMS} />);

		// Assert
		expect(screen.getByText("80.0%")).toBeInTheDocument();
		expect(screen.getByText("20.0%")).toBeInTheDocument();
	});

	it("Given items When se renderiza Then muestra los headers Estado/Cantidad/%", () => {
		// Arrange + Act
		render(<ContactByStatusTable items={ITEMS} />);

		// Assert
		expect(screen.getByText("Estado")).toBeInTheDocument();
		expect(screen.getByText("Cantidad")).toBeInTheDocument();
		expect(screen.getByText("%")).toBeInTheDocument();
	});
});
