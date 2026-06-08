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
	it("Given las entradas When render Then muestra una fila por metodo (incluido email_code)", async () => {
		// Arrange
		mockOverview(fiveMethods());

		// Act
		render((<SecurityOverviewPanel />) as ReactElement);

		// Assert: los 5 metodos presentes, INCLUIDO email_code (ahora se lista
		// como un metodo configurable mas, no se filtra).
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

	it("Given un metodo visible configured=false When render Then muestra No configurado", async () => {
		// Arrange: el TOTP pasa a configured=false. email_code ya viene
		// configured=false en el fixture, asi que hay >=1 badge 'No configurado'.
		const methods = fiveMethods().map((m) =>
			m.type === "totp" ? { ...m, configured: false, enabled: false } : m,
		);
		mockOverview(methods);

		// Act
		render((<SecurityOverviewPanel />) as ReactElement);
		await screen.findByText("Aplicacion de autenticacion (TOTP)");

		// Assert: TOTP (forzado) + email_code (fixture) -> 2 badges 'No configurado'.
		expect(screen.getAllByText("No configurado")).toHaveLength(2);
	});

	it("Given webauthn con un passkey When render Then expande el nickname del passkey", async () => {
		// Arrange
		mockOverview(fiveMethods());

		// Act
		render((<SecurityOverviewPanel />) as ReactElement);

		// Assert: el passkey YubiKey aparece como sub-fila
		expect(await screen.findByText("YubiKey")).toBeInTheDocument();
	});

	it("Given un passkey When clic Eliminar Then dispara webauthn.delete-credential", async () => {
		// Arrange: capturar el request de delete-credential (apiFetch aplana body).
		mockOverview(fiveMethods());
		let deletedCredId: string | null = null;
		server.use(
			http.post(`${API_BASE}/auth`, async ({ request }) => {
				const body = (await request.json()) as {
					operation: string;
					action: string;
					credential_id?: string;
				};
				if (
					body.operation === "webauthn" &&
					body.action === "delete-credential"
				) {
					deletedCredId = body.credential_id ?? null;
					return new HttpResponse(null, { status: 204 });
				}
				return HttpResponse.json({
					is_valid: true,
					code: 0,
					data: { methods: fiveMethods() },
				});
			}),
		);
		const user = userEvent.setup();

		// Act
		render((<SecurityOverviewPanel />) as ReactElement);
		const passkeyRow = (await screen.findByText("YubiKey")).closest("li");
		expect(passkeyRow).not.toBeNull();
		await user.click(
			within(passkeyRow as HTMLElement).getByRole("button", {
				name: /eliminar/i,
			}),
		);

		// Assert: el backend recibe webauthn.delete-credential con el credential_id.
		await waitFor(() => {
			expect(deletedCredId).toBe("cred_01");
		});
	});

	it("Given email_code no configurado When clic Configurar Then abre el dialog de setup", async () => {
		// Arrange
		mockOverview(fiveMethods());
		const user = userEvent.setup();

		// Act
		render((<SecurityOverviewPanel />) as ReactElement);
		const emailRow = await screen.findByTestId("security-row-email_code");
		await user.click(
			within(emailRow).getByRole("button", { name: /configurar/i }),
		);

		// Assert: el dialog de setup de email_code aparece con su CTA.
		const activar = await screen.findByRole("button", {
			name: /activar codigo por email/i,
		});
		expect(activar).toBeInTheDocument();

		// Act: activar -> el setup (204) dispara onDone -> cierra el dialog.
		await user.click(activar);

		// Assert: el dialog se cierra (el CTA ya no esta en el DOM).
		await waitFor(() => {
			expect(
				screen.queryByRole("button", { name: /activar codigo por email/i }),
			).toBeNull();
		});
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

	it("Given password NO configurada When render Then ofrece 'Establecer contrasena' sin switch requerido", async () => {
		// Arrange: password sin configurar -> sin switch requerido + CTA distinto.
		const methods = fiveMethods().map((m) =>
			m.type === "password"
				? { ...m, configured: false, enabled: false, detail: {} }
				: m,
		);
		mockOverview(methods);

		// Act
		render((<SecurityOverviewPanel />) as ReactElement);
		const passwordRow = await screen.findByTestId("security-row-password");

		// Assert: CTA 'Establecer contrasena' y NO hay switch 'Requerido' (sin
		// password no hay flag required).
		expect(
			within(passwordRow).getByRole("button", {
				name: /establecer contrasena/i,
			}),
		).toBeInTheDocument();
		expect(within(passwordRow).queryByText(/requerido al loguear/i)).toBeNull();
	});

	it("Given recovery_codes ya generados When render Then ofrece Regenerar", async () => {
		// Arrange: total>0 -> la seccion muestra el flujo 'ya generados'.
		mockOverview(fiveMethods());

		// Act
		render((<SecurityOverviewPanel />) as ReactElement);
		await screen.findByText("Codigos de recuperacion");

		// Assert: con codigos previos, el boton es 'Regenerar' (no 'Generar').
		expect(
			screen.getByRole("button", { name: /regenerar codigos/i }),
		).toBeInTheDocument();
	});

	it("Given un passkey activo When toggle Activo off Then dispara webauthn.disable", async () => {
		// Arrange: capturar el request de disable del passkey.
		mockOverview(fiveMethods());
		let disabledCred: string | null = null;
		server.use(
			http.post(`${API_BASE}/auth`, async ({ request }) => {
				const body = (await request.json()) as {
					operation: string;
					action: string;
					credential_id?: string;
				};
				if (body.operation === "webauthn" && body.action === "disable") {
					disabledCred = body.credential_id ?? null;
					return new HttpResponse(null, { status: 204 });
				}
				return HttpResponse.json({
					is_valid: true,
					code: 0,
					data: { methods: fiveMethods() },
				});
			}),
		);
		const user = userEvent.setup();

		// Act: la sub-fila del passkey tiene 2 switches (Activo, Requerido); el
		// 1ro es 'Activo' -> apagarlo dispara webauthn.disable.
		render((<SecurityOverviewPanel />) as ReactElement);
		const passkeyRow = (await screen.findByText("YubiKey")).closest("li");
		const switches = within(passkeyRow as HTMLElement).getAllByRole("switch");
		await user.click(switches[0] as HTMLElement);

		// Assert
		await waitFor(() => {
			expect(disabledCred).toBe("cred_01");
		});
	});

	it("Given un TOTP confirmado When toggle Requerido y confirmo Then dispara mfa.set-required {required:true}", async () => {
		// Arrange: TOTP confirmado (configured+enabled+confirmed) con required=false.
		const methods = fiveMethods().map((m) =>
			m.type === "totp"
				? { ...m, configured: true, enabled: true, detail: { confirmed: true } }
				: m,
		);
		let requiredKind: string | null = null;
		server.use(
			http.post(`${API_BASE}/auth`, async ({ request }) => {
				const body = (await request.json()) as {
					operation: string;
					action: string;
					kind?: string;
				};
				if (body.operation === "mfa" && body.action === "set-required") {
					requiredKind = body.kind ?? null;
					return new HttpResponse(null, { status: 204 });
				}
				return HttpResponse.json({
					is_valid: true,
					code: 0,
					data: { methods },
				});
			}),
		);
		const user = userEvent.setup();

		// Act: la fila TOTP confirmada tiene 2 switches (Activo, Requerido); el
		// 2do es 'Requerido' -> activarlo abre el AlertDialog -> Confirmar.
		render((<SecurityOverviewPanel />) as ReactElement);
		const totpRow = await screen.findByTestId("security-row-totp");
		const switches = within(totpRow).getAllByRole("switch");
		await user.click(switches[1] as HTMLElement);
		await user.click(
			await screen.findByRole("button", { name: /^confirmar$/i }),
		);

		// Assert
		await waitFor(() => {
			expect(requiredKind).toBe("totp");
		});
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

	it("Given un TOTP confirmado When toggle Activo off Then dispara mfa.disable {kind:totp}", async () => {
		// Arrange: TOTP confirmado -> tiene switch 'Activo' (1er switch).
		const methods = fiveMethods().map((m) =>
			m.type === "totp"
				? { ...m, configured: true, enabled: true, detail: { confirmed: true } }
				: m,
		);
		let disabledKind: string | null = null;
		server.use(
			http.post(`${API_BASE}/auth`, async ({ request }) => {
				const body = (await request.json()) as {
					operation: string;
					action: string;
					kind?: string;
				};
				if (body.operation === "mfa" && body.action === "disable") {
					disabledKind = body.kind ?? null;
					return new HttpResponse(null, { status: 204 });
				}
				return HttpResponse.json({
					is_valid: true,
					code: 0,
					data: { methods },
				});
			}),
		);
		const user = userEvent.setup();

		// Act: el 1er switch de la fila TOTP es 'Activo'.
		render((<SecurityOverviewPanel />) as ReactElement);
		const totpRow = await screen.findByTestId("security-row-totp");
		const switches = within(totpRow).getAllByRole("switch");
		await user.click(switches[0] as HTMLElement);

		// Assert
		await waitFor(() => {
			expect(disabledKind).toBe("totp");
		});
	});

	it("Given un passkey When activo el switch Requerido y confirmo Then dispara webauthn.set-required", async () => {
		// Arrange
		mockOverview(fiveMethods());
		let requiredCred: string | null = null;
		server.use(
			http.post(`${API_BASE}/auth`, async ({ request }) => {
				const body = (await request.json()) as {
					operation: string;
					action: string;
					credential_id?: string;
				};
				if (body.operation === "webauthn" && body.action === "set-required") {
					requiredCred = body.credential_id ?? null;
					return new HttpResponse(null, { status: 204 });
				}
				return HttpResponse.json({
					is_valid: true,
					code: 0,
					data: { methods: fiveMethods() },
				});
			}),
		);
		const user = userEvent.setup();

		// Act: el 2do switch del passkey es 'Requerido' -> AlertDialog -> Confirmar.
		render((<SecurityOverviewPanel />) as ReactElement);
		const passkeyRow = (await screen.findByText("YubiKey")).closest("li");
		const switches = within(passkeyRow as HTMLElement).getAllByRole("switch");
		await user.click(switches[1] as HTMLElement);
		await user.click(
			await screen.findByRole("button", { name: /^confirmar$/i }),
		);

		// Assert
		await waitFor(() => {
			expect(requiredCred).toBe("cred_01");
		});
	});

	it("Given TOTP no configurado When clic Configurar Then abre el dialog de setup TOTP", async () => {
		// Arrange: TOTP no configurado -> boton 'Configurar'.
		const methods = fiveMethods().map((m) =>
			m.type === "totp" ? { ...m, configured: false, enabled: false } : m,
		);
		mockOverview(methods);
		const user = userEvent.setup();

		// Act
		render((<SecurityOverviewPanel />) as ReactElement);
		const totpRow = await screen.findByTestId("security-row-totp");
		await user.click(
			within(totpRow).getByRole("button", { name: /configurar/i }),
		);

		// Assert: el dialog de setup TOTP aparece (titulo Configurar TOTP).
		expect(
			await screen.findByText(/escanea el qr con tu app/i),
		).toBeInTheDocument();
	});

	it("Given password configured When clic Cambiar contrasena Then abre el dialog", async () => {
		// Arrange
		mockOverview(fiveMethods());
		const user = userEvent.setup();

		// Act
		render((<SecurityOverviewPanel />) as ReactElement);
		const passwordRow = await screen.findByTestId("security-row-password");
		await user.click(
			within(passwordRow).getByRole("button", { name: /cambiar contrasena/i }),
		);

		// Assert: el dialog de cambio de contrasena aparece (heading unico).
		const dialog = await screen.findByRole("dialog");
		expect(
			within(dialog).getByRole("heading", { name: /cambiar contrasena/i }),
		).toBeInTheDocument();
	});

	it("Given un TOTP pendiente (confirmed=false) When render Then muestra 'Pendiente' + Confirmar + Eliminar, sin switch requerido", async () => {
		// Arrange: el TOTP esta configurado pero NO confirmado (setup-totp
		// abandonado): detail.confirmed === false.
		const methods = fiveMethods().map((m) =>
			m.type === "totp"
				? {
						...m,
						configured: true,
						enabled: true,
						detail: { confirmed: false },
					}
				: m,
		);
		mockOverview(methods);

		// Act
		render((<SecurityOverviewPanel />) as ReactElement);
		await screen.findByText("Aplicacion de autenticacion (TOTP)");

		// Assert: badge pendiente + botones Confirmar/Eliminar; sin el switch
		// 'Requerido al loguear' (un pendiente no es marcable).
		const totpRow = screen.getByTestId("security-row-totp");
		expect(
			within(totpRow).getByText(/pendiente de confirmacion/i),
		).toBeInTheDocument();
		expect(
			within(totpRow).getByRole("button", { name: /confirmar/i }),
		).toBeInTheDocument();
		expect(
			within(totpRow).getByRole("button", { name: /eliminar/i }),
		).toBeInTheDocument();
		expect(within(totpRow).queryByText(/requerido al loguear/i)).toBeNull();
	});

	it("Given un TOTP pendiente When clic Eliminar Then dispara mfa.delete {kind:totp}", async () => {
		// Arrange: capturar el request de mfa.delete (hard-delete, NO disable).
		// apiFetch APLANA el body -> kind queda en la raiz.
		const methods = fiveMethods().map((m) =>
			m.type === "totp"
				? {
						...m,
						configured: true,
						enabled: true,
						detail: { confirmed: false },
					}
				: m,
		);
		let deletedKind: string | null = null;
		server.use(
			http.post(`${API_BASE}/auth`, async ({ request }) => {
				const body = (await request.json()) as {
					operation: string;
					action: string;
					kind?: string;
				};
				if (body.operation === "mfa" && body.action === "delete") {
					deletedKind = body.kind ?? null;
					return new HttpResponse(null, { status: 204 });
				}
				return HttpResponse.json({
					is_valid: true,
					code: 0,
					data: { methods },
				});
			}),
		);
		const user = userEvent.setup();

		// Act
		render((<SecurityOverviewPanel />) as ReactElement);
		await screen.findByText("Aplicacion de autenticacion (TOTP)");
		const totpRow = screen.getByTestId("security-row-totp");
		await user.click(
			within(totpRow).getByRole("button", { name: /eliminar/i }),
		);

		// Assert: el backend recibe mfa.delete con kind=totp (NO disable).
		await waitFor(() => {
			expect(deletedKind).toBe("totp");
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
