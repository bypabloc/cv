import { render, screen, userEvent } from "@tests/utils/render";
import type { ReactElement } from "react";
import { describe, expect, it, vi } from "vitest";
import { MetricsRangePicker } from "@/features/analytics/components/MetricsRangePicker";
import { resolveRelative } from "@/features/analytics/lib/range-presets";

/**
 * @module tests/unit/features/analytics/MetricsRangePicker
 * @description Verifica el selector de rango estilo CloudWatch: chips rapidos,
 *   pestanas Relative/Absolute y que aplicar un preset llama onChange con un
 *   rango datetime + bucket derivado.
 */

const baseRange = resolveRelative(30, "days", new Date("2026-06-03T00:00:00Z"));

describe("MetricsRangePicker", () => {
	it("Given el picker When se abre Then muestra los chips 5m/30m/1h/3h/12h + Custom", async () => {
		// Arrange
		const user = userEvent.setup();
		render(
			(
				<MetricsRangePicker range={baseRange} onChange={vi.fn()} />
			) as ReactElement,
		);

		// Act
		await user.click(screen.getByRole("button"));

		// Assert: los chips de la imagen
		for (const label of ["5m", "30m", "1h", "3h", "12h", "Custom"]) {
			expect(
				screen.getByRole("button", { name: new RegExp(`^${label}$`) }),
			).toBeInTheDocument();
		}
	});

	it("Given el picker abierto When click en un chip Then onChange recibe un rango datetime + bucket", async () => {
		// Arrange
		const onChange = vi.fn();
		const user = userEvent.setup();
		render(
			(
				<MetricsRangePicker range={baseRange} onChange={onChange} />
			) as ReactElement,
		);

		// Act: abrir y elegir "1h"
		await user.click(screen.getByRole("button"));
		await user.click(screen.getByRole("button", { name: /^1h$/ }));

		// Assert: onChange con from/to datetime (con hora, "T") + bucket minute
		expect(onChange).toHaveBeenCalledTimes(1);
		const arg = onChange.mock.calls[0]?.[0] as {
			from: string;
			to: string;
			bucket: string;
		};
		expect(arg.from).toContain("T");
		expect(arg.to).toContain("T");
		expect(arg.bucket).toBe("minute");
	});

	it("Given el grid Relative When click en un preset Then onChange con el rango", async () => {
		// Arrange
		const onChange = vi.fn();
		const user = userEvent.setup();
		render(
			(
				<MetricsRangePicker range={baseRange} onChange={onChange} />
			) as ReactElement,
		);

		// Act: abrir y elegir el preset "45" (minutes) del grid
		await user.click(screen.getByRole("button"));
		await user.click(screen.getByRole("button", { name: /^45$/ }));

		// Assert: 45 min -> bucket minute
		expect(onChange).toHaveBeenCalledTimes(1);
		const arg = onChange.mock.calls[0]?.[0] as { bucket: string };
		expect(arg.bucket).toBe("minute");
	});

	it("Given Duration + Apply When se aplica Then onChange con el custom relativo", async () => {
		// Arrange
		const onChange = vi.fn();
		const user = userEvent.setup();
		render(
			(
				<MetricsRangePicker range={baseRange} onChange={onChange} />
			) as ReactElement,
		);

		// Act: abrir, escribir duration y Apply
		await user.click(screen.getByRole("button"));
		const duration = screen.getByLabelText("Duration");
		await user.clear(duration);
		await user.type(duration, "5");
		await user.click(screen.getByRole("button", { name: /^apply$/i }));

		// Assert
		expect(onChange).toHaveBeenCalledTimes(1);
		const arg = onChange.mock.calls[0]?.[0] as { from: string; to: string };
		expect(arg.from).toContain("T");
		expect(arg.to).toContain("T");
	});

	it("Given el picker abierto When abre la pestana Absolute Then muestra Start/End date y aplica", async () => {
		// Arrange
		const onChange = vi.fn();
		const user = userEvent.setup();
		render(
			(
				<MetricsRangePicker range={baseRange} onChange={onChange} />
			) as ReactElement,
		);

		// Act
		await user.click(screen.getByRole("button"));
		await user.click(screen.getByRole("tab", { name: /absolute/i }));

		// Assert: los inputs de fecha/hora estan
		expect(screen.getByText("Start date")).toBeInTheDocument();
		expect(screen.getByText("End date")).toBeInTheDocument();

		// Act: editar las fechas y aplicar
		const startDate = screen.getByLabelText("Start date");
		const endDate = screen.getByLabelText("End date");
		await user.clear(startDate);
		await user.type(startDate, "2026-06-01");
		await user.clear(endDate);
		await user.type(endDate, "2026-06-03");
		await user.click(screen.getByRole("button", { name: /^apply$/i }));

		// Assert
		expect(onChange).toHaveBeenCalledTimes(1);
		const arg = onChange.mock.calls[0]?.[0] as { from: string; to: string };
		expect(arg.from).toContain("2026-06-01");
		expect(arg.to).toContain("2026-06-03");
	});

	it("Given Absolute con fecha vacia When Apply Then NO llama onChange", async () => {
		// Arrange
		const onChange = vi.fn();
		const user = userEvent.setup();
		render(
			(
				<MetricsRangePicker range={baseRange} onChange={onChange} />
			) as ReactElement,
		);

		// Act: abrir Absolute, vaciar Start date y aplicar
		await user.click(screen.getByRole("button"));
		await user.click(screen.getByRole("tab", { name: /absolute/i }));
		await user.clear(screen.getByLabelText("Start date"));
		await user.click(screen.getByRole("button", { name: /^apply$/i }));

		// Assert: combineDateTime devuelve null -> no aplica
		expect(onChange).not.toHaveBeenCalled();
	});

	it("Given el chip Custom When click Then queda en la pestana Relative", async () => {
		// Arrange (cubre el onClick del chip Custom)
		const user = userEvent.setup();
		render(
			(
				<MetricsRangePicker range={baseRange} onChange={vi.fn()} />
			) as ReactElement,
		);

		// Act
		await user.click(screen.getByRole("button"));
		await user.click(screen.getByRole("button", { name: /^custom$/i }));

		// Assert: el grid Relative sigue visible (Duration es de esa pestana)
		expect(screen.getByLabelText("Duration")).toBeInTheDocument();
	});

	it("Given el Select Unit When cambio a Days Then aplica un rango en dias", async () => {
		// Arrange (cubre el onValueChange del Select)
		const onChange = vi.fn();
		const user = userEvent.setup();
		render(
			(
				<MetricsRangePicker range={baseRange} onChange={onChange} />
			) as ReactElement,
		);

		// Act: abrir, cambiar la unidad a Days via el Select y aplicar
		await user.click(screen.getByRole("button"));
		await user.click(screen.getByRole("combobox"));
		await user.click(screen.getByRole("option", { name: "Days" }));
		await user.click(screen.getByRole("button", { name: /^apply$/i }));

		// Assert
		expect(onChange).toHaveBeenCalledTimes(1);
	});

	it("Given Absolute When edito Start/End time Then aplica con esa hora", async () => {
		// Arrange (cubre los onChange de los time inputs)
		const onChange = vi.fn();
		const user = userEvent.setup();
		render(
			(
				<MetricsRangePicker range={baseRange} onChange={onChange} />
			) as ReactElement,
		);

		// Act
		await user.click(screen.getByRole("button"));
		await user.click(screen.getByRole("tab", { name: /absolute/i }));
		const startTime = screen.getByLabelText("Start time");
		const endTime = screen.getByLabelText("End time");
		await user.clear(startTime);
		await user.type(startTime, "08:00:00");
		await user.clear(endTime);
		await user.type(endTime, "20:00:00");
		await user.click(screen.getByRole("button", { name: /^apply$/i }));

		// Assert: aplico con la hora editada
		expect(onChange).toHaveBeenCalledTimes(1);
		const arg = onChange.mock.calls[0]?.[0] as { from: string };
		expect(arg.from).toContain("T08:00:00");
	});

	it("Given la pestana Absolute When Cancel Then cierra sin onChange", async () => {
		// Arrange
		const onChange = vi.fn();
		const user = userEvent.setup();
		render(
			(
				<MetricsRangePicker range={baseRange} onChange={onChange} />
			) as ReactElement,
		);

		// Act
		await user.click(screen.getByRole("button"));
		await user.click(screen.getByRole("tab", { name: /absolute/i }));
		await user.click(screen.getByRole("button", { name: /^cancel$/i }));

		// Assert
		expect(onChange).not.toHaveBeenCalled();
	});
});
