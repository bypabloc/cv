import { server } from "@tests/mocks/server";
import { render, screen, userEvent, waitFor } from "@tests/utils/render";
import { delay, HttpResponse, http } from "msw";
import type { ReactElement } from "react";
import { describe, expect, it } from "vitest";
import { EmailCodeSetup } from "@/features/auth";
import { RecoveryCodesSection } from "@/features/settings/components/recovery-codes-section";

const API = "https://api.test.the-full-stack.com";

/**
 * @module tests/unit/features/settings/components/security-sections
 * @description Cubre la seccion recovery-codes (genera/regenera + modal con los
 *   10 codes) y el setup de email_code que componen el panel de seguridad.
 */

describe("RecoveryCodesSection", () => {
	it("Given sin codigos previos (total=0) When click Generar Then muestra los 10 codes en el modal", async () => {
		// Arrange: sin codigos previos -> boton 'Generar codigos' directo.
		const user = userEvent.setup();
		render((<RecoveryCodesSection total={0} remaining={0} />) as ReactElement);

		// Act
		await user.click(screen.getByRole("button", { name: /generar codigos/i }));

		// Assert: el modal abre con el primer code del MSW (RECOV00000)
		await waitFor(() => {
			expect(screen.getByText("RECOV00000")).toBeInTheDocument();
		});
		expect(screen.getByText("RECOV00009")).toBeInTheDocument();
	});

	it("Given codigos ya generados (total>0) When render Then muestra disponibles + boton Regenerar", () => {
		// Arrange + Act
		render((<RecoveryCodesSection total={10} remaining={4} />) as ReactElement);

		// Assert: estado 'ya generados' con el conteo + boton Regenerar (no Generar).
		expect(screen.getByText(/4 de 10 disponibles/i)).toBeInTheDocument();
		expect(
			screen.getByRole("button", { name: /regenerar codigos/i }),
		).toBeInTheDocument();
		expect(
			screen.queryByRole("button", { name: /^generar codigos$/i }),
		).toBeNull();
	});

	it("Given codigos ya generados When click Regenerar y confirma Then advierte y muestra los nuevos", async () => {
		// Arrange
		const user = userEvent.setup();
		render((<RecoveryCodesSection total={10} remaining={4} />) as ReactElement);

		// Act: abre el AlertDialog de advertencia.
		await user.click(
			screen.getByRole("button", { name: /regenerar codigos/i }),
		);
		// Assert: la advertencia menciona que invalida los 10 actuales.
		expect(screen.getByText(/invalida tus 10 codigos/i)).toBeInTheDocument();

		// Act: confirma -> regenera y muestra el modal con los nuevos codes.
		await user.click(screen.getByRole("button", { name: /^regenerar$/i }));
		await waitFor(() => {
			expect(screen.getByText("RECOV00000")).toBeInTheDocument();
		});
	});
});

describe("EmailCodeSetup", () => {
	it("Given el boton When click Then activa email_code y llama onDone", async () => {
		// Arrange
		const user = userEvent.setup();
		let done = false;
		render((<EmailCodeSetup onDone={() => (done = true)} />) as ReactElement);

		// Act
		await user.click(
			screen.getByRole("button", { name: /activar codigo por email/i }),
		);

		// Assert: el setup (204) dispara onDone para cerrar el Dialog padre.
		await waitFor(() => {
			expect(done).toBe(true);
		});
	});

	it("Given sin onDone When click Then activa email_code sin romper (boton deshabilitado tras click)", async () => {
		// Arrange: sin onDone -> cubre el branch `onDone?.()` undefined.
		const user = userEvent.setup();
		render((<EmailCodeSetup />) as ReactElement);

		// Act
		await user.click(
			screen.getByRole("button", { name: /activar codigo por email/i }),
		);

		// Assert: el boton vuelve a su label tras resolver (no quedo en error).
		await waitFor(() => {
			expect(
				screen.getByRole("button", { name: /activar codigo por email/i }),
			).toBeEnabled();
		});
	});

	it("Given el setup en vuelo When click Then muestra el estado 'Activando...' (branch isPending)", async () => {
		// Arrange: MSW con delay -> el boton queda en estado pending.
		server.use(
			http.post(`${API}/auth`, async () => {
				await delay(300);
				return new HttpResponse(null, { status: 204 });
			}),
		);
		const user = userEvent.setup();
		render((<EmailCodeSetup />) as ReactElement);

		// Act
		await user.click(
			screen.getByRole("button", { name: /activar codigo por email/i }),
		);

		// Assert: durante el request el label es 'Activando...' (disabled).
		await waitFor(() => {
			expect(screen.getByRole("button", { name: /activando/i })).toBeDisabled();
		});
	});
});
