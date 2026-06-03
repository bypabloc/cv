import { render, screen } from "@tests/utils/render";
import { describe, expect, it } from "vitest";
import { ContactByStatusChart } from "@/features/contacts/components/ContactByStatusChart";
import type { ContactByStatusResponse } from "@/features/contacts/types";

/**
 * @module tests/unit/features/contacts/ContactByStatusChart
 * @description ContactByStatusChart: PieChart de Recharts del desglose por
 *   estado. Cubre los 3 branches: loading (Skeleton), vacio (mensaje) y con
 *   data. Recharts NO renderiza el SVG con dimensiones 0 en happy-dom, asi
 *   que el branch con data solo verifica que el codigo de transformacion
 *   (map de Cells) corre sin crashear.
 */

const DATA: ContactByStatusResponse = {
	items: [
		{ status: "new", count: 8, pct: 0.8 },
		{ status: "converted", count: 2, pct: 0.2 },
	],
};

describe("ContactByStatusChart", () => {
	it("Given isLoading true When se renderiza Then muestra el skeleton (no el mensaje vacio)", () => {
		// Arrange + Act
		const { container } = render(
			<ContactByStatusChart data={DATA} isLoading={true} />,
		);

		// Assert: el skeleton (.h-64) se monta y no muestra el mensaje de vacio
		expect(container.querySelector(".h-64")).not.toBeNull();
		expect(
			screen.queryByText("Sin contactos en el rango seleccionado."),
		).not.toBeInTheDocument();
	});

	it("Given data undefined When isLoading false Then cae al skeleton (no el mensaje vacio)", () => {
		// Arrange + Act
		const { container } = render(
			<ContactByStatusChart data={undefined} isLoading={false} />,
		);

		// Assert
		expect(container.querySelector(".h-64")).not.toBeNull();
		expect(
			screen.queryByText("Sin contactos en el rango seleccionado."),
		).not.toBeInTheDocument();
	});

	it("Given items vacios When isLoading false Then muestra el mensaje vacio", () => {
		// Arrange + Act
		render(<ContactByStatusChart data={{ items: [] }} isLoading={false} />);

		// Assert
		expect(
			screen.getByText("Sin contactos en el rango seleccionado."),
		).toBeInTheDocument();
	});

	it("Given data con items When se renderiza Then no crashea y no muestra el mensaje vacio", () => {
		// Arrange + Act
		const { container } = render(
			<ContactByStatusChart data={DATA} isLoading={false} />,
		);

		// Assert: corrio el map de Cells (sin crash); no es el branch vacio
		expect(
			screen.queryByText("Sin contactos en el rango seleccionado."),
		).not.toBeInTheDocument();
		expect(container.querySelector(".recharts-responsive-container")).not.toBe(
			null,
		);
	});
});
