import { server } from "@tests/mocks/server";
import { render, screen, userEvent, waitFor } from "@tests/utils/render";
import { delay, HttpResponse, http } from "msw";
import type { ReactElement } from "react";
import { describe, expect, it, vi } from "vitest";
import { ChangeEmailForm } from "@/features/settings/components/change-email-form";
import { ChangePasswordForm } from "@/features/settings/components/change-password-form";
import { ConfirmEmailChange } from "@/features/settings/components/confirm-email-change";
import { EmailCodeSection } from "@/features/settings/components/email-code-section";
import { ProfileForm } from "@/features/settings/components/profile-form";
import { RecoveryCodesSection } from "@/features/settings/components/recovery-codes-section";
import { WebAuthnCredentialsList } from "@/features/settings/components/webauthn-credentials-list";

/**
 * @module tests/unit/features/settings/components/settings-components-branches
 * @description Cubre ramas faltantes de los componentes de settings: estados
 *   isLoading/isError/empty/pending, fallbacks `?? ''`/`?? 'Passkey'`, el
 *   Reintentar del ErrorAlert y el onClose del RecoveryCodesModal.
 */

const { searchParamsMock } = vi.hoisted(() => ({
	searchParamsMock: { get: vi.fn() },
}));
vi.mock("next/navigation", () => ({
	useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
	useSearchParams: () => searchParamsMock,
}));

vi.mock("@simplewebauthn/browser", () => ({
	startRegistration: vi.fn(),
	startAuthentication: vi.fn(),
}));

const API = "https://api.test.the-full-stack.com";

describe("ProfileForm estados", () => {
	it("Given profile.get lento When monta Then muestra el LoadingSpinner", () => {
		// Arrange
		server.use(
			http.post(`${API}/users`, async () => {
				await delay(300);
				return HttpResponse.json({ is_valid: true, code: 0, data: {} });
			}),
		);

		// Act
		render((<ProfileForm />) as ReactElement);

		// Assert: rama isLoading
		expect(screen.getByRole("status")).toBeInTheDocument();
	});

	it("Given profile.get 500 When monta Then muestra el ErrorAlert", async () => {
		// Arrange
		server.use(
			http.post(`${API}/users`, () =>
				HttpResponse.json(
					{ error: "SERVER_ERROR", code: 5000, message: "Falla" },
					{ status: 500 },
				),
			),
		);

		// Act
		render((<ProfileForm />) as ReactElement);

		// Assert: rama isError
		await waitFor(() => {
			expect(screen.getByText("Falla")).toBeInTheDocument();
		});
	});

	it('Given un perfil sin display_name When monta Then usa "" (rama ?? )', async () => {
		// Arrange: display_name null -> el reset usa `displayName ?? ''`
		server.use(
			http.post(`${API}/users`, () =>
				HttpResponse.json({
					is_valid: true,
					code: 0,
					// El backend responde el perfil FLAT (campos al nivel raiz
					// de `data`, NO anidados en `profile`).
					data: {
						id: "usr_01",
						email: "sinnombre@test.com",
						display_name: null,
						status: "active",
						locale: "es",
						timezone: "UTC",
						marketing_consent: false,
						created_at: "2026-01-01T00:00:00Z",
					},
				}),
			),
		);

		// Act
		render((<ProfileForm />) as ReactElement);

		// Assert
		const input = await screen.findByLabelText(/nombre para mostrar/i);
		await waitFor(() => {
			expect(input).toHaveValue("");
		});
	});
});

describe("ChangePasswordForm pending", () => {
	it("Given submit en vuelo When responde lento Then muestra Actualizando...", async () => {
		// Arrange
		server.use(
			http.post(`${API}/users`, async () => {
				await delay(300);
				return HttpResponse.json({
					is_valid: true,
					code: 0,
					data: { ok: true },
				});
			}),
		);
		const user = userEvent.setup();
		render((<ChangePasswordForm />) as ReactElement);

		// Act
		await user.type(
			screen.getByLabelText(/contrasena actual/i),
			"old-pass-123",
		);
		await user.type(
			screen.getByLabelText(/^nueva contrasena$/i),
			"nueva-pass-larga-1",
		);
		await user.type(
			screen.getByLabelText(/confirmar nueva contrasena/i),
			"nueva-pass-larga-1",
		);
		await user.click(
			screen.getByRole("button", { name: /actualizar contrasena/i }),
		);

		// Assert: rama isPending
		await waitFor(() => {
			expect(
				screen.getByRole("button", { name: /actualizando/i }),
			).toBeDisabled();
		});
	});
});

describe("ChangeEmailForm pending", () => {
	it("Given submit en vuelo When responde lento Then muestra Enviando...", async () => {
		// Arrange
		server.use(
			http.post(`${API}/users`, async () => {
				await delay(300);
				return HttpResponse.json({
					is_valid: true,
					code: 0,
					data: { request_id: "r", expires_in: 900 },
				});
			}),
		);
		const user = userEvent.setup();
		render((<ChangeEmailForm />) as ReactElement);

		// Act
		await user.type(screen.getByLabelText(/nuevo email/i), "nuevo@test.com");
		await user.click(
			screen.getByRole("button", { name: /enviar confirmacion/i }),
		);

		// Assert
		await waitFor(() => {
			expect(screen.getByRole("button", { name: /enviando/i })).toBeDisabled();
		});
	});
});

