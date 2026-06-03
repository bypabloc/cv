import { render, screen } from "@tests/utils/render";
import { describe, expect, it } from "vitest";
import { SessionsTable } from "@/features/sessions/components/SessionsTable";
import type { SessionRow } from "@/features/sessions/types";

/**
 * @module tests/unit/features/sessions/sessions-table
 * @description Render del listado de sesiones: skeleton mientras carga, mensaje
 *   vacio sin filas, filas con link al detalle + badge de dispositivo. Cubre el
 *   branch del browser_version presente vs ausente.
 */

const ROW: SessionRow = {
	session_id: "sess_1",
	first_seen_at: "2026-05-01T10:00:00Z",
	last_seen_at: "2026-05-20T10:00:00Z",
	browser: "Chrome",
	browser_version: "120",
	os: "Linux",
	device_type: "desktop",
	visits_count: 4,
};

describe("SessionsTable", () => {
	it("Given isLoading true When se renderiza Then muestra los headers de la tabla", () => {
		// Arrange + Act
		render(<SessionsTable items={[]} isLoading />);

		// Assert: header siempre visible; sin mensaje vacio mientras carga
		expect(screen.getByText("Sesion")).toBeInTheDocument();
		expect(screen.getByText("Navegador")).toBeInTheDocument();
		expect(
			screen.queryByText("Sin sesiones en el rango seleccionado."),
		).toBeNull();
	});

	it("Given items vacios y isLoading false When se renderiza Then muestra el mensaje vacio", () => {
		// Arrange + Act
		render(<SessionsTable items={[]} isLoading={false} />);

		// Assert
		expect(
			screen.getByText("Sin sesiones en el rango seleccionado."),
		).toBeInTheDocument();
	});

	it("Given una fila con browser_version When se renderiza Then muestra session_id, version, os, dispositivo y visitas", () => {
		// Arrange + Act
		render(<SessionsTable items={[ROW]} isLoading={false} />);

		// Assert
		const link = screen.getByRole("link", { name: "sess_1" });
		expect(link).toHaveAttribute("href", "/metrics/sessions/detail?id=sess_1");
		expect(screen.getByText("120")).toBeInTheDocument();
		expect(screen.getByText("Linux")).toBeInTheDocument();
		expect(screen.getByText("desktop")).toBeInTheDocument();
		expect(screen.getByText("4")).toBeInTheDocument();
	});

	it("Given una fila sin browser_version When se renderiza Then no muestra el span de version", () => {
		// Arrange
		const noVersion: SessionRow = { ...ROW, browser_version: "" };

		// Act
		render(<SessionsTable items={[noVersion]} isLoading={false} />);

		// Assert: solo el nombre del navegador, sin version
		expect(screen.getByText("Chrome")).toBeInTheDocument();
		expect(screen.queryByText("120")).toBeNull();
	});
});
