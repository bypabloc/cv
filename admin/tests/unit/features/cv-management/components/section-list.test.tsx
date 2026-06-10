import { render, screen, userEvent, within } from "@tests/utils/render";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { SectionList } from "@/features/cv-management/components/section-list";
import type { SectionListItem } from "@/features/cv-management/lib/sections";

/**
 * @module tests/unit/features/cv-management/components/section-list
 * @description Verifica la lista de cards: skeletons, empty state, badges de
 *   niches, alta/editar/eliminar y el reorden (cv-entity-move-up/down emite
 *   la lista COMPLETA de slugs; deshabilitado sin niche activo).
 *
 *   El shadcn Select (Radix) usa portal + pointer events poco fiables en
 *   happy-dom: se mockea para exponer value/onValueChange determinista
 *   (mismo patron que SessionFilters).
 */

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

const ITEMS: SectionListItem[] = [
	{
		slug: "exp-a",
		title: "Arquitecto",
		subtitle: "Acme · 2021-03 — 2024-01",
		niches: ["generic", "vibe"],
	},
	{ slug: "exp-b", title: "Lead", subtitle: "Beta", niches: ["generic"] },
	{ slug: "exp-c", title: "Dev", subtitle: "Gamma", niches: ["generic"] },
];

function defaultProps() {
	return {
		items: ITEMS,
		isLoading: false,
		niches: ["generic", "vibe"],
		activeNiche: "generic",
		onNicheChange: vi.fn(),
		onNew: vi.fn(),
		onEdit: vi.fn(),
		onDelete: vi.fn(),
		onReorder: vi.fn(),
	};
}

describe("SectionList", () => {
	it("Given isLoading When se renderiza Then muestra skeletons y ninguna card", () => {
		// Arrange + Act
		render(<SectionList {...defaultProps()} isLoading items={[]} />);

		// Assert
		expect(screen.getByTestId("cv-section-skeleton")).toBeInTheDocument();
		expect(screen.queryByTestId("cv-entity-card")).not.toBeInTheDocument();
	});

	it("Given cero items When se renderiza Then muestra el empty state", () => {
		// Arrange + Act
		render(<SectionList {...defaultProps()} items={[]} />);

		// Assert
		expect(screen.getByText("Sin entradas")).toBeInTheDocument();
	});

	it("Given items When se renderiza Then una card por item con titulo y badges", () => {
		// Arrange + Act
		render(<SectionList {...defaultProps()} />);

		// Assert
		const cards = screen.getAllByTestId("cv-entity-card");
		expect(cards).toHaveLength(3);
		expect(cards[0]).toHaveAttribute("data-slug", "exp-a");
		expect(screen.getByText("Arquitecto")).toBeInTheDocument();
		// El badge vive dentro de la primera card (el select mockeado tambien
		// imprime "vibe" como item, por eso se acota con within).
		expect(
			within(cards[0] as HTMLElement).getByText("vibe"),
		).toBeInTheDocument();
	});

	it("Given cv-entity-new When se clickea Then dispara onNew", async () => {
		// Arrange
		const user = userEvent.setup();
		const props = defaultProps();
		render(<SectionList {...props} />);

		// Act
		await user.click(screen.getByTestId("cv-entity-new"));

		// Assert
		expect(props.onNew).toHaveBeenCalledTimes(1);
	});

	it("Given editar/eliminar de una card When se clickean Then emiten el slug", async () => {
		// Arrange
		const user = userEvent.setup();
		const props = defaultProps();
		render(<SectionList {...props} />);

		// Act
		await user.click(screen.getAllByTestId("cv-entity-edit")[1] as HTMLElement);
		await user.click(
			screen.getAllByTestId("cv-entity-delete")[2] as HTMLElement,
		);

		// Assert
		expect(props.onEdit).toHaveBeenCalledWith("exp-b");
		expect(props.onDelete).toHaveBeenCalledWith("exp-c");
	});

	it("Given move-up del item 2 When se clickea Then emite la lista completa con el swap", async () => {
		// Arrange
		const user = userEvent.setup();
		const props = defaultProps();
		render(<SectionList {...props} />);

		// Act
		await user.click(
			screen.getAllByTestId("cv-entity-move-up")[2] as HTMLElement,
		);

		// Assert
		expect(props.onReorder).toHaveBeenCalledWith(["exp-a", "exp-c", "exp-b"]);
	});

	it("Given move-down del item 0 When se clickea Then emite el swap hacia abajo", async () => {
		// Arrange
		const user = userEvent.setup();
		const props = defaultProps();
		render(<SectionList {...props} />);

		// Act
		await user.click(
			screen.getAllByTestId("cv-entity-move-down")[0] as HTMLElement,
		);

		// Assert
		expect(props.onReorder).toHaveBeenCalledWith(["exp-b", "exp-a", "exp-c"]);
	});

	it("Given los extremos When se inspeccionan Then up[0] y down[ultimo] deshabilitados", () => {
		// Arrange + Act
		render(<SectionList {...defaultProps()} />);

		// Assert
		expect(screen.getAllByTestId("cv-entity-move-up")[0]).toBeDisabled();
		expect(screen.getAllByTestId("cv-entity-move-down")[2]).toBeDisabled();
	});

	it("Given sin niche activo When se renderiza Then NO hay botones de reorden y el select recibe _all", () => {
		// Arrange + Act
		render(<SectionList {...defaultProps()} activeNiche="" />);

		// Assert
		expect(screen.queryByTestId("cv-entity-move-up")).not.toBeInTheDocument();
		expect(capturedValues).toEqual(["_all"]);
	});

	it("Given el selector de niche When emite un niche Then onNicheChange lo recibe ('' para _all)", () => {
		// Arrange
		const props = defaultProps();
		render(<SectionList {...props} />);

		// Act: el Select mockeado expone el onValueChange capturado.
		capturedOnValueChange[0]?.("vibe");
		capturedOnValueChange[0]?.("_all");

		// Assert
		expect(props.onNicheChange).toHaveBeenNthCalledWith(1, "vibe");
		expect(props.onNicheChange).toHaveBeenNthCalledWith(2, "");
	});
});
