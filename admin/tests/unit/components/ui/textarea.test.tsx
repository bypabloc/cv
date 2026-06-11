import { render, screen } from "@tests/utils/render";
import { describe, expect, it } from "vitest";
import { Textarea } from "@/components/ui/textarea";

/**
 * @module tests/unit/components/ui/textarea
 * @description Verifica las clases base del Textarea shadcn: auto-grow
 *   (field-sizing-content) con piso min-h-28 y techo max-h-80, resize
 *   vertical y el focus ring/aria-invalid intactos.
 */

describe("Textarea", () => {
	it("Given el Textarea base When se renderiza Then trae auto-grow + min/max height + resize-y", () => {
		// Arrange + Act
		render(<Textarea data-testid="textarea-base" />);
		const textarea = screen.getByTestId("textarea-base");

		// Assert: clases exactas del sizing nuevo.
		expect(textarea.className).toContain("field-sizing-content");
		expect(textarea.className).toContain("min-h-28");
		expect(textarea.className).toContain("max-h-80");
		expect(textarea.className).toContain("resize-y");
		expect(textarea.className).not.toContain("min-h-16");
	});

	it("Given el Textarea When se renderiza Then conserva focus ring y estilo aria-invalid", () => {
		// Arrange + Act
		render(<Textarea data-testid="textarea-base" />);
		const textarea = screen.getByTestId("textarea-base");

		// Assert
		expect(textarea.className).toContain("focus-visible:ring-[3px]");
		expect(textarea.className).toContain("aria-invalid:border-destructive");
		expect(textarea).toHaveAttribute("data-slot", "textarea");
	});

	it("Given una className extra When se renderiza Then se mergea con la base", () => {
		// Arrange + Act
		render(<Textarea className="font-mono" data-testid="textarea-custom" />);

		// Assert
		expect(screen.getByTestId("textarea-custom").className).toContain(
			"font-mono",
		);
	});
});
