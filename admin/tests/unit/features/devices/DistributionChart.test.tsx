import { render } from "@tests/utils/render";
import { describe, expect, it } from "vitest";
import { DistributionChart } from "@/features/devices/components/DistributionChart";
import type { DeviceTypeDist } from "@/features/devices/types";

/**
 * @module tests/unit/features/devices/DistributionChart
 * @description BarChart generico de una distribucion de sesiones. Cubre los 3
 *   branches: loading (skeleton), undefined/vacio (mensaje) y con data (no
 *   crashea + ejecuta la transformacion/sort). En happy-dom el SVG no renderiza
 *   con dimensiones reales -> no se asserta sobre el SVG, solo el contenedor /
 *   branches.
 */

const DATA: DeviceTypeDist[] = [
	{ device_type: "mobile", sessions: 20 },
	{ device_type: "desktop", sessions: 50 },
];

describe("DistributionChart", () => {
	it("Given isLoading true When se renderiza Then muestra el skeleton (sin mensaje vacio)", () => {
		// Arrange + Act
		const { container, queryByText } = render(
			<DistributionChart<DeviceTypeDist>
				isLoading={true}
				nameKey="device_type"
			/>,
		);

		// Assert: el skeleton es un div con la clase de tamano; no hay mensaje vacio
		expect(container.querySelector(".h-64")).not.toBeNull();
		expect(queryByText("Sin datos en el rango seleccionado.")).toBeNull();
	});

	it("Given data undefined y isLoading false When se renderiza Then sigue mostrando skeleton", () => {
		// Arrange + Act
		const { container } = render(
			<DistributionChart<DeviceTypeDist>
				isLoading={false}
				nameKey="device_type"
				data={undefined}
			/>,
		);

		// Assert
		expect(container.querySelector(".h-64")).not.toBeNull();
	});

	it("Given data vacia When se renderiza Then muestra el mensaje de vacio", () => {
		// Arrange + Act
		const { getByText } = render(
			<DistributionChart<DeviceTypeDist>
				isLoading={false}
				nameKey="device_type"
				data={[]}
			/>,
		);

		// Assert
		expect(
			getByText("Sin datos en el rango seleccionado."),
		).toBeInTheDocument();
	});

	it("Given filas con data When se renderiza Then monta el ResponsiveContainer sin crashear", () => {
		// Arrange + Act
		const { container } = render(
			<DistributionChart<DeviceTypeDist>
				isLoading={false}
				nameKey="device_type"
				data={DATA}
			/>,
		);

		// Assert: el wrapper de Recharts existe; no se assertan paths del SVG
		expect(
			container.querySelector(".recharts-responsive-container"),
		).not.toBeNull();
	});

	it("Given una fila sin valor en nameKey When se renderiza Then cae al fallback sin crashear", () => {
		// Arrange: el valor de nameKey es undefined -> el .map usa '-' como label
		const rows = [
			{ device_type: undefined, sessions: 5 },
		] as unknown as DeviceTypeDist[];

		// Act
		const { container } = render(
			<DistributionChart<DeviceTypeDist>
				isLoading={false}
				nameKey="device_type"
				data={rows}
			/>,
		);

		// Assert
		expect(
			container.querySelector(".recharts-responsive-container"),
		).not.toBeNull();
	});
});
