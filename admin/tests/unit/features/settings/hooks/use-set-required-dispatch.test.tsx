import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useSetRequired } from "@/features/settings/hooks/use-set-required";
import { ApiError } from "@/lib/api-client";

/**
 * @module tests/unit/features/settings/hooks/use-set-required-dispatch
 * @description Verifica el ruteo de dispatchSetRequired (webauthn por
 *   credential_id, MFA con fallback de kind, password, type desconocido) y
 *   el onError (409 con mensaje fijo vs generico).
 */

const { authClientMock, toastError } = vi.hoisted(() => ({
	authClientMock: {
		webauthnSetRequired: vi.fn(),
		mfaSetRequired: vi.fn(),
		passwordSetRequired: vi.fn(),
	},
	toastError: vi.fn(),
}));

vi.mock("@/features/auth/api/auth-client", () => ({
	authClient: authClientMock,
}));
vi.mock("sonner", () => ({
	toast: { success: vi.fn(), error: toastError },
}));

beforeEach(() => {
	authClientMock.webauthnSetRequired
		.mockReset()
		.mockResolvedValue({ ok: true });
	authClientMock.mfaSetRequired.mockReset().mockResolvedValue({ ok: true });
	authClientMock.passwordSetRequired
		.mockReset()
		.mockResolvedValue({ ok: true });
	toastError.mockReset();
});

function createWrapper() {
	const client = new QueryClient({
		defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
	});
	const invalidateSpy = vi.spyOn(client, "invalidateQueries");
	function Wrapper({ children }: { children: ReactNode }) {
		return (
			<QueryClientProvider client={client}>{children}</QueryClientProvider>
		);
	}
	return { Wrapper, invalidateSpy };
}

describe("useSetRequired (dispatch)", () => {
	it("Given webauthn When muta Then llama webauthnSetRequired e invalida el overview", async () => {
		// Arrange
		const { Wrapper, invalidateSpy } = createWrapper();
		const { result } = renderHook(() => useSetRequired(), {
			wrapper: Wrapper,
		});

		// Act
		await act(async () => {
			await result.current.mutateAsync({
				type: "webauthn",
				recordId: "cred-1",
				required: true,
			});
		});

		// Assert
		expect(authClientMock.webauthnSetRequired).toHaveBeenCalledWith({
			credential_id: "cred-1",
			required: true,
		});
		expect(invalidateSpy).toHaveBeenCalledWith({
			queryKey: ["auth", "security", "overview"],
		});
	});

	it("Given webauthn sin recordId When muta Then falla con el mensaje de obligatorio", async () => {
		// Arrange
		const { Wrapper } = createWrapper();
		const { result } = renderHook(() => useSetRequired(), {
			wrapper: Wrapper,
		});

		// Act
		await act(async () => {
			await result.current
				.mutateAsync({ type: "webauthn", required: true })
				.catch(() => undefined);
		});

		// Assert
		await waitFor(() => {
			expect(result.current.isError).toBe(true);
		});
		expect(toastError).toHaveBeenCalledWith(
			"recordId (credential_id) es obligatorio para webauthn",
		);
	});

	it("Given email_code sin kind When muta Then usa el type como kind", async () => {
		// Arrange
		const { Wrapper } = createWrapper();
		const { result } = renderHook(() => useSetRequired(), {
			wrapper: Wrapper,
		});

		// Act
		await act(async () => {
			await result.current.mutateAsync({
				type: "email_code",
				required: false,
			});
		});

		// Assert
		expect(authClientMock.mfaSetRequired).toHaveBeenCalledWith({
			kind: "email_code",
			required: false,
		});
	});

	it("Given password When muta Then llama passwordSetRequired", async () => {
		// Arrange
		const { Wrapper } = createWrapper();
		const { result } = renderHook(() => useSetRequired(), {
			wrapper: Wrapper,
		});

		// Act
		await act(async () => {
			await result.current.mutateAsync({ type: "password", required: true });
		});

		// Assert
		expect(authClientMock.passwordSetRequired).toHaveBeenCalledWith({
			required: true,
		});
	});

	it("Given un type desconocido When muta Then falla con el mensaje de no soportado", async () => {
		// Arrange
		const { Wrapper } = createWrapper();
		const { result } = renderHook(() => useSetRequired(), {
			wrapper: Wrapper,
		});

		// Act
		await act(async () => {
			await result.current
				.mutateAsync({
					// reason: type invalido a proposito para cubrir el throw final.
					type: "recovery_codes" as never,
					required: true,
				})
				.catch(() => undefined);
		});

		// Assert
		expect(toastError).toHaveBeenCalledWith(
			"No se puede marcar como requerido el metodo: recovery_codes",
		);
	});

	it("Given un 409 When muta Then toastea Debes conservar al menos un metodo", async () => {
		// Arrange
		authClientMock.mfaSetRequired.mockRejectedValue(
			new ApiError(409, 4090, "MUST_KEEP_ONE_MFA_METHOD"),
		);
		const { Wrapper } = createWrapper();
		const { result } = renderHook(() => useSetRequired(), {
			wrapper: Wrapper,
		});

		// Act
		await act(async () => {
			await result.current
				.mutateAsync({ type: "totp", required: false })
				.catch(() => undefined);
		});

		// Assert
		expect(toastError).toHaveBeenCalledWith(
			"Debes conservar al menos un metodo",
		);
	});
});
