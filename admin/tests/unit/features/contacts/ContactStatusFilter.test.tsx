import { render, screen } from "@tests/utils/render";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ContactStatusFilter } from "@/features/contacts/components/ContactStatusFilter";

/**
 * @module tests/unit/features/contacts/ContactStatusFilter
 * @description ContactStatusFilter: select de estado. value undefined cae al
 *   centinela `all`; un value concreto se refleja en el Select. El onChange
 *   mapea `all` -> undefined y un estado concreto -> ese ContactStatus.
 *
 *   El shadcn Select (Radix) usa portal + pointer events poco fiables en
 *   happy-dom, asi que se mockea para exponer su `value` y disparar su
 *   `onValueChange` de forma determinista (mismo patron que MetricsDateRange).
 */

/** Captura del ultimo `value` recibido + dispara el onValueChange controlado. */
let lastValue: string | undefined;
let lastOnValueChange: ((next: string) => void) | undefined;

vi.mock("@/components/ui/select", () => ({
	Select: ({
		value,
		onValueChange,
		children,
	}: {
		value: string;
		onValueChange: (next: string) => void;
		children: ReactNode;
	}) => {
		lastValue = value;
		lastOnValueChange = onValueChange;
		return <div data-testid="select">{children}</div>;
	},
	SelectContent: ({ children }: { children: ReactNode }) => <>{children}</>,
	SelectItem: ({ value, children }: { value: string; children: ReactNode }) => (
		<div data-value={value}>{children}</div>
	),
	SelectTrigger: ({ children }: { children: ReactNode }) => <>{children}</>,
	SelectValue: ({ placeholder }: { placeholder?: string }) => (
		<span>{placeholder}</span>
	),
}));

beforeEach(() => {
	lastValue = undefined;
	lastOnValueChange = undefined;
});

describe("ContactStatusFilter", () => {
	it("Given value undefined When se renderiza Then el Select recibe el centinela `all`", () => {
		// Arrange + Act
		render(<ContactStatusFilter value={undefined} onChange={vi.fn()} />);

		// Assert
		expect(lastValue).toBe("all");
	});

	it("Given value 'converted' When se renderiza Then el Select recibe ese estado", () => {
		// Arrange + Act
		render(<ContactStatusFilter value="converted" onChange={vi.fn()} />);

		// Assert
		expect(lastValue).toBe("converted");
	});

	it("Given el Select emite un estado concreto When onValueChange Then onChange recibe ese ContactStatus", () => {
		// Arrange
		const onChange = vi.fn();
		render(<ContactStatusFilter value={undefined} onChange={onChange} />);

		// Act
		lastOnValueChange?.("qualified");

		// Assert
		expect(onChange).toHaveBeenCalledWith("qualified");
	});

	it("Given el Select emite el centinela `all` When onValueChange Then onChange recibe undefined", () => {
		// Arrange
		const onChange = vi.fn();
		render(<ContactStatusFilter value="new" onChange={onChange} />);

		// Act
		lastOnValueChange?.("all");

		// Assert
		expect(onChange).toHaveBeenCalledWith(undefined);
	});

	it("Given se renderiza When se listan las opciones Then incluye los 5 estados + Todos", () => {
		// Arrange + Act
		render(<ContactStatusFilter value={undefined} onChange={vi.fn()} />);

		// Assert: el map de STATUS_OPTIONS + el item ALL + el placeholder. "Todos
		// los estados" aparece 2 veces (SelectValue placeholder + SelectItem ALL).
		expect(screen.getAllByText("Todos los estados")).toHaveLength(2);
		expect(screen.getByText("Nuevo")).toBeInTheDocument();
		expect(screen.getByText("Contactado")).toBeInTheDocument();
		expect(screen.getByText("Calificado")).toBeInTheDocument();
		expect(screen.getByText("Convertido")).toBeInTheDocument();
		expect(screen.getByText("Rechazado")).toBeInTheDocument();
	});
});
