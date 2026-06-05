import { render, screen, userEvent, waitFor } from "@tests/utils/render";
import type { ReactElement } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { LoginChecklist } from "@/features/auth/components/login-checklist";
import { useAuthStore } from "@/features/auth/store/use-auth-store";
import type { MethodRequired } from "@/types/api";

/**
 * @module tests/unit/features/auth/components/login-checklist
 * @description Tests del checklist de login (metodos `required`). UI segun la
 *   cantidad de metodos: con 1 metodo el input se muestra directo; con >1 una
 *   LISTA selectora (al elegir uno -> su input + "Atras"; al completar -> vuelve
 *   a la lista auto). El tempToken es ROLLING (el verify del siguiente metodo
 *   usa el temp_token NUEVO); cierra el login con AuthResponse (setTokens +
 *   router.replace); permite cualquier orden; maneja email_code (envio previo) y
 *   el link de recovery.
 */

const { replaceMock } = vi.hoisted(() => ({ replaceMock: vi.fn() }));
vi.mock("next/navigation", () => ({
	useRouter: () => ({ push: vi.fn(), replace: replaceMock }),
}));

const PASSWORD_TOTP: MethodRequired[] = [
	{
		type: "password",
		input: "password",
		sent: null,
		dispatch_action: "verify-password",
	},
	{ type: "totp", input: "code6", sent: null, dispatch_action: "verify-totp" },
];

const EMAIL_CODE: MethodRequired[] = [
	{
		type: "email_code",
		input: "code8",
		sent: false,
		dispatch_action: "send-email-code",
	},
];

const PASSWORD_ONLY: MethodRequired[] = [
	{
		type: "password",
		input: "password",
		sent: null,
		dispatch_action: "verify-password",
	},
];

const WEBAUTHN_ONLY: MethodRequired[] = [
	{
		type: "webauthn",
		input: "webauthn",
		sent: null,
		dispatch_action: "login-verify",
	},
];

function renderChecklist(
	methodsRequired: MethodRequired[],
	initialPending: string[],
): void {
	render(
		(
			<LoginChecklist
				methodsRequired={methodsRequired}
				initialTempToken="cl-step2-0"
				email="user@test.com"
				initialPending={initialPending}
			/>
		) as ReactElement,
	);
}

/** En la vista lista (>1 metodo), entra a la sub-vista del input del metodo. */
async function openMethod(type: string): Promise<void> {
	const user = userEvent.setup();
	await user.click(screen.getByTestId(`picker-method-${type}`));
}

async function submitPassword(): Promise<void> {
	const user = userEvent.setup();
	await user.type(screen.getByTestId("checklist-password"), "a-strong-pass-12");
	await user.click(screen.getByRole("button", { name: /continuar/i }));
}

async function submitTotp(): Promise<void> {
	const user = userEvent.setup();
	await user.type(screen.getByTestId("checklist-totp"), "123456");
	await user.click(screen.getByRole("button", { name: /^verificar$/i }));
}

