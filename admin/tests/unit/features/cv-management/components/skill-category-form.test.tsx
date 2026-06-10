import { act, render, screen, userEvent, waitFor } from "@tests/utils/render";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { SkillCategoryForm } from "@/features/cv-management/components/skill-category-form";
import type {
	CvCatalogs,
	CvSkillCategory,
} from "@/features/cv-management/types";

/**
 * @module tests/unit/features/cv-management/components/skill-category-form
 * @description Verifica el form de categoria de skills: hidratacion, skills
 *   ordenadas con reorden interno (tag-chip-up) reflejado en el payload y
 *   validacion (al menos una skill). Select de kind mockeado.
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

const CATALOGS: CvCatalogs = {
	niches: ["generic"],
	skills: [
		{ slug: "python", name: "Python" },
		{ slug: "sql", name: "SQL" },
	],
	techTags: [],
};

const CATEGORY: CvSkillCategory = {
	slug: "backend",
	name: { es: "Backend", en: "Backend" },
	kind: "technical",
	skills: ["Python", "SQL"],
	niches: ["generic"],
	priority: { generic: 2 },
};

describe("SkillCategoryForm", () => {
	it("Given una categoria inicial When se renderiza Then hidrata nombre, kind y skills en orden", () => {
		// Arrange + Act
		render(
			<SkillCategoryForm
				initial={CATEGORY}
				onSubmit={vi.fn()}
				submitting={false}
				catalogs={CATALOGS}
			/>,
		);

		// Assert
		expect(screen.getByTestId("cv-field-slug")).toHaveValue("backend");
		expect(screen.getByTestId("bilang-name-es")).toHaveValue("Backend");
		expect(capturedValues[0]).toBe("technical");
		const chips = screen.getAllByTestId("tag-chip");
		expect(chips.map((chip) => chip.getAttribute("data-value"))).toEqual([
			"Python",
			"SQL",
		]);
	});

	it("Given el reorden interno de skills When se sube SQL y guarda Then el payload preserva el orden nuevo", async () => {
		// Arrange
		const user = userEvent.setup();
		const onSubmit = vi.fn();
		render(
			<SkillCategoryForm
				initial={CATEGORY}
				onSubmit={onSubmit}
				submitting={false}
				catalogs={CATALOGS}
			/>,
		);

		// Act
		await user.click(screen.getAllByTestId("tag-chip-up")[1] as HTMLElement);
		await user.click(screen.getByTestId("cv-form-submit"));

		// Assert
		await waitFor(() => {
			expect(onSubmit).toHaveBeenCalledWith({
				...CATEGORY,
				skills: ["SQL", "Python"],
			});
		});
	});

	it("Given el alta vacia When se guarda Then exige nombre/kind/skills/niches y NO emite", async () => {
		// Arrange
		const user = userEvent.setup();
		const onSubmit = vi.fn();
		render(
			<SkillCategoryForm
				onSubmit={onSubmit}
				submitting={false}
				catalogs={CATALOGS}
			/>,
		);

		// Act
		await user.click(screen.getByTestId("cv-form-submit"));

		// Assert
		await waitFor(() => {
			expect(screen.getByText("Selecciona el tipo")).toBeInTheDocument();
		});
		expect(screen.getByText("Agrega al menos una skill")).toBeInTheDocument();
		expect(
			screen.getByText("Selecciona al menos un niche"),
		).toBeInTheDocument();
		expect(onSubmit).not.toHaveBeenCalled();
	});

	it("Given submitting When se renderiza Then el boton dice Guardando y esta deshabilitado", () => {
		// Arrange + Act
		render(
			<SkillCategoryForm
				initial={CATEGORY}
				onSubmit={vi.fn()}
				submitting
				catalogs={CATALOGS}
			/>,
		);

		// Assert
		const submit = screen.getByTestId("cv-form-submit");
		expect(submit).toBeDisabled();
		expect(submit).toHaveTextContent("Guardando...");
	});

	it("Given el picker de niches When se desmarca generic Then el payload pierde el niche", async () => {
		// Arrange
		const user = userEvent.setup();
		const onSubmit = vi.fn();
		render(
			<SkillCategoryForm
				initial={CATEGORY}
				onSubmit={onSubmit}
				submitting={false}
				catalogs={CATALOGS}
			/>,
		);

		// Act
		await user.click(screen.getByTestId("niche-checkbox-generic"));
		await user.click(screen.getByTestId("cv-form-submit"));

		// Assert: sin niches el schema bloquea el submit.
		await waitFor(() => {
			expect(
				screen.getByText("Selecciona al menos un niche"),
			).toBeInTheDocument();
		});
		expect(onSubmit).not.toHaveBeenCalled();
	});

	it("Given el select de kind When emite soft Then el payload lo adopta", async () => {
		// Arrange
		const user = userEvent.setup();
		const onSubmit = vi.fn();
		render(
			<SkillCategoryForm
				initial={CATEGORY}
				onSubmit={onSubmit}
				submitting={false}
				catalogs={CATALOGS}
			/>,
		);

		// Act
		act(() => {
			capturedOnValueChange[0]?.("soft");
		});
		await user.click(screen.getByTestId("cv-form-submit"));

		// Assert
		await waitFor(() => {
			expect(onSubmit).toHaveBeenCalledWith({ ...CATEGORY, kind: "soft" });
		});
	});
});
