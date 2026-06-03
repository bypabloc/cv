import { render, screen, within } from "@tests/utils/render";
import { describe, expect, it } from "vitest";
import { GeoCountryTable } from "@/features/geo/components/GeoCountryTable";
import type { GeoCountryItem } from "@/features/geo/types";

/**
 * @module tests/unit/features/geo/geo-country-table
 * @description Render del ranking de paises: filas con country + sessions +
 *   visits + events formateados, reordenadas por sessions desc, y mensaje
 *   vacio cuando items=[].
 */

const ITEMS: GeoCountryItem[] = [
	{ country: "AR", sessions: 30, visits: 40, events: 100 },
	{ country: "CL", sessions: 1500, visits: 1800, events: 5000 },
];

describe("GeoCountryTable", () => {
	it("Given 2 paises When se renderiza Then muestra ambos codigos ISO-2", () => {
		// Arrange + Act
		render(<GeoCountryTable items={ITEMS} />);

		// Assert
		expect(screen.getByText("AR")).toBeInTheDocument();
		expect(screen.getByText("CL")).toBeInTheDocument();
	});

	it("Given filas desordenadas When se renderiza Then la de mas sessions queda primera", () => {
		// Arrange + Act
		render(<GeoCountryTable items={ITEMS} />);
		const dataRows = screen
			.getAllByRole("row")
			.filter((row) => within(row).queryByText(/AR|CL/));

		// Assert: CL (1500) antes que AR (30)
		expect(
			within(dataRows[0] as HTMLElement).getByText("CL"),
		).toBeInTheDocument();
		expect(
			within(dataRows[1] as HTMLElement).getByText("AR"),
		).toBeInTheDocument();
	});

	it("Given valores numericos When se renderiza Then formatea los miles con Intl es", () => {
		// Arrange + Act
		render(<GeoCountryTable items={ITEMS} />);

		// Assert: el componente usa Intl.NumberFormat('es'); se calcula el
		// valor esperado con el mismo formateador (agnostico al ICU del runtime).
		const fmt = new Intl.NumberFormat("es");
		expect(screen.getByText(fmt.format(1500))).toBeInTheDocument();
		expect(screen.getByText(fmt.format(5000))).toBeInTheDocument();
	});

	it("Given una fila When se renderiza Then muestra sessions, visits y events de ese pais", () => {
		// Arrange + Act
		render(<GeoCountryTable items={[ITEMS[0] as GeoCountryItem]} />);
		const row = screen.getByText("AR").closest("tr");
		if (!row) throw new Error("fila AR no encontrada");

		// Assert
		expect(within(row).getByText("30")).toBeInTheDocument();
		expect(within(row).getByText("40")).toBeInTheDocument();
		expect(within(row).getByText("100")).toBeInTheDocument();
	});

	it("Given items vacio When se renderiza Then muestra el mensaje vacio", () => {
		// Arrange + Act
		render(<GeoCountryTable items={[]} />);

		// Assert
		expect(
			screen.getByText("Sin paises en el rango seleccionado."),
		).toBeInTheDocument();
	});

	it("Given los encabezados When se renderiza Then muestra las 4 columnas", () => {
		// Arrange + Act
		render(<GeoCountryTable items={ITEMS} />);

		// Assert
		expect(screen.getByText("Pais")).toBeInTheDocument();
		expect(screen.getByText("Sesiones")).toBeInTheDocument();
		expect(screen.getByText("Visitas")).toBeInTheDocument();
		expect(screen.getByText("Eventos")).toBeInTheDocument();
	});
});