describe("EmailCodeSection pending", () => {
	it("Given setup en vuelo When responde lento Then muestra Activando...", async () => {
		// Arrange
		server.use(
			http.post(`${API}/auth`, async () => {
				await delay(300);
				return HttpResponse.json({
					is_valid: true,
					code: 0,
					data: { methods: [], webauthn_count: 0, total_mfa: 1 },
				});
			}),
		);
		const user = userEvent.setup();
		render((<EmailCodeSection />) as ReactElement);

		// Act
		await user.click(
			screen.getByRole("button", { name: /activar codigo por email/i }),
		);

		// Assert
		await waitFor(() => {
			expect(screen.getByRole("button", { name: /activando/i })).toBeDisabled();
		});
	});
});

describe("RecoveryCodesSection pending + cierre", () => {
	it("Given generar en vuelo When responde lento Then muestra Generando...", async () => {
		// Arrange
		server.use(
			http.post(`${API}/auth`, async () => {
				await delay(300);
				return HttpResponse.json({
					is_valid: true,
					code: 0,
					data: { codes: ["A", "B"] },
				});
			}),
		);
		const user = userEvent.setup();
		render((<RecoveryCodesSection />) as ReactElement);

		// Act
		await user.click(screen.getByRole("button", { name: /generar codigos/i }));

		// Assert
		await waitFor(() => {
			expect(screen.getByRole("button", { name: /generando/i })).toBeDisabled();
		});
	});

	it('Given el modal abierto When click "Ya los guarde" Then cierra (onClose)', async () => {
		// Arrange
		const user = userEvent.setup();
		render((<RecoveryCodesSection />) as ReactElement);
		await user.click(screen.getByRole("button", { name: /generar codigos/i }));
		await screen.findByText("RECOV00000");

		// Act: cubre el `onClose={() => setOpen(false)}`
		await user.click(screen.getByRole("button", { name: /ya los guarde/i }));

		// Assert
		await waitFor(() => {
			expect(screen.queryByText("RECOV00000")).not.toBeInTheDocument();
		});
	});
});

describe("WebAuthnCredentialsList estados", () => {
	it("Given list-credentials lento When monta Then muestra el LoadingSpinner", () => {
		// Arrange
		server.use(
			http.post(`${API}/auth`, async () => {
				await delay(300);
				return HttpResponse.json({
					is_valid: true,
					code: 0,
					data: { credentials: [] },
				});
			}),
		);

		// Act
		render((<WebAuthnCredentialsList />) as ReactElement);

		// Assert: rama isLoading
		expect(screen.getByRole("status")).toBeInTheDocument();
	});

	it("Given list-credentials 500 When monta Then ErrorAlert + Reintentar", async () => {
		// Arrange
		server.use(
			http.post(`${API}/auth`, () =>
				HttpResponse.json(
					{ error: "SERVER_ERROR", code: 5000, message: "Falla creds" },
					{ status: 500 },
				),
			),
		);
		const user = userEvent.setup();
		render((<WebAuthnCredentialsList />) as ReactElement);
		await screen.findByText("Falla creds");

		// Act: cubre el `onRetry={() => credentials.refetch()}`
		await user.click(screen.getByRole("button", { name: /reintentar/i }));

		// Assert: tras el retry el ErrorAlert sigue (mismo handler 500)
		await waitFor(() => {
			expect(screen.getByText("Falla creds")).toBeInTheDocument();
		});
	});

	it("Given sin passkeys When monta Then muestra el estado vacio", async () => {
		// Arrange
		server.use(
			http.post(`${API}/auth`, () =>
				HttpResponse.json({
					is_valid: true,
					code: 0,
					data: { credentials: [] },
				}),
			),
		);

		// Act
		render((<WebAuthnCredentialsList />) as ReactElement);

		// Assert: rama length === 0
		expect(
			await screen.findByText(/no tienes passkeys registrados/i),
		).toBeInTheDocument();
	});

	it('Given un passkey sin nickname When monta Then usa "Passkey" (rama ??)', async () => {
		// Arrange: nickname null -> fallback `?? 'Passkey'`
		server.use(
			http.post(`${API}/auth`, () =>
				HttpResponse.json({
					is_valid: true,
					code: 0,
					data: {
						credentials: [
							{
								id: "cred_no_nick",
								nickname: null,
								last_used_at: null,
								created_at: "2026-01-01T00:00:00Z",
							},
						],
					},
				}),
			),
		);

		// Act
		render((<WebAuthnCredentialsList />) as ReactElement);

		// Assert
		expect(await screen.findByText("Passkey")).toBeInTheDocument();
	});
});

describe("ConfirmEmailChange estados", () => {
	it("Given confirm 500 When monta Then muestra error + Reintentar", async () => {
		// Arrange
		searchParamsMock.get.mockReturnValue("tok-err");
		server.use(
			http.post(`${API}/users`, () =>
				HttpResponse.json(
					{ error: "INVALID_TOKEN", code: 4000, message: "Token invalido" },
					{ status: 400 },
				),
			),
		);
		const user = userEvent.setup();
		render((<ConfirmEmailChange />) as ReactElement);
		await screen.findByText(/no pudimos confirmar el cambio de email/i);

		// Act: cubre el onClick del boton Reintentar
		await user.click(screen.getByRole("button", { name: /reintentar/i }));

		// Assert
		await waitFor(() => {
			expect(
				screen.getByText(/no pudimos confirmar el cambio de email/i),
			).toBeInTheDocument();
		});
	});
});
