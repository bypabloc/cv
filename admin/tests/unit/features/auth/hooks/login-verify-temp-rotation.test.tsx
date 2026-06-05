import { act, renderHook } from "@testing-library/react";
import { server } from "@tests/mocks/server";
import { makeHookWrapper } from "@tests/utils/hook-wrapper";
import { HttpResponse, http } from "msw";
import { describe, expect, it, vi } from "vitest";
import { useLoginVerifyCode } from "@/features/auth/hooks/use-login-verify-code";
import { useLoginVerifyTotp } from "@/features/auth/hooks/use-login-verify-totp";
import { useAuthStore } from "@/features/auth/store/use-auth-store";

/**
 * @module tests/unit/features/auth/hooks/login-verify-temp-rotation
 * @description Cubre la rama del onSuccess de los hooks standalone de
 *   login.verify-code y login.verify-totp donde el VerifyResult NO es un
 *   AuthResponse (faltan factores): rota el temp_token del store en vez de
 *   setear tokens + redirigir. Complementa login-verify-session.test.tsx (que
 *   solo cubre la rama AuthResponse + el 400).
 */

const { replaceMock } = vi.hoisted(() => ({ replaceMock: vi.fn() }));
vi.mock("next/navigation", () => ({
	useRouter: () => ({ push: vi.fn(), replace: replaceMock }),
}));

const API = "https://api.test.the-full-stack.com";

describe("useLoginVerifyCode (factores pendientes)", () => {
	it("Given verify devuelve temp_token nuevo When mutate Then rota el temp del store y NO redirige", async () => {
		// Arrange: verify-code devuelve un TempTokenResponse rolling (sin
		// access_token, mfa_complete:false) -> rama setTempToken.
		useAuthStore.getState().reset();
		replaceMock.mockClear();
		server.use(
			http.post(`${API}/auth`, () =>
				HttpResponse.json({
					is_valid: true,
					code: 0,
					data: {
						temp_token: "rolled-1",
						step: 2,
						mfa_complete: false,
						methods: ["totp"],
					},
				}),
			),
		);
		const { wrapper } = makeHookWrapper();
		const { result } = renderHook(() => useLoginVerifyCode(), { wrapper });

		// Act
		await act(async () => {
			await result.current.mutateAsync({ code: "ABCDEFGH", temp_token: "t" });
		});

		// Assert: el temp del store rota; no se setean tokens ni se navega.
		expect(useAuthStore.getState().tempToken).toBe("rolled-1");
		expect(useAuthStore.getState().accessToken).toBe(null);
		expect(replaceMock).not.toHaveBeenCalled();
	});

	it("Given el backend falla con 400 When mutate Then NO toca el store (onError)", async () => {
		// Arrange: code malo -> 400 -> rama onError (toast).
		useAuthStore.getState().reset();
		server.use(
			http.post(`${API}/auth`, () =>
				HttpResponse.json(
					{ error: "INVALID_CODE", code: 4001, message: "Codigo invalido" },
					{ status: 400 },
				),
			),
		);
		const { wrapper } = makeHookWrapper();
		const { result } = renderHook(() => useLoginVerifyCode(), { wrapper });

		// Act
		await act(async () => {
			await result.current
				.mutateAsync({ code: "00000000", temp_token: "t" })
				.catch(() => undefined);
		});

		// Assert
		expect(useAuthStore.getState().accessToken).toBe(null);
		expect(useAuthStore.getState().tempToken).toBe(null);
	});
});

describe("useLoginVerifyTotp (factores pendientes)", () => {
	it("Given verify devuelve temp_token nuevo When mutate Then rota el temp del store y NO redirige", async () => {
		// Arrange: verify-totp devuelve un TempTokenResponse rolling -> rama
		// setTempToken (line 32).
		useAuthStore.getState().reset();
		replaceMock.mockClear();
		server.use(
			http.post(`${API}/auth`, () =>
				HttpResponse.json({
					is_valid: true,
					code: 0,
					data: {
						temp_token: "rolled-2",
						step: 2,
						mfa_complete: false,
						methods: ["password"],
					},
				}),
			),
		);
		const { wrapper } = makeHookWrapper();
		const { result } = renderHook(() => useLoginVerifyTotp(), { wrapper });

		// Act
		await act(async () => {
			await result.current.mutateAsync({ code: "123456", temp_token: "t" });
		});

		// Assert
		expect(useAuthStore.getState().tempToken).toBe("rolled-2");
		expect(useAuthStore.getState().accessToken).toBe(null);
		expect(replaceMock).not.toHaveBeenCalled();
	});
});
