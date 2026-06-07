import { server } from "@tests/mocks/server";
import {
	render,
	screen,
	userEvent,
	waitFor,
	within,
} from "@tests/utils/render";
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
 * @description Verifica que el panel unificado renderiza las filas del
 *   overview con UNA sola query (security.overview), muestra el badge de
 *   estado por metodo y expande los passkeys de webauthn.
 */

vi.mock("next/navigation", () => ({
	useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
}));

describe("SecurityOverviewPanel", () => {
	it("Given las entradas When render Then muestra una fila por metodo (sin email_code)", async () => {
		// Arrange
		mockOverview(fiveMethods());

		// Act
		render((<SecurityOverviewPanel />) as ReactElement);

		// Assert: TOTP, WebAuthn, recovery y password presentes; email_code NO
		// (es el canal de entrada del login, no un metodo configurable aqui).
		expect(
			await screen.findByText("Aplicacion de autenticacion (TOTP)"),
		).toBeInTheDocument();
		expect(screen.getByText("Passkeys (WebAuthn)")).toBeInTheDocument();
		expect(screen.getByText("Codigos de recuperacion")).toBeInTheDocument();
		expect(screen.getByText("Contrasena")).toBeInTheDocument();
		expect(screen.queryByText("Codigo por email")).toBe(null);
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

	it("Given un metodo visible configured=false When render Then muestra No configurado", async () => {
		// Arrange: el TOTP pasa a configured=false (email_code se filtra, asi
		// que se usa un metodo que SI se renderiza).
		const methods = fiveMethods().map((m) =>
			m.type === "totp" ? { ...m, configured: false, enabled: false } : m,
		);
		mockOverview(methods);

		// Act
		render((<SecurityOverviewPanel />) as ReactElement);
		await screen.findByText("Aplicacion de autenticacion (TOTP)");

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

	it("Given password configured When render Then muestra Cambiar contrasena Y el switch Requerido al loguear", async () => {
		// Arrange
		mockOverview(fiveMethods());

		// Act
		render((<SecurityOverviewPanel />) as ReactElement);

		// Assert: la password ahora ofrece el control de required (igual que
		// TOTP/webauthn), no solo el boton de cambio.
		const passwordRow = await screen.findByTestId("security-row-password");
		expect(
			within(passwordRow).getByRole("button", { name: /cambiar contrasena/i }),
		).toBeInTheDocument();
		expect(
			within(passwordRow).getByText(/requerido al loguear/i),
		).toBeInTheDocument();
	});

	it("Given password required=false When activo el switch Then dispara security.password-set-required {required:true}", async () => {
		// Arrange: overview con SOLO la password (aisla el switch bajo prueba;
		// otras filas tienen sus propios RequiredSwitch que ensucian el assert).
		// UN solo handler sirve el overview y captura el password-set-required.
		// apiFetch APLANA el body ({operation, action, ...data}), asi que
		// `required` viaja al nivel raiz del request, NO en `data`.
		const onlyPassword = fiveMethods().filter((m) => m.type === "password");
		let capturedRequired: boolean | null = null;
		server.use(
			http.post(`${API_BASE}/auth`, async ({ request }) => {
				const body = (await request.json()) as {
					operation: string;
					action: string;
					required?: boolean;
				};
				if (
					body.operation === "security" &&
					body.action === "password-set-required"
				) {
					capturedRequired = body.required ?? null;
					return new HttpResponse(null, { status: 204 });
				}
				return HttpResponse.json({
					is_valid: true,
					code: 0,
					data: { methods: onlyPassword },
				});
			}),
		);
		const user = userEvent.setup();

		// Act: activar el switch de la password -> AlertDialog -> Confirmar.
		render((<SecurityOverviewPanel />) as ReactElement);
		const passwordRow = await screen.findByTestId("security-row-password");
		await user.click(within(passwordRow).getByRole("switch"));
		// El AlertDialog de advertencia se monta en un portal; esperar su
		// titulo antes de confirmar.
		await screen.findByText(/hacer obligatorio este metodo/i);
		await user.click(screen.getByRole("button", { name: /confirmar/i }));

		// Assert: el backend recibe password-set-required con required=true.
		await waitFor(() => {
			expect(capturedRequired).toBe(true);
		});
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
