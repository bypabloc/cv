import { render, screen, userEvent } from "@tests/utils/render";
import { describe, expect, it, vi } from "vitest";
import { BiLangField } from "@/features/cv-management/components/bilang-field";

/**
 * @module tests/unit/features/cv-management/components/bilang-field
 * @description Verifica el par es|en lado a lado: render de ambos inputs,
 *   onChange por locale, modo multiline (textarea) y errores por locale.
 */

describe("BiLangField", () => {
	it("Given un valor BiLang When se renderiza Then muestra ambos locales con sus testids", () => {
		// Arrange + Act
		render(
			<BiLangField
				name="role"
				label="Rol"
				value={{ es: "Arquitecto", en: "Architect" }}
				onChange={vi.fn()}
			/>,
		);

		// Assert
		expect(screen.getByTestId("bilang-role-es")).toHaveValue("Arquitecto");
		expect(screen.getByTestId("bilang-role-en")).toHaveValue("Architect");
		expect(screen.getByTestId("bilang-field-role")).toBeInTheDocument();
	});

	it("Given el input es When se tipea Then emite el par con el locale es actualizado", async () => {
		// Arrange
		const user = userEvent.setup();
		const onChange = vi.fn();
		render(
			<BiLangField
				name="role"
				label="Rol"
				value={{ es: "", en: "Architect" }}
				onChange={onChange}
			/>,
		);

		// Act
		await user.type(screen.getByTestId("bilang-role-es"), "A");

		// Assert
		expect(onChange).toHaveBeenCalledWith({ es: "A", en: "Architect" });
	});

	it("Given multiline When se renderiza Then usa textareas en ambos locales", () => {
		// Arrange + Act
		render(
			<BiLangField
				name="summary"
				label="Resumen"
				multiline
				value={{ es: "", en: "" }}
				onChange={vi.fn()}
			/>,
		);

		// Assert
		expect(screen.getByTestId("bilang-summary-es").tagName).toBe("TEXTAREA");
		expect(screen.getByTestId("bilang-summary-en").tagName).toBe("TEXTAREA");
	});

	it("Given un error en el locale en When se renderiza Then señala SOLO ese locale", () => {
		// Arrange + Act
		render(
			<BiLangField
				name="role"
				label="Rol"
				value={{ es: "Hola", en: "" }}
				onChange={vi.fn()}
				errors={{ en: "Falta el texto en inglés (en)" }}
			/>,
		);

		// Assert
		expect(screen.getByRole("alert")).toHaveTextContent(
			"Falta el texto en inglés (en)",
		);
		expect(screen.getByTestId("bilang-role-en")).toHaveAttribute(
			"aria-invalid",
			"true",
		);
		expect(screen.getByTestId("bilang-role-es")).not.toHaveAttribute(
			"aria-invalid",
		);
	});
});
