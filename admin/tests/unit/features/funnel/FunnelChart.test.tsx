import { render } from "@tests/utils/render";
import { describe, expect, it } from "vitest";
import { FunnelChart } from "@/features/funnel/components/FunnelChart";
import type { FunnelConversionResponse } from "@/features/funnel/types";

/**
 * @module tests/unit/features/funnel/FunnelChart
 * @description FunnelChart: cubre los 3 branches (loading -> skeleton,
 *   sessions=0 -> mensaje vacio, con data -> 3 barras + tasas). No usa Recharts:
 *   el render es DOM plano (divs), por lo que se asertan los labels y valores
 *   formateados directamente.
 */

const RESPONSE: FunnelConversionResponse = {
	sessions: 100,
	visits: 80,
	contacts: 5,
	session_to_visit_rate: 0.8,
	visit_to_contact_rate: 0.063,
	session_to_contact_rate: 0.05,
};

describe("FunnelChart", () => {
	it("Given isLoading=true When se renderiza Then muestra el skeleton", () => {
		// Arrange + Act
		const { container } = render(<FunnelChart isLoading={true} />);

		// Assert: el skeleton son 3 divs con data-slot="skeleton"
		expect(container.querySelectorAll('[data-slot="skeleton"]')).toHaveLength(
			3,
		);
	});

	it("Given data undefined When isLoading=false Then tambien muestra el skeleton", () => {
		// Arrange + Act
		const { container } = render(<FunnelChart isLoading={false} />);

		// Assert
		expect(container.querySelector('[data-slot="skeleton"]')).not.toBeNull();
	});

	it("Given sessions=0 When se renderiza Then muestra el mensaje de rango sin sesiones", () => {
		// Arrange + Act
		const { getByText } = render(
			<FunnelChart
				data={{
					sessions: 0,
					visits: 0,
					contacts: 0,
					session_to_visit_rate: 0,
					visit_to_contact_rate: 0,
					session_to_contact_rate: 0,
				}}
				isLoading={false}
			/>,
		);

		// Assert
		expect(
			getByText("Sin sesiones en el rango seleccionado."),
		).toBeInTheDocument();
	});

	it("Given data con sesiones When se renderiza Then muestra los 3 labels de etapa", () => {
		// Arrange + Act
		const { getByText } = render(
			<FunnelChart data={RESPONSE} isLoading={false} />,
		);

		// Assert
		expect(getByText("Sesiones")).toBeInTheDocument();
		expect(getByText("Visitas")).toBeInTheDocument();
		expect(getByText("Contactos")).toBeInTheDocument();
	});

	it("Given data con sesiones When se renderiza Then formatea los valores enteros de cada etapa", () => {
		// Arrange + Act
		const { getByText } = render(
			<FunnelChart data={RESPONSE} isLoading={false} />,
		);

		// Assert: fmtInt -> Intl.NumberFormat('es')
		expect(getByText("100")).toBeInTheDocument();
		expect(getByText("80")).toBeInTheDocument();
		expect(getByText("5")).toBeInTheDocument();
	});

	it("Given data con tasas When se renderiza Then muestra las tasas de conversion entre etapas", () => {
		// Arrange + Act
		const { getByText } = render(
			<FunnelChart data={RESPONSE} isLoading={false} />,
		);

		// Assert: fmtPct(0.8)=80.0%, fmtPct(0.063)=6.3% como tasas intermedias
		expect(getByText("80.0% de conversion")).toBeInTheDocument();
		expect(getByText("6.3% de conversion")).toBeInTheDocument();
	});

	it("Given data con conversion total When se renderiza Then muestra session_to_contact_rate formateada", () => {
		// Arrange + Act
		const { getByText } = render(
			<FunnelChart data={RESPONSE} isLoading={false} />,
		);

		// Assert: fmtPct(0.05) = 5.0% en el pie del embudo
		expect(getByText("5.0%")).toBeInTheDocument();
	});
});
