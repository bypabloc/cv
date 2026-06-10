import { render, screen, userEvent } from "@tests/utils/render";
import { describe, expect, it, vi } from "vitest";
import { TagInput } from "@/features/cv-management/components/tag-input";

/**
 * @module tests/unit/features/cv-management/components/tag-input
 * @description Verifica los chips con sugerencias: filtrado del catalogo al
 *   tipear, agregar por sugerencia/Enter/boton, dedupe, remover y el modo
 *   reorderable (tag-chip-up/down).
 */

const SUGGESTIONS = ["Python", "React", "Vue"];

describe("TagInput", () => {
	it("Given tags elegidos When se renderiza Then muestra un chip por tag", () => {
		// Arrange + Act
		render(
			<TagInput
				name="skills"
				label="Skills"
				value={["Python", "Vue"]}
				onChange={vi.fn()}
				suggestions={SUGGESTIONS}
			/>,
		);

		// Assert
		const chips = screen.getAllByTestId("tag-chip");
		expect(chips).toHaveLength(2);
		expect(chips[0]).toHaveAttribute("data-value", "Python");
		expect(chips[1]).toHaveAttribute("data-value", "Vue");
	});

	it("Given texto tipeado When matchea el catalogo Then muestra sugerencias sin las ya elegidas", async () => {
		// Arrange
		const user = userEvent.setup();
		render(
			<TagInput
				name="skills"
				label="Skills"
				value={["React"]}
				onChange={vi.fn()}
				suggestions={SUGGESTIONS}
			/>,
		);

		// Act: 'e' matchea React y Vue; React ya esta elegido.
		await user.type(screen.getByTestId("tag-input-skills-field"), "e");

		// Assert
		const suggestions = screen.getAllByTestId("tag-suggestion");
		expect(suggestions).toHaveLength(1);
		expect(suggestions[0]).toHaveAttribute("data-value", "Vue");
	});

	it("Given una sugerencia When se clickea Then agrega el tag y limpia el filtro", async () => {
		// Arrange
		const user = userEvent.setup();
		const onChange = vi.fn();
		render(
			<TagInput
				name="skills"
				label="Skills"
				value={[]}
				onChange={onChange}
				suggestions={SUGGESTIONS}
			/>,
		);

		// Act
		await user.type(screen.getByTestId("tag-input-skills-field"), "py");
		await user.click(screen.getByTestId("tag-suggestion"));

		// Assert
		expect(onChange).toHaveBeenCalledWith(["Python"]);
		expect(screen.getByTestId("tag-input-skills-field")).toHaveValue("");
	});

	it("Given texto libre When se presiona Enter Then crea el tag nuevo", async () => {
		// Arrange
		const user = userEvent.setup();
		const onChange = vi.fn();
		render(
			<TagInput
				name="skills"
				label="Skills"
				value={[]}
				onChange={onChange}
				suggestions={SUGGESTIONS}
			/>,
		);

		// Act
		await user.type(
			screen.getByTestId("tag-input-skills-field"),
			"E2E Skill{Enter}",
		);

		// Assert
		expect(onChange).toHaveBeenCalledWith(["E2E Skill"]);
	});

	it("Given el boton agregar When se clickea con texto Then agrega; vacio o duplicado Then no", async () => {
		// Arrange
		const user = userEvent.setup();
		const onChange = vi.fn();
		render(
			<TagInput
				name="skills"
				label="Skills"
				value={["Python"]}
				onChange={onChange}
				suggestions={SUGGESTIONS}
			/>,
		);

		// Act 1: vacio -> no agrega.
		await user.click(screen.getByTestId("tag-add"));
		expect(onChange).not.toHaveBeenCalled();

		// Act 2: duplicado -> no agrega.
		await user.type(screen.getByTestId("tag-input-skills-field"), "Python");
		await user.click(screen.getByTestId("tag-add"));
		expect(onChange).not.toHaveBeenCalled();

		// Act 3: nuevo -> agrega.
		await user.clear(screen.getByTestId("tag-input-skills-field"));
		await user.type(screen.getByTestId("tag-input-skills-field"), "Go");
		await user.click(screen.getByTestId("tag-add"));

		// Assert
		expect(onChange).toHaveBeenCalledWith(["Python", "Go"]);
	});

	it("Given el boton remover de un chip When se clickea Then quita ese tag", async () => {
		// Arrange
		const user = userEvent.setup();
		const onChange = vi.fn();
		render(
			<TagInput
				name="skills"
				label="Skills"
				value={["Python", "Vue"]}
				onChange={onChange}
				suggestions={SUGGESTIONS}
			/>,
		);

		// Act
		await user.click(
			screen.getAllByTestId("tag-chip-remove")[0] as HTMLElement,
		);

		// Assert
		expect(onChange).toHaveBeenCalledWith(["Vue"]);
	});

	it("Given reorderable When se sube el segundo chip Then invierte el orden", async () => {
		// Arrange
		const user = userEvent.setup();
		const onChange = vi.fn();
		render(
			<TagInput
				name="skills"
				label="Skills"
				value={["Python", "Vue"]}
				onChange={onChange}
				suggestions={SUGGESTIONS}
				reorderable
			/>,
		);

		// Act
		await user.click(screen.getAllByTestId("tag-chip-up")[1] as HTMLElement);

		// Assert
		expect(onChange).toHaveBeenCalledWith(["Vue", "Python"]);
		expect(screen.getAllByTestId("tag-chip-up")[0]).toBeDisabled();
		expect(screen.getAllByTestId("tag-chip-down")[1]).toBeDisabled();
	});

	it("Given reorderable When se baja el primer chip Then invierte el orden", async () => {
		// Arrange
		const user = userEvent.setup();
		const onChange = vi.fn();
		render(
			<TagInput
				name="skills"
				label="Skills"
				value={["Python", "Vue"]}
				onChange={onChange}
				suggestions={SUGGESTIONS}
				reorderable
			/>,
		);

		// Act
		await user.click(screen.getAllByTestId("tag-chip-down")[0] as HTMLElement);

		// Assert
		expect(onChange).toHaveBeenCalledWith(["Vue", "Python"]);
	});

	it("Given un error del schema When se renderiza Then lo muestra como alert", () => {
		// Arrange + Act
		render(
			<TagInput
				name="skills"
				label="Skills"
				value={[]}
				onChange={vi.fn()}
				suggestions={[]}
				error="Agrega al menos una skill"
			/>,
		);

		// Assert
		expect(screen.getByRole("alert")).toHaveTextContent(
			"Agrega al menos una skill",
		);
	});
});
