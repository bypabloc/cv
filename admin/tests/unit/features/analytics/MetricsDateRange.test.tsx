import { render, screen } from "@tests/utils/render";
import type { DateRange } from "react-day-picker";
import { describe, expect, it, vi } from "vitest";
import { MetricsDateRange } from "@/features/analytics/components/MetricsDateRange";

/**
 * @module tests/unit/features/analytics/MetricsDateRange
 * @description MetricsDateRange: adapta entre los strings YYYY-MM-DD (params del
 *   backend) y los Date del DateRangePicker. Se mockea el DateRangePicker para
 *   exponer su `value` (que MetricsDateRange computa) y disparar su `onChange`
 *   de forma determinista, sin depender del calendario real.
 */

/** Captura del ultimo `value` recibido + dispara el onChange controlado. */
let lastValue: DateRange | undefined;
let lastOnChange: ((range: DateRange | undefined) => void) | undefined;

vi.mock("@/components/ui/date-range-picker", () => ({
	DateRangePicker: ({
		value,
		onChange,
	}: {
		value: DateRange | undefined;
		onChange: (range: DateRange | undefined) => void;
	}) => {
		lastValue = value;
		lastOnChange = onChange;
		return (
			<div data-testid="picker">
				{value?.from
					? `from:${value.from.toISOString().slice(0, 10)}`
					: "no-value"}
			</div>
		);
	},
}));

describe("MetricsDateRange", () => {
	it("Given un rango con from/to When se renderiza Then pasa Dates parseados al picker", () => {
		// Arrange + Act
		render(
			<MetricsDateRange
				range={{ from: "2026-04-27", to: "2026-05-28" }}
				onChange={() => {}}
			/>,
		);

		// Assert: el value derivado expone el from convertido a Date
		expect(screen.getByTestId("picker")).toHaveTextContent("from:2026-04-27");
		expect(lastValue?.from).toBeInstanceOf(Date);
		expect(lastValue?.to).toBeInstanceOf(Date);
	});

	it("Given un rango sin from When se renderiza Then el value del picker es undefined", () => {
		// Arrange + Act
		render(<MetricsDateRange range={{}} onChange={() => {}} />);

		// Assert
		expect(screen.getByTestId("picker")).toHaveTextContent("no-value");
		expect(lastValue).toBeUndefined();
	});

	it("Given el picker emite un rango completo When onChange Then propaga los strings ISO", () => {
		// Arrange
		const onChange = vi.fn();
		render(<MetricsDateRange range={{}} onChange={onChange} />);

		// Act: simula que el calendario eligio un rango from+to
		lastOnChange?.({
			from: new Date("2026-01-01T00:00:00Z"),
			to: new Date("2026-01-31T00:00:00Z"),
		});

		// Assert
		expect(onChange).toHaveBeenCalledWith({
			from: "2026-01-01",
			to: "2026-01-31",
		});
	});

	it("Given el picker emite un rango incompleto (solo from) When onChange Then NO propaga", () => {
		// Arrange
		const onChange = vi.fn();
		render(<MetricsDateRange range={{}} onChange={onChange} />);

		// Act: solo from, sin to -> el guard no propaga
		lastOnChange?.({ from: new Date("2026-01-01T00:00:00Z"), to: undefined });

		// Assert
		expect(onChange).not.toHaveBeenCalled();
	});

	it("Given el picker emite un rango incompleto (solo to) When onChange Then NO propaga", () => {
		// Arrange
		const onChange = vi.fn();
		render(<MetricsDateRange range={{}} onChange={onChange} />);

		// Act: solo to, sin from -> el guard `next?.from && next?.to` no propaga
		lastOnChange?.({
			from: undefined as unknown as Date,
			to: new Date("2026-01-31T00:00:00Z"),
		});

		// Assert
		expect(onChange).not.toHaveBeenCalled();
	});

	it("Given el picker emite undefined When onChange Then NO propaga", () => {
		// Arrange
		const onChange = vi.fn();
		render(<MetricsDateRange range={{}} onChange={onChange} />);

		// Act: el calendario se limpia -> next undefined
		lastOnChange?.(undefined);

		// Assert
		expect(onChange).not.toHaveBeenCalled();
	});

	it("Given un range con from invalido When se renderiza Then toDate retorna undefined (NaN guard)", () => {
		// Arrange + Act: 'no-es-fecha' produce un Date NaN -> toDate -> undefined.
		// `range.from` truthy entra a la rama del value, pero el from parseado es
		// undefined (cubre el branch Number.isNaN de toDate, lineas 18-20).
		render(
			<MetricsDateRange
				range={{ from: "no-es-fecha", to: "tampoco" }}
				onChange={() => {}}
			/>,
		);

		// Assert: value existe (from era truthy) pero ambos Dates son undefined
		expect(screen.getByTestId("picker")).toHaveTextContent("no-value");
		expect(lastValue).toEqual({ from: undefined, to: undefined });
	});
});
