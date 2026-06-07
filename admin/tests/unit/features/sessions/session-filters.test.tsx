import { render, screen } from "@tests/utils/render";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { SessionFilters } from "@/features/sessions/components/SessionFilters";

/**
 * @module tests/unit/features/sessions/session-filters
 * @description SessionFilters: dos Selects (device_type, browser). El valor
 *   centinela `_all` representa "sin filtro": al renderizar, un value undefined
 *   cae a `_all`; al emitirse, `_all` -> undefined y un valor concreto se
 *   propaga tal cual.
 *
 *   El shadcn Select (Radix) usa portal + pointer events poco fiables en
 *   happy-dom, asi que se mockea cada Select para exponer su `value` y disparar
 *   su `onValueChange` de forma determinista (mismo patron que
 *   ContactStatusFilter / MetricsDateRange). Se capturan AMBOS Selects en orden:
 *   [0] = device_type, [1] = browser.
 */

/** Captura del value + onValueChange de cada Select, en orden de render. */
let capturedValues: string[] = [];
let capturedOnValueChange: ((next: string) => void)[] = [];

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
		capturedValues.push(value);
		capturedOnValueChange.push(onValueChange);
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
	capturedValues = [];
	capturedOnValueChange = [];
});

describe("SessionFilters", () => {
	it("Given deviceType y browser undefined When se renderiza Then ambos Selects reciben el centinela `_all`", () => {
		// Arrange + Act
		render(
			<SessionFilters
				deviceType={undefined}
				browser={undefined}
				onDeviceTypeChange={vi.fn()}
				onBrowserChange={vi.fn()}
			/>,
		);

		// Assert: [0] = device_type, [1] = browser
		expect(capturedValues).toEqual(["_all", "_all"]);
	});

	it("Given deviceType y browser concretos When se renderiza Then cada Select recibe su value", () => {
		// Arrange + Act
		render(
			<SessionFilters
				deviceType="mobile"
				browser="Firefox"
				onDeviceTypeChange={vi.fn()}
				onBrowserChange={vi.fn()}
			/>,
		);

		// Assert
		expect(capturedValues).toEqual(["mobile", "Firefox"]);
	});

	it("Given el Select de dispositivo emite un valor concreto When onValueChange Then onDeviceTypeChange recibe ese valor", () => {
		// Arrange
		const onDeviceTypeChange = vi.fn();
		render(
			<SessionFilters
				deviceType={undefined}
				browser={undefined}
				onDeviceTypeChange={onDeviceTypeChange}
				onBrowserChange={vi.fn()}
			/>,
		);

		// Act: el primer Select es device_type
		capturedOnValueChange[0]?.("tablet");

		// Assert
		expect(onDeviceTypeChange).toHaveBeenCalledWith("tablet");
	});

	it("Given el Select de dispositivo emite el centinela `_all` When onValueChange Then onDeviceTypeChange recibe undefined", () => {
		// Arrange
		const onDeviceTypeChange = vi.fn();
		render(
			<SessionFilters
				deviceType="desktop"
				browser={undefined}
				onDeviceTypeChange={onDeviceTypeChange}
				onBrowserChange={vi.fn()}
			/>,
		);

		// Act
		capturedOnValueChange[0]?.("_all");

		// Assert
		expect(onDeviceTypeChange).toHaveBeenCalledWith(undefined);
	});

	it("Given el Select de navegador emite un valor concreto When onValueChange Then onBrowserChange recibe ese valor", () => {
		// Arrange
		const onBrowserChange = vi.fn();
		render(
			<SessionFilters
				deviceType={undefined}
				browser={undefined}
				onDeviceTypeChange={vi.fn()}
				onBrowserChange={onBrowserChange}
			/>,
		);

		// Act: el segundo Select es browser
		capturedOnValueChange[1]?.("Safari");

		// Assert
		expect(onBrowserChange).toHaveBeenCalledWith("Safari");
	});

	it("Given el Select de navegador emite el centinela `_all` When onValueChange Then onBrowserChange recibe undefined", () => {
		// Arrange
		const onBrowserChange = vi.fn();
		render(
			<SessionFilters
				deviceType={undefined}
				browser="Chrome"
				onDeviceTypeChange={vi.fn()}
				onBrowserChange={onBrowserChange}
			/>,
		);

		// Act
		capturedOnValueChange[1]?.("_all");

		// Assert
		expect(onBrowserChange).toHaveBeenCalledWith(undefined);
	});

	it("Given se renderiza When se listan las opciones Then incluye los 4 dispositivos, los 5 navegadores y los placeholders/centinelas", () => {
		// Arrange + Act
		render(
			<SessionFilters
				deviceType={undefined}
				browser={undefined}
				onDeviceTypeChange={vi.fn()}
				onBrowserChange={vi.fn()}
			/>,
		);

		// Assert: placeholders (SelectValue)
		expect(screen.getByText("Dispositivo")).toBeInTheDocument();
		expect(screen.getByText("Navegador")).toBeInTheDocument();
		// centinelas (SelectItem ALL)
		expect(screen.getByText("Todos los dispositivos")).toBeInTheDocument();
		expect(screen.getByText("Todos los navegadores")).toBeInTheDocument();
		// 4 device types
		expect(screen.getByText("desktop")).toBeInTheDocument();
		expect(screen.getByText("mobile")).toBeInTheDocument();
		expect(screen.getByText("tablet")).toBeInTheDocument();
		expect(screen.getByText("bot")).toBeInTheDocument();
		// 5 browsers
		expect(screen.getByText("Chrome")).toBeInTheDocument();
		expect(screen.getByText("Firefox")).toBeInTheDocument();
		expect(screen.getByText("Safari")).toBeInTheDocument();
		expect(screen.getByText("Edge")).toBeInTheDocument();
		expect(screen.getByText("Opera")).toBeInTheDocument();
	});
});
