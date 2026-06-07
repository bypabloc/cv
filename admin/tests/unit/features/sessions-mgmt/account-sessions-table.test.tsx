import { render, screen, within } from "@tests/utils/render";
import { describe, expect, it } from "vitest";
import { AccountSessionsTable } from "@/features/sessions-mgmt/components/account-sessions-table";
import type { AccountSession } from "@/features/sessions-mgmt/types";

/**
 * @module tests/unit/features/sessions-mgmt/account-sessions-table
 * @description Render de la tabla de sesiones: badge "Sesion actual" en la
 *   sesion en curso y boton Revocar deshabilitado solo en esa fila.
 */

const SESSIONS: AccountSession[] = [
	{
		session_id: "sess_current",
		family_id: "fam_01",
		ip: "190.0.0.1",
		user_agent: "Mozilla/5.0 (Chrome)",
		created_at: "2026-05-01T10:00:00Z",
		last_seen_at: "2026-05-27T10:00:00Z",
		is_current: true,
	},
	{
		session_id: "sess_other",
		family_id: "fam_02",
		ip: "190.0.0.2",
		user_agent: "Mozilla/5.0 (Safari iPhone)",
		created_at: "2026-05-10T10:00:00Z",
		last_seen_at: "2026-05-26T10:00:00Z",
		is_current: false,
	},
];

describe("AccountSessionsTable", () => {
	it("Given 2 sesiones When se renderiza Then muestra ambas IPs", () => {
		// Arrange + Act
		render(<AccountSessionsTable sessions={SESSIONS} />);

		// Assert
		expect(screen.getByText("190.0.0.1")).toBeInTheDocument();
		expect(screen.getByText("190.0.0.2")).toBeInTheDocument();
	});

	it('Given una sesion actual When se renderiza Then muestra el badge "Sesion actual" una sola vez', () => {
		// Arrange + Act
		render(<AccountSessionsTable sessions={SESSIONS} />);

		// Assert
		const badges = screen.getAllByText("Sesion actual");
		expect(badges).toHaveLength(1);
	});

	it("Given una sesion actual When se renderiza Then su boton Revocar esta deshabilitado", () => {
		// Arrange + Act
		render(<AccountSessionsTable sessions={SESSIONS} />);
		const currentRow = screen.getByText("190.0.0.1").closest("tr");
		if (!currentRow) throw new Error("fila de la sesion actual no encontrada");

		// Assert
		const button = within(currentRow).getByRole("button", { name: "Revocar" });
		expect(button).toBeDisabled();
	});

	it("Given una sesion NO actual When se renderiza Then su boton Revocar esta habilitado", () => {
		// Arrange + Act
		render(<AccountSessionsTable sessions={SESSIONS} />);
		const otherRow = screen.getByText("190.0.0.2").closest("tr");
		if (!otherRow) throw new Error("fila de la otra sesion no encontrada");

		// Assert
		const button = within(otherRow).getByRole("button", { name: "Revocar" });
		expect(button).toBeEnabled();
	});

	it("Given sin sesiones When isLoading es false Then muestra el mensaje vacio", () => {
		// Arrange + Act
		render(<AccountSessionsTable sessions={[]} />);

		// Assert
		expect(screen.getByText("No tienes sesiones activas")).toBeInTheDocument();
	});

	it('Given una sesion sin ip ni user_agent When se renderiza Then muestra "-" en esas celdas', () => {
		// Arrange
		const nullSession: AccountSession = {
			session_id: "sess_null",
			family_id: "fam_03",
			ip: null,
			user_agent: null,
			created_at: "2026-05-15T10:00:00Z",
			last_seen_at: null,
			is_current: false,
		};

		// Act
		render(<AccountSessionsTable sessions={[nullSession]} />);
		const row = screen.getByText("Revocar").closest("tr");
		if (!row) throw new Error("fila de la sesion null no encontrada");

		// Assert: ip, user_agent y last_seen_at (relativeTime null) caen al fallback '-'
		const dashes = within(row).getAllByText("-");
		expect(dashes).toHaveLength(3);
	});
});
