import { render, screen, userEvent, within } from "@tests/utils/render";
import { describe, expect, it, vi } from "vitest";
import { EventListTable } from "@/features/events/components/EventListTable";
import type { EventListResponse } from "@/features/events/types";

/**
 * @module tests/unit/features/events/EventListTable
 * @description Listado crudo paginado de eventos. Cubre loading (skeleton rows),
 *   vacio (mensaje), con data (filas + badge niche), paginacion (botones
 *   anterior/siguiente con disabled segun page/has_more) y onPageChange.
 */

const DATA: EventListResponse = {
	items: [
		{
			created_at: "2026-05-20T10:00:00Z",
			visit_id: "vis_1",
			page_id: "pg_1",
			session_id: "sess_1",
			page_path: "/projects",
			niche: "fintech",
			viewport_width: 1920,
			viewport_height: 1080,
			event_type: "page_view",
			event_props: {},
		},
	],
	page: 1,
	page_size: 50,
	total: 1,
	has_more: false,
};

describe("EventListTable", () => {
	it("Given isLoading true When se renderiza Then muestra filas skeleton y deshabilita la paginacion", () => {
		// Arrange + Act
		const { container } = render(
			<EventListTable
				data={undefined}
				isLoading={true}
				page={1}
				onPageChange={() => {}}
			/>,
		);

		// Assert: hay skeletons y ambos botones de paginacion deshabilitados
		expect(container.querySelectorAll(".h-5").length).toBeGreaterThan(0);
		expect(screen.getByRole("button", { name: "Anterior" })).toBeDisabled();
		expect(screen.getByRole("button", { name: "Siguiente" })).toBeDisabled();
	});

	it("Given items vacios When no carga Then muestra el mensaje de vacio", () => {
		// Arrange + Act
		render(
			<EventListTable
				data={{ items: [], page: 1, page_size: 50, total: 0, has_more: false }}
				isLoading={false}
				page={1}
				onPageChange={() => {}}
			/>,
		);

		// Assert
		expect(
			screen.getByText("Sin eventos en el rango seleccionado."),
		).toBeInTheDocument();
	});

	it("Given una pagina con un evento When se renderiza Then muestra el tipo, path y niche", () => {
		// Arrange + Act
		render(
			<EventListTable
				data={DATA}
				isLoading={false}
				page={1}
				onPageChange={() => {}}
			/>,
		);

		// Assert
		expect(screen.getByText("page_view")).toBeInTheDocument();
		expect(screen.getByText("/projects")).toBeInTheDocument();
		expect(screen.getByText("fintech")).toBeInTheDocument();
		expect(screen.getByText("sess_1")).toBeInTheDocument();
		expect(
			screen.getByText("Pagina 1 · 1 eventos en total"),
		).toBeInTheDocument();
	});

	it("Given page 1 When se renderiza Then el boton Anterior esta deshabilitado", () => {
		// Arrange + Act
		render(
			<EventListTable
				data={DATA}
				isLoading={false}
				page={1}
				onPageChange={() => {}}
			/>,
		);

		// Assert
		expect(screen.getByRole("button", { name: "Anterior" })).toBeDisabled();
	});

	it("Given has_more false When se renderiza Then el boton Siguiente esta deshabilitado", () => {
		// Arrange + Act
		render(
			<EventListTable
				data={DATA}
				isLoading={false}
				page={1}
				onPageChange={() => {}}
			/>,
		);

		// Assert
		expect(screen.getByRole("button", { name: "Siguiente" })).toBeDisabled();
	});

	it("Given page 2 con has_more When click Siguiente Then llama onPageChange con la pagina siguiente", async () => {
		// Arrange
		const onPageChange = vi.fn();
		const user = userEvent.setup();
		render(
			<EventListTable
				data={{ ...DATA, page: 2, total: 100, has_more: true }}
				isLoading={false}
				page={2}
				onPageChange={onPageChange}
			/>,
		);

		// Act
		await user.click(screen.getByRole("button", { name: "Siguiente" }));

		// Assert
		expect(onPageChange).toHaveBeenCalledWith(3);
	});

	it("Given page 2 When click Anterior Then llama onPageChange con la pagina previa", async () => {
		// Arrange
		const onPageChange = vi.fn();
		const user = userEvent.setup();
		render(
			<EventListTable
				data={{ ...DATA, page: 2, total: 100, has_more: true }}
				isLoading={false}
				page={2}
				onPageChange={onPageChange}
			/>,
		);

		// Act
		await user.click(screen.getByRole("button", { name: "Anterior" }));

		// Assert
		expect(onPageChange).toHaveBeenCalledWith(1);
	});

	it("Given data undefined When no carga Then usa los defaults (vacio + paginacion deshabilitada)", () => {
		// Arrange + Act: data?.items ?? [] -> vacio; has_more ?? false; total ?? 0
		render(
			<EventListTable
				data={undefined}
				isLoading={false}
				page={1}
				onPageChange={() => {}}
			/>,
		);

		// Assert
		expect(
			screen.getByText("Sin eventos en el rango seleccionado."),
		).toBeInTheDocument();
		expect(screen.getByText("Pagina 1")).toBeInTheDocument();
		expect(screen.getByRole("button", { name: "Siguiente" })).toBeDisabled();
	});

	it("Given filas con data When se renderiza Then la celda de fecha no esta vacia", () => {
		// Arrange + Act
		render(
			<EventListTable
				data={DATA}
				isLoading={false}
				page={1}
				onPageChange={() => {}}
			/>,
		);
		const row = screen.getByText("page_view").closest("tr");
		if (!row) throw new Error("fila del evento no encontrada");

		// Assert: la primera celda (fecha) tiene contenido formateado (no '-')
		const firstCell = within(row).getAllByRole("cell")[0];
		expect(firstCell?.textContent).not.toBe("");
		expect(firstCell?.textContent).not.toBe("-");
	});
});
