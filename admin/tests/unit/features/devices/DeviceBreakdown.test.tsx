import { render } from "@tests/utils/render";
import { describe, expect, it } from "vitest";
import { DeviceBreakdown } from "@/features/devices/components/DeviceBreakdown";
import type { BreakdownResponse } from "@/features/devices/types";

/**
 * @module tests/unit/features/devices/DeviceBreakdown
 * @description Las 3 Cards (tipos de dispositivo, navegadores, sistemas
 *   operativos) con su DistributionChart. Cubre el estado loading (3 skeletons +
 *   titulos) y el estado con data (3 ResponsiveContainer de Recharts).
 */

const DATA: BreakdownResponse = {
	device_types: [{ device_type: "desktop", sessions: 50 }],
	browsers: [{ browser: "Chrome", sessions: 40 }],
	os: [{ os: "Linux", sessions: 35 }],
};

describe("DeviceBreakdown", () => {
	it("Given cualquier estado When se renderiza Then muestra los 3 titulos de Card", () => {
		// Arrange + Act
		const { getByText } = render(
			<DeviceBreakdown data={DATA} isLoading={false} />,
		);

		// Assert
		expect(getByText("Tipos de dispositivo")).toBeInTheDocument();
		expect(getByText("Navegadores")).toBeInTheDocument();
		expect(getByText("Sistemas operativos")).toBeInTheDocument();
	});

	it("Given isLoading true When se renderiza Then muestra 3 skeletons (uno por chart)", () => {
		// Arrange + Act
		const { container } = render(
			<DeviceBreakdown data={undefined} isLoading={true} />,
		);

		// Assert: cada DistributionChart en loading renderiza un Skeleton .h-64
		expect(container.querySelectorAll(".h-64")).toHaveLength(3);
	});

	it("Given data When se renderiza Then monta los 3 ResponsiveContainer de Recharts", () => {
		// Arrange + Act
		const { container } = render(
			<DeviceBreakdown data={DATA} isLoading={false} />,
		);

		// Assert: un wrapper de Recharts por cada una de las 3 distribuciones
		expect(
			container.querySelectorAll(".recharts-responsive-container"),
		).toHaveLength(3);
	});
});
