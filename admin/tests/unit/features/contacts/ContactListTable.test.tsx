import userEvent from "@testing-library/user-event";
import { render, screen, within } from "@tests/utils/render";
import { describe, expect, it, vi } from "vitest";
import { ContactListTable } from "@/features/contacts/components/ContactListTable";
import type { ContactListResponse } from "@/features/contacts/types";

/**
 * @module tests/unit/features/contacts/ContactListTable
 * @description ContactListTable: render del listado crudo paginado. Cubre
 *   loading (skeleton), vacio, con data (filas) y la paginacion (disabled de
 *   anterior/siguiente + callbacks onPageChange).
 */

const DATA: ContactListResponse = {
	items: [
		{
			id: "ct_1",
			created_at: "2026-05-20T10:00:00Z",
			name: "Ada",
			email: "ada@example.com",
			message: "Hola",
			company: "Acme",
			role: "CTO",
			service_type: "consulting",
			budget: "10k",
			timeline: "Q3",
			niche: "fintech",
			status: "new",
			session_id: "sess_1",
		},
		{
			id: "ct_2",
			created_at: "2026-05-21T10:00:00Z",
			name: "Linus",
			email: "linus@example.com",
			message: "Hey",
			company: null,
			role: null,
			service_type: null,
			budget: null,
			timeline: null,
			niche: "architect",
			status: "converted",
			session_id: null,
		},
	],
	page: 2,
	page_size: 50,
	total: 120,
	has_more: true,
};

describe("ContactListTable", () => {
	it("Given isLoading true When se renderiza Then muestra skeletons y NO filas de datos", () => {
		// Arrange + Act
		render(
			<ContactListTable
				data={undefined}
				isLoading={true}
				page={1}
				onPageChange={vi.fn()}
			/>,
		);

		// Assert
		expect(screen.queryByText("Ada")).not.toBeInTheDocument();
		expect(screen.getByText("Fecha")).toBeInTheDocument();
	});

	it("Given items vacios When isLoading false Then muestra el mensaje vacio", () => {
		// Arrange
		const empty: ContactListResponse = {
			items: [],
			page: 1,
			page_size: 50,
			total: 0,
			has_more: false,
		};

		// Act
		render(
			<ContactListTable
				data={empty}
				isLoading={false}
				page={1}
				onPageChange={vi.fn()}
			/>,
		);

		// Assert
		expect(
			screen.getByText("Sin contactos en el rango seleccionado."),
		).toBeInTheDocument();
	});

	it("Given data con items When se renderiza Then muestra nombre, email, niche y company", () => {
		// Arrange + Act
		render(
			<ContactListTable
				data={DATA}
				isLoading={false}
				page={2}
				onPageChange={vi.fn()}
			/>,
		);

		// Assert
		expect(screen.getByText("Ada")).toBeInTheDocument();
		expect(screen.getByText("ada@example.com")).toBeInTheDocument();
		expect(screen.getByText("Linus")).toBeInTheDocument();
		expect(screen.getByText("Acme")).toBeInTheDocument();
	});

	it("Given una company null When se renderiza Then muestra '-' en esa celda", () => {
		// Arrange + Act
		render(
			<ContactListTable
				data={DATA}
				isLoading={false}
				page={2}
				onPageChange={vi.fn()}
			/>,
		);
		const row = screen.getByText("Linus").closest("tr");
		if (!row) throw new Error("fila de Linus no encontrada");

		// Assert
		expect(within(row).getByText("-")).toBeInTheDocument();
	});

	it("Given page 2 con total When se renderiza Then muestra el resumen de pagina y total", () => {
		// Arrange + Act
		render(
			<ContactListTable
				data={DATA}
				isLoading={false}
				page={2}
				onPageChange={vi.fn()}
			/>,
		);

		// Assert
		expect(
			screen.getByText("Pagina 2 · 120 contactos en total"),
		).toBeInTheDocument();
	});

	it("Given page 1 When se renderiza Then el boton Anterior esta deshabilitado", () => {
		// Arrange
		const firstPage: ContactListResponse = { ...DATA, page: 1, has_more: true };

		// Act
		render(
			<ContactListTable
				data={firstPage}
				isLoading={false}
				page={1}
				onPageChange={vi.fn()}
			/>,
		);

		// Assert
		expect(screen.getByRole("button", { name: "Anterior" })).toBeDisabled();
		expect(screen.getByRole("button", { name: "Siguiente" })).toBeEnabled();
	});

	it("Given has_more false When se renderiza Then el boton Siguiente esta deshabilitado", () => {
		// Arrange
		const lastPage: ContactListResponse = { ...DATA, has_more: false };

		// Act
		render(
			<ContactListTable
				data={lastPage}
				isLoading={false}
				page={2}
				onPageChange={vi.fn()}
			/>,
		);

		// Assert
		expect(screen.getByRole("button", { name: "Siguiente" })).toBeDisabled();
	});

	it("Given click en Siguiente When se habilita Then llama onPageChange con page+1", async () => {
		// Arrange
		const onPageChange = vi.fn();
		const user = userEvent.setup();
		render(
			<ContactListTable
				data={DATA}
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

	it("Given click en Anterior When se habilita Then llama onPageChange con page-1", async () => {
		// Arrange
		const onPageChange = vi.fn();
		const user = userEvent.setup();
		render(
			<ContactListTable
				data={DATA}
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

	it("Given data undefined When isLoading false Then cae a items vacios y total 0", () => {
		// Arrange + Act
		render(
			<ContactListTable
				data={undefined}
				isLoading={false}
				page={1}
				onPageChange={vi.fn()}
			/>,
		);

		// Assert: sin total muestra solo "Pagina 1" (sin sufijo de total)
		expect(screen.getByText("Pagina 1")).toBeInTheDocument();
		expect(
			screen.getByText("Sin contactos en el rango seleccionado."),
		).toBeInTheDocument();
	});
});
