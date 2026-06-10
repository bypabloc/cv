import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useToggleMethod } from "@/features/settings/hooks/use-toggle-method";
import { ApiError } from "@/lib/api-client";

/**
 * @module tests/unit/features/settings/hooks/use-toggle-method
 * @description Verifica el ruteo de dispatchToggle (webauthn por
 *   credential_id, MFA por kind con fallback al type, type desconocido) y
 *   el onError (409 MUST_KEEP_ONE con mensaje fijo vs error generico).
 */

const { authClientMock, toastError } = vi.hoisted(() => ({
	authClientMock: {
		webauthnEnable: vi.fn(),
		webauthnDisable: vi.fn(),
		mfaEnable: vi.fn(),
		mfaDisable: vi.fn(),
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
	authClientMock.webauthnEnable.mockReset().mockResolvedValue({ ok: true });
	authClientMock.webauthnDisable.mockReset().mockResolvedValue({ ok: true });
	authClientMock.mfaEnable.mockReset().mockResolvedValue({ ok: true });
	authClientMock.mfaDisable.mockReset().mockResolvedValue({ ok: true });
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

describe("useToggleMethod", () => {
	it("Given webauthn enable When muta Then llama webauthnEnable con el credential_id e invalida", async () => {
		// Arrange
		const { Wrapper, invalidateSpy } = createWrapper();
		const { result } = renderHook(() => useToggleMethod(), {
			wrapper: Wrapper,
		});

		// Act
		await act(async () => {
			await result.current.mutateAsync({
				type: "webauthn",
				recordId: "cred-1",
				enable: true,
			});
		});

		// Assert
		expect(authClientMock.webauthnEnable).toHaveBeenCalledWith({
			credential_id: "cred-1",
		});
		expect(invalidateSpy).toHaveBeenCalledWith({
			queryKey: ["auth", "security", "overview"],
		});
	});

	it("Given webauthn disable When muta Then llama webauthnDisable", async () => {
		// Arrange
		const { Wrapper } = createWrapper();
		const { result } = renderHook(() => useToggleMethod(), {
			wrapper: Wrapper,
		});

		// Act
		await act(async () => {
			await result.current.mutateAsync({
				type: "webauthn",
				recordId: "cred-2",
				enable: false,
			});
		});

		// Assert
		expect(authClientMock.webauthnDisable).toHaveBeenCalledWith({
			credential_id: "cred-2",
		});
	});

	it("Given webauthn sin recordId When muta Then falla con el mensaje de obligatorio", async () => {
		// Arrange
		const { Wrapper } = createWrapper();
		const { result } = renderHook(() => useToggleMethod(), {
			wrapper: Wrapper,
		});

		// Act
		await act(async () => {
			await result.current
				.mutateAsync({ type: "webauthn", enable: true })
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

	it("Given email_code sin kind When muta enable=false Then usa el type como kind", async () => {
		// Arrange
		const { Wrapper } = createWrapper();
		const { result } = renderHook(() => useToggleMethod(), {
			wrapper: Wrapper,
		});

		// Act
		await act(async () => {
			await result.current.mutateAsync({ type: "email_code", enable: false });
		});

		// Assert
		expect(authClientMock.mfaDisable).toHaveBeenCalledWith({
			kind: "email_code",
		});
	});

	it("Given totp con kind explicito When muta enable=true Then usa el kind", async () => {
		// Arrange
		const { Wrapper } = createWrapper();
		const { result } = renderHook(() => useToggleMethod(), {
			wrapper: Wrapper,
		});

		// Act
		await act(async () => {
			await result.current.mutateAsync({
				type: "totp",
				kind: "totp",
				enable: true,
			});
		});

		// Assert
		expect(authClientMock.mfaEnable).toHaveBeenCalledWith({ kind: "totp" });
	});

	it("Given un type desconocido When muta Then falla con el mensaje de no soportado", async () => {
		// Arrange
		const { Wrapper } = createWrapper();
		const { result } = renderHook(() => useToggleMethod(), {
			wrapper: Wrapper,
		});

		// Act
		await act(async () => {
			await result.current
				.mutateAsync({
					// reason: type invalido a proposito para cubrir el throw final.
					type: "recovery_codes" as never,
					enable: true,
				})
				.catch(() => undefined);
		});

		// Assert
		expect(toastError).toHaveBeenCalledWith(
			"No se puede activar/desactivar el metodo: recovery_codes",
		);
	});

	it("Given un 409 MUST_KEEP_ONE When muta Then toastea el mensaje fijo", async () => {
		// Arrange
		authClientMock.mfaDisable.mockRejectedValue(
			new ApiError(409, 4090, "MUST_KEEP_ONE_MFA_METHOD"),
		);
		const { Wrapper } = createWrapper();
		const { result } = renderHook(() => useToggleMethod(), {
			wrapper: Wrapper,
		});

		// Act
		await act(async () => {
			await result.current
				.mutateAsync({ type: "totp", enable: false })
				.catch(() => undefined);
		});

		// Assert
		expect(toastError).toHaveBeenCalledWith(
			"Debes conservar al menos un metodo",
		);
	});
});
