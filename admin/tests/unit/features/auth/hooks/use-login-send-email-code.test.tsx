import { act, renderHook } from "@testing-library/react";
import { server } from "@tests/mocks/server";
import { makeHookWrapper } from "@tests/utils/hook-wrapper";
import { HttpResponse, http } from "msw";
import { describe, expect, it, vi } from "vitest";
import { useLoginSendEmailCode } from "@/features/auth/hooks/use-login-send-email-code";

/**
 * @module tests/unit/features/auth/hooks/use-login-send-email-code
 * @description Verifica el envio del code de 8 chars (login.send-email-code):
 *   exito -> {ok:true} + toast.success; error -> toast.error con el mensaje.
 */

const { successMock, errorMock } = vi.hoisted(() => ({
	successMock: vi.fn(),
	errorMock: vi.fn(),
}));
vi.mock("sonner", () => ({
	toast: { success: successMock, error: errorMock },
}));

const API = "https://api.test.the-full-stack.com";

describe("useLoginSendEmailCode", () => {
	it("Given un temp_token valido When mutate Then devuelve {ok:true} y avisa el envio", async () => {
		// Arrange
		successMock.mockClear();
		const { wrapper } = makeHookWrapper();
		const { result } = renderHook(() => useLoginSendEmailCode(), { wrapper });

		// Act
		const response = await act(async () =>
			result.current.mutateAsync({ temp_token: "cl-email-0" }),
		);

		// Assert
		expect(response.data).toEqual({ ok: true });
		expect(successMock).toHaveBeenCalledWith("Te enviamos un codigo");
	});

	it("Given el backend falla When mutate Then dispara toast.error", async () => {
		// Arrange
		errorMock.mockClear();
		server.use(
			http.post(`${API}/auth`, () =>
				HttpResponse.json(
					{ error: "RATE_LIMITED", code: 4290, message: "Demasiados intentos" },
					{ status: 429 },
				),
			),
		);
		const { wrapper } = makeHookWrapper();
		const { result } = renderHook(() => useLoginSendEmailCode(), { wrapper });

		// Act
		await act(async () => {
			await result.current
				.mutateAsync({ temp_token: "cl-email-0" })
				.catch(() => undefined);
		});

		// Assert
		expect(errorMock).toHaveBeenCalledTimes(1);
	});
});
