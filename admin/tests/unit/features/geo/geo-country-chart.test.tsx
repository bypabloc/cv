import { render } from "@tests/utils/render";
import { describe, expect, it } from "vitest";
import { GeoCountryChart } from "@/features/geo/components/GeoCountryChart";
import type {
	GeoByCountryResponse,
	GeoCountryItem,
} from "@/features/geo/types";

/**
 * @module tests/unit/features/geo/geo-country-chart
 * @description GeoCountryChart: cubre los 3 branches (loading -> skeleton,
 *   vacio -> mensaje, con data -> BarChart). Recharts no pinta el SVG con
 *   dimensiones 0 en happy-dom: se verifica que no crashea y el codigo de
 *   transformacion (sort + slice top 10) se ejecuta.
 */

const RESPONSE: GeoByCountryResponse = {
	items: [
		{ country: "AR", sessions: 30, visits: 40, events: 100 },
		{ country: "CL", sessions: 90, visits: 120, events: 300 },
	],
	total: 120,
};

describe("GeoCountryChart", () => {
	it("Given isLoading=true When se renderiza Then muestra el skeleton", () => {
		// Arrange + Act
		const { container } = render(<GeoCountryChart isLoading={true} />);

		// Assert: skeleton es un div con data-slot="skeleton"
		expect(container.querySelector('[data-slot="skeleton"]')).not.toBeNull();
	});

	it("Given data undefined When isLoading=false Then tambien muestra el skeleton", () => {
		// Arrange + Act
		const { container } = render(<GeoCountryChart isLoading={false} />);

		// Assert
		expect(container.querySelector('[data-slot="skeleton"]')).not.toBeNull();
	});

	it("Given items vacio When se renderiza Then muestra el mensaje vacio", () => {
		// Arrange + Act
		const { getByText } = render(
			<GeoCountryChart data={{ items: [], total: 0 }} isLoading={false} />,
		);

		// Assert
		expect(
			getByText("Sin datos en el rango seleccionado."),
		).toBeInTheDocument();
	});

	it("Given data con paises When se renderiza Then no crashea y monta el contenedor del chart", () => {
		// Arrange + Act
		const { container } = render(
			<GeoCountryChart data={RESPONSE} isLoading={false} />,
		);

		// Assert: ResponsiveContainer renderiza su wrapper; no muestra mensaje vacio
		expect(
			container.querySelector(".recharts-responsive-container"),
		).not.toBeNull();
	});

	it("Given mas de 10 paises When se renderiza Then ejecuta el slice top 10 sin crashear", () => {
		// Arrange: 12 paises -> el codigo corta a 10
		const many: GeoCountryItem[] = Array.from({ length: 12 }, (_, i) => ({
			country: `C${i}`,
			sessions: i + 1,
			visits: i + 2,
			events: i + 3,
		}));

		// Act + Assert: el render no lanza con la rama de transformacion
		expect(() =>
			render(
				<GeoCountryChart data={{ items: many, total: 78 }} isLoading={false} />,
			),
		).not.toThrow();
	});
});
