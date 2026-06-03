import { server } from "@tests/mocks/server";
import { render, screen, waitFor } from "@tests/utils/render";
import { HttpResponse, http } from "msw";
import type { ReactElement } from "react";
import { describe, expect, it, vi } from "vitest";
import { SecurityOverviewPanel } from "@/features/settings/components/security-overview-panel";
import type { SecurityMethod } from "@/types/models";

const API_BASE = "https://api.test.the-full-stack.com";

/**
 * @function fiveMethods
 * @description Las 5 entradas que devuelve security.overview (totp,
 *   email_code, webauthn, recovery_codes, password) con su detail polimorfico.
 */
function fiveMethods(): SecurityMethod[] {
	return [
		{
			type: "totp",
			label: "Aplicacion de autenticacion (TOTP)",
			configured: true,
			enabled: true,
			required: false,
			preferred: true,
			created_at: "2026-05-01T00:00:00Z",
			last_used_at: null,
			detail: {},
		},
		{
			type: "email_code",
			label: "Codigo por email",
			configured: false,
			enabled: false,
			required: false,
			preferred: false,
			created_at: null,
			last_used_at: null,
			detail: {},
		},
		{
			type: "webauthn",
			label: "Passkeys (WebAuthn)",
			configured: true,
			enabled: true,
			required: false,
			preferred: false,
			created_at: "2026-05-02T00:00:00Z",
			last_used_at: null,
			detail: {
				credentials: [
					{
						credential_id: "cred_01",
						nickname: "YubiKey",
						transports: ["usb"],
						enabled: true,
						required: false,
						created_at: "2026-05-02T00:00:00Z",
						last_used_at: null,
					},
				],
			},
		},
		{
			type: "recovery_codes",
			label: "Codigos de recuperacion",
			configured: true,
			enabled: true,
			required: false,
			preferred: false,
			created_at: "2026-05-03T00:00:00Z",
			last_used_at: null,
			detail: { total: 10, remaining: 7 },
		},
		{
			type: "password",
			label: "Contrasena",
			configured: true,
			enabled: true,
			required: false,
			preferred: false,
			created_at: "2026-05-04T00:00:00Z",
			last_used_at: null,
			detail: { last_change_at: "2026-05-04T00:00:00Z" },
		},
	];
}

/**
 * @function mockOverview
 * @description Override del handler `/auth`: cuenta cuantas veces se invoca
 *   security.overview y responde las 5 entradas. Devuelve el contador.
 */
function mockOverview(methods: SecurityMethod[]): { count: () => number } {
	let calls = 0;
	server.use(
		http.post(`${API_BASE}/auth`, async ({ request }) => {
			const body = (await request.json()) as {
				operation: string;
				action: string;
			};
			if (body.operation === "security" && body.action === "overview") {
				calls += 1;
				return HttpResponse.json({
					is_valid: true,
					code: 0,
					data: { methods },
				});
			}
			return HttpResponse.json({ is_valid: true, code: 0, data: {} });
		}),
	);
	return { count: () => calls };
}

/**
 * @module tests/unit/features/settings/components/security-overview-panel
 * @description Verifica que el panel unificado renderiza las 5 filas del
 *   overview con UNA sola query (security.overview), muestra el badge de
 *   estado por metodo y expande los passkeys de webauthn.
 */

vi.mock("next/navigation", () => ({
	useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
}));

describe("SecurityOverviewPanel", () => {
	it("Given las 5 entradas When render Then muestra una fila por metodo", async () => {
		// Arrange
		mockOverview(fiveMethods());

		// Act
		render((<SecurityOverviewPanel />) as ReactElement);

		// Assert: las 5 labels estan presentes
		expect(
			await screen.findByText("Aplicacion de autenticacion (TOTP)"),
		).toBeInTheDocument();
		expect(screen.getByText("Codigo por email")).toBeInTheDocument();
		expect(screen.getByText("Passkeys (WebAuthn)")).toBeInTheDocument();
		expect(screen.getByText("Codigos de recuperacion")).toBeInTheDocument();
		expect(screen.getByText("Contrasena")).toBeInTheDocument();
	});

	it("Given el panel montado When render Then dispara security.overview UNA sola vez", async () => {
		// Arrange
		const tracker = mockOverview(fiveMethods());

		// Act
		render((<SecurityOverviewPanel />) as ReactElement);
		await screen.findByText("Aplicacion de autenticacion (TOTP)");

		// Assert: un solo request a security.overview alimenta las 5 filas
		await waitFor(() => {
			expect(tracker.count()).toBe(1);
		});
	});

	it("Given un metodo configured=false When render Then muestra No configurado", async () => {
		// Arrange: email_code esta configured=false
		mockOverview(fiveMethods());

		// Act
		render((<SecurityOverviewPanel />) as ReactElement);
		await screen.findByText("Codigo por email");

		// Assert
		expect(screen.getByText("No configurado")).toBeInTheDocument();
	});

	it("Given webauthn con un passkey When render Then expande el nickname del passkey", async () => {
		// Arrange
		mockOverview(fiveMethods());

		// Act
		render((<SecurityOverviewPanel />) as ReactElement);

		// Assert: el passkey YubiKey aparece como sub-fila
		expect(await screen.findByText("YubiKey")).toBeInTheDocument();
	});

	it("Given recovery_codes con total/remaining When render Then muestra el conteo", async () => {
		// Arrange
		mockOverview(fiveMethods());

		// Act
		render((<SecurityOverviewPanel />) as ReactElement);
		await screen.findByText("Codigos de recuperacion");

		// Assert
		expect(
			screen.getByText(/codigos disponibles: 7 de 10/i),
		).toBeInTheDocument();
	});

	it("Given password When render Then muestra el boton Cambiar contrasena sin switches", async () => {
		// Arrange
		mockOverview(fiveMethods());

		// Act
		render((<SecurityOverviewPanel />) as ReactElement);

		// Assert
		expect(
			await screen.findByRole("button", { name: /cambiar contrasena/i }),
		).toBeInTheDocument();
	});

	it("Given security.overview falla When render Then muestra el ErrorAlert", async () => {
		// Arrange
		server.use(
			http.post(`${API_BASE}/auth`, () =>
				HttpResponse.json(
					{ error: "SERVER_ERROR", code: 5000, message: "fallo" },
					{ status: 500 },
				),
			),
		);

		// Act
		render((<SecurityOverviewPanel />) as ReactElement);

		// Assert
		expect(await screen.findByText(/^error$/i)).toBeInTheDocument();
	});
});