describe("LoginChecklist", () => {
	beforeEach(() => {
		replaceMock.mockClear();
		useAuthStore.getState().reset();
	});

	it("Given 1 metodo required When se monta Then muestra su input directo sin lista ni contador", () => {
		// Arrange / Act
		renderChecklist(PASSWORD_ONLY, ["password"]);

		// Assert: input directo, sin picker ni contador
		expect(screen.getByTestId("checklist-password")).toBeInTheDocument();
		expect(screen.queryByTestId("login-method-picker")).not.toBeInTheDocument();
		expect(screen.queryByTestId("checklist-progress")).not.toBeInTheDocument();
		// El recovery link sigue visible abajo
		expect(screen.getByTestId("checklist-use-recovery")).toBeInTheDocument();
	});

	it("Given >1 metodo required When se monta Then muestra la lista selectora y el contador, sin input", () => {
		// Arrange / Act
		renderChecklist(PASSWORD_TOTP, ["password", "totp"]);

		// Assert: picker con una fila por metodo + contador, sin inputs
		expect(screen.getByTestId("login-method-picker")).toBeInTheDocument();
		expect(screen.getByTestId("picker-method-password")).toBeInTheDocument();
		expect(screen.getByTestId("picker-method-totp")).toBeInTheDocument();
		expect(screen.getByTestId("checklist-progress")).toHaveTextContent(
			"0 de 2 completados",
		);
		expect(screen.queryByTestId("checklist-password")).not.toBeInTheDocument();
		expect(screen.getByTestId("checklist-use-recovery")).toBeInTheDocument();
	});

	it("Given la lista When click en una fila pendiente Then muestra su input y el boton Atras", async () => {
		// Arrange
		renderChecklist(PASSWORD_TOTP, ["password", "totp"]);

		// Act
		await openMethod("password");

		// Assert
		expect(screen.getByTestId("checklist-password")).toBeInTheDocument();
		expect(screen.getByTestId("checklist-back")).toBeInTheDocument();
	});

	it("Given la sub-vista de un input When click en Atras Then vuelve a la lista sin completar", async () => {
		// Arrange
		const user = userEvent.setup();
		renderChecklist(PASSWORD_TOTP, ["password", "totp"]);
		await openMethod("password");

		// Act
		await user.click(screen.getByTestId("checklist-back"));

		// Assert: vuelve a la lista, password sigue pendiente (0 de 2)
		expect(screen.getByTestId("login-method-picker")).toBeInTheDocument();
		expect(screen.getByTestId("checklist-progress")).toHaveTextContent(
			"0 de 2 completados",
		);
		expect(screen.getByTestId("picker-method-password")).not.toBeDisabled();
	});

	it("Given >1 metodo When se completa un factor Then vuelve a la lista auto con el check y 1 de 2", async () => {
		// Arrange
		renderChecklist(PASSWORD_TOTP, ["password", "totp"]);

		// Act: entrar a password y completarlo (verify rota a cl-step2-1 + [totp])
		await openMethod("password");
		await submitPassword();

		// Assert: vuelve a la lista, password con check + disabled, 1 de 2
		await waitFor(() => {
			expect(screen.getByTestId("checklist-progress")).toHaveTextContent(
				"1 de 2 completados",
			);
		});
		expect(screen.getByTestId("login-method-picker")).toBeInTheDocument();
		expect(screen.getByTestId("picker-method-password")).toBeDisabled();
	});

	it("Given el ultimo metodo When verify devuelve AuthResponse Then setTokens + replace(dashboard)", async () => {
		// Arrange
		renderChecklist(PASSWORD_TOTP, ["password", "totp"]);

		// Act: password (vuelve a la lista) -> totp (cierra con mfa_complete).
		// El temp es ROLLING: el verify-totp exige el temp NUEVO (cl-step2-1); el
		// handler responde AuthResponse SOLO si lo recibe.
		await openMethod("password");
		await submitPassword();
		await waitFor(() => {
			expect(screen.getByTestId("checklist-progress")).toHaveTextContent(
				"1 de 2 completados",
			);
		});
		await openMethod("totp");
		await submitTotp();

		// Assert
		await waitFor(() => {
			expect(useAuthStore.getState().accessToken).not.toBe(null);
		});
		expect(replaceMock).toHaveBeenCalledWith("/");
	});

	it("Given cualquier orden When totp primero luego password Then cierra el login", async () => {
		// Arrange
		renderChecklist(PASSWORD_TOTP, ["password", "totp"]);

		// Act: totp PRIMERO (temp cl-step2-0 -> rota a cl-step2-tp + [password]).
		await openMethod("totp");
		await submitTotp();
		await waitFor(() => {
			expect(screen.getByTestId("checklist-progress")).toHaveTextContent(
				"1 de 2 completados",
			);
		});
		// Luego password con el temp rotado (cl-step2-tp) -> cierra el login.
		await openMethod("password");
		await submitPassword();

		// Assert
		await waitFor(() => {
			expect(replaceMock).toHaveBeenCalledWith("/");
		});
		expect(useAuthStore.getState().accessToken).not.toBe(null);
	});

	it("Given 1 metodo email_code When click Enviar codigo Then envia y luego verify-code cierra", async () => {
		// Arrange: un solo metodo email_code (input directo, sent:false -> boton).
		const user = userEvent.setup();
		renderChecklist(EMAIL_CODE, ["email-code"]);

		// Act: enviar el code (send-email-code) -> el boton de envio desaparece.
		await user.click(screen.getByTestId("checklist-send-code"));
		await waitFor(() => {
			expect(
				screen.queryByTestId("checklist-send-code"),
			).not.toBeInTheDocument();
		});
		// Luego ingresar el code de 8 chars -> verify-code cierra el login.
		await user.type(screen.getByTestId("checklist-email-code"), "ABCDEFGH");
		await user.click(screen.getByRole("button", { name: /^verificar$/i }));

		// Assert
		await waitFor(() => {
			expect(replaceMock).toHaveBeenCalledWith("/");
		});
	});

	it("Given el link de recuperacion When click y luego Volver Then muestra recovery y regresa a los metodos", async () => {
		// Arrange
		const user = userEvent.setup();
		renderChecklist(PASSWORD_TOTP, ["password", "totp"]);

		// Act: abrir recovery
		await user.click(screen.getByTestId("checklist-use-recovery"));

		// Assert: aparece el input de recovery (10 chars) y el titulo (heading)
		expect(screen.getByTestId("checklist-recovery")).toBeInTheDocument();
		expect(
			screen.getByRole("heading", { name: /codigo de recuperacion/i }),
		).toBeInTheDocument();

		// Act: volver a los metodos -> regresa a la lista selectora
		await user.click(
			screen.getByRole("button", { name: /volver a los metodos/i }),
		);

		// Assert
		expect(screen.getByTestId("login-method-picker")).toBeInTheDocument();
		expect(screen.queryByTestId("checklist-recovery")).not.toBeInTheDocument();
	});

	it("Given 1 metodo webauthn When se monta Then muestra el boton de passkey directo", () => {
		// Arrange / Act
		renderChecklist(WEBAUTHN_ONLY, ["webauthn"]);

		// Assert: input directo del passkey (sin lista) + recovery link
		expect(screen.getByTestId("checklist-webauthn")).toBeInTheDocument();
		expect(screen.queryByTestId("login-method-picker")).not.toBeInTheDocument();
		expect(screen.getByTestId("checklist-use-recovery")).toBeInTheDocument();
	});
});
