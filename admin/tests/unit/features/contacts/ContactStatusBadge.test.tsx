import { render, screen } from "@tests/utils/render";
import { describe, expect, it } from "vitest";
import { ContactStatusBadge } from "@/features/contacts/components/ContactStatusBadge";
import type { ContactStatus } from "@/features/contacts/types";

/**
 * @module tests/unit/features/contacts/ContactStatusBadge
 * @description ContactStatusBadge: muestra el label en espanol del estado del
 *   embudo segun el mapa STATUS_LABEL. Cubre los 5 estados validos.
 */

describe("ContactStatusBadge", () => {
	it.each<[ContactStatus, string]>([
		["new", "Nuevo"],
		["contacted", "Contactado"],
		["qualified", "Calificado"],
		["converted", "Convertido"],
		["rejected", "Rechazado"],
	])("Given status %s When se renderiza Then muestra el label %s", (status, label) => {
		// Arrange + Act
		render(<ContactStatusBadge status={status} />);

		// Assert
		expect(screen.getByText(label)).toBeInTheDocument();
	});

	it("Given un status fuera del union When se renderiza Then cae al fallback (valor crudo)", () => {
		// Arrange + Act: cast deliberado para ejercitar los branch ?? defensivos.
		render(<ContactStatusBadge status={"archived" as ContactStatus} />);

		// Assert: sin label mapeado -> muestra el valor crudo.
		expect(screen.getByText("archived")).toBeInTheDocument();
	});
});
