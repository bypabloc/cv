import { fireEvent, render, screen, userEvent } from "@tests/utils/render";
import { describe, expect, it, vi } from "vitest";
import { NichePriorityPicker } from "@/features/cv-management/components/niche-priority-picker";

/**
 * @module tests/unit/features/cv-management/components/niche-priority-picker
 * @description Verifica el picker: checkbox por niche del catalogo, input de
 *   prioridad solo para los marcados, alta con prioridad default 1, baja
 *   eliminando la entrada del mapa y modo sin prioridad (profile).
 */

const NICHES = ["generic", "vibe", "fintech"];

describe("NichePriorityPicker", () => {
	it("Given seleccionados con prioridad When se renderiza Then solo los marcados muestran input", () => {
		// Arrange + Act
		render(
			<NichePriorityPicker
				niches={NICHES}
				selected={["generic"]}
				priority={{ generic: 5 }}
				onChange={vi.fn()}
			/>,
		);

		// Assert
		expect(screen.getByTestId("niche-checkbox-generic")).toBeChecked();
		expect(screen.getByTestId("niche-checkbox-vibe")).not.toBeChecked();
		expect(screen.getByTestId("niche-priority-generic")).toHaveValue(5);
		expect(screen.queryByTestId("niche-priority-vibe")).not.toBeInTheDocument();
	});

	it("Given un niche sin marcar When se marca Then agrega el slug con prioridad 1", async () => {
		// Arrange
		const user = userEvent.setup();
		const onChange = vi.fn();
		render(
			<NichePriorityPicker
				niches={NICHES}
				selected={["generic"]}
				priority={{ generic: 5 }}
				onChange={onChange}
			/>,
		);

		// Act
		await user.click(screen.getByTestId("niche-checkbox-vibe"));

		// Assert
		expect(onChange).toHaveBeenCalledWith({
			niches: ["generic", "vibe"],
			priority: { generic: 5, vibe: 1 },
		});
	});

	it("Given un niche marcado When se desmarca Then quita el slug y su prioridad", async () => {
		// Arrange
		const user = userEvent.setup();
		const onChange = vi.fn();
		render(
			<NichePriorityPicker
				niches={NICHES}
				selected={["generic", "vibe"]}
				priority={{ generic: 5, vibe: 3 }}
				onChange={onChange}
			/>,
		);

		// Act
		await user.click(screen.getByTestId("niche-checkbox-vibe"));

		// Assert
		expect(onChange).toHaveBeenCalledWith({
			niches: ["generic"],
			priority: { generic: 5 },
		});
	});

	it("Given el input de prioridad When se cambia Then emite el numero parseado", () => {
		// Arrange
		const onChange = vi.fn();
		render(
			<NichePriorityPicker
				niches={NICHES}
				selected={["generic"]}
				priority={{ generic: 5 }}
				onChange={onChange}
			/>,
		);

		// Act: fireEvent.change con el valor final (input controlado por el
		// padre, sin estado local — type concatenaria digitos).
		fireEvent.change(screen.getByTestId("niche-priority-generic"), {
			target: { value: "7" },
		});

		// Assert
		expect(onChange).toHaveBeenCalledWith({
			niches: ["generic"],
			priority: { generic: 7 },
		});
	});

	it("Given un valor no numerico When se cambia la prioridad Then cae a 0", () => {
		// Arrange
		const onChange = vi.fn();
		render(
			<NichePriorityPicker
				niches={NICHES}
				selected={["generic"]}
				priority={{ generic: 5 }}
				onChange={onChange}
			/>,
		);

		// Act
		fireEvent.change(screen.getByTestId("niche-priority-generic"), {
			target: { value: "abc" },
		});

		// Assert
		expect(onChange).toHaveBeenCalledWith({
			niches: ["generic"],
			priority: { generic: 0 },
		});
	});

	it("Given showPriority=false When se marca un niche Then NO toca el mapa de prioridades", async () => {
		// Arrange
		const user = userEvent.setup();
		const onChange = vi.fn();
		render(
			<NichePriorityPicker
				niches={NICHES}
				selected={[]}
				priority={{}}
				showPriority={false}
				onChange={onChange}
			/>,
		);

		// Act
		await user.click(screen.getByTestId("niche-checkbox-generic"));

		// Assert: sin inputs de prioridad y el mapa queda intacto.
		expect(onChange).toHaveBeenCalledWith({
			niches: ["generic"],
			priority: {},
		});
		expect(
			screen.queryByTestId("niche-priority-generic"),
		).not.toBeInTheDocument();
	});

	it("Given un error del schema When se renderiza Then lo muestra como alert", () => {
		// Arrange + Act
		render(
			<NichePriorityPicker
				niches={NICHES}
				selected={[]}
				priority={{}}
				onChange={vi.fn()}
				error="Selecciona al menos un niche"
			/>,
		);

		// Assert
		expect(screen.getByRole("alert")).toHaveTextContent(
			"Selecciona al menos un niche",
		);
	});
});
