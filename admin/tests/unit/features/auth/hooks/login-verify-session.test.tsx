import { act, renderHook, waitFor } from "@testing-library/react";
import { makeJwt, nowSec } from "@tests/mocks/jwt";
import { server } from "@tests/mocks/server";
import { makeHookWrapper } from "@tests/utils/hook-wrapper";
import { HttpResponse, http } from "msw";
import { describe, expect, it, vi } from "vitest";
import { useLoginVerifyCode } from "@/features/auth/hooks/use-login-verify-code";
import { useLoginVerifyPassword } from "@/features/auth/hooks/use-login-verify-password";
import { useLoginVerifyTotp } from "@/features/auth/hooks/use-login-verify-totp";
import { useResendCode } from "@/features/auth/hooks/use-resend-code";
import { useSessionRefresh } from "@/features/auth/hooks/use-session-refresh";
import { useSetPassword } from "@/features/auth/hooks/use-set-password";
import { useAuthStore } from "@/features/auth/store/use-auth-store";

/**
 * @module tests/unit/features/auth/hooks/register-login-verify
 * @description Happy paths de los hooks de login/verify/session.
 */

// Fixture de password de prueba (NO un secreto real): 12 chars sinteticos.
const FAKE_PW = "x".repeat(12);

const { pushMock, replaceMock } = vi.hoisted(() => ({
	pushMock: vi.fn(),
	replaceMock: vi.fn(),
}));
vi.mock("next/navigation", () => ({
	useRouter: () => ({ push: pushMock, replace: replaceMock }),
}));

const API = "https://api.test.the-full-stack.com";

describe("useLoginVerifyCode", () => {
	it("Given submit When mutate Then setTokens + redirect", async () => {
		const { wrapper } = makeHookWrapper();
		const { result } = renderHook(() => useLoginVerifyCode(), { wrapper });

		await act(async () => {
			await result.current.mutateAsync({ code: "12345678", temp_token: "t" });
		});

		expect(useAuthStore.getState().user?.email).toBe("user@test.com");
	});
});

describe("useLoginVerifyPassword", () => {
	it("Given credenciales sin MFA When mutate Then setTokens + redirect", async () => {
		const { wrapper } = makeHookWrapper();
		const { result } = renderHook(() => useLoginVerifyPassword(), { wrapper });

		await act(async () => {
			await result.current.mutateAsync({ temp_token: "t", password: FAKE_PW });
		});

		expect(useAuthStore.getState().accessToken).not.toBe(null);
	});

	it("Given credenciales con MFA When mutate Then setea tempToken y llama onMfaRequired", async () => {
		server.use(
			http.post(`${API}/auth`, () =>
				HttpResponse.json({
					is_valid: true,
					code: 0,
					data: {
						temp_token: "step2",
						user_id: "usr_01",
						expires_in: 300,
						methods: ["totp"],
					},
				}),
			),
		);
		const onMfaRequired = vi.fn();
		const { wrapper } = makeHookWrapper();
		const { result } = renderHook(
			() => useLoginVerifyPassword({ onMfaRequired }),
			{ wrapper },
		);

		await act(async () => {
			await result.current.mutateAsync({ temp_token: "t", password: FAKE_PW });
		});

		expect(useAuthStore.getState().tempToken).toBe("step2");
		expect(onMfaRequired).toHaveBeenCalledWith(["totp"]);
	});
});

describe("useLoginVerifyTotp", () => {
	it("Given code valido When mutate Then setTokens + redirect", async () => {
		const { wrapper } = makeHookWrapper();
		const { result } = renderHook(() => useLoginVerifyTotp(), { wrapper });

		await act(async () => {
			await result.current.mutateAsync({ code: "123456", temp_token: "t" });
		});

		expect(useAuthStore.getState().accessToken).not.toBe(null);
	});

	it("Given code 000000 When mutate Then NO setea tokens (400)", async () => {
		const { wrapper } = makeHookWrapper();
		const { result } = renderHook(() => useLoginVerifyTotp(), { wrapper });

		await act(async () => {
			await result.current
				.mutateAsync({ code: "000000", temp_token: "t" })
				.catch(() => undefined);
		});

		expect(useAuthStore.getState().accessToken).toBe(null);
	});
});

describe("useSetPassword", () => {
	it("Given password When mutate Then setTokens + redirect", async () => {
		const { wrapper } = makeHookWrapper();
		const { result } = renderHook(() => useSetPassword(), { wrapper });

		await act(async () => {
			await result.current.mutateAsync({ password: FAKE_PW, temp_token: "t" });
		});

		expect(useAuthStore.getState().accessToken).not.toBe(null);
	});
});

describe("useResendCode", () => {
	it("Given temp_token When mutate Then resuelve ok", async () => {
		const { wrapper } = makeHookWrapper();
		const { result } = renderHook(() => useResendCode(), { wrapper });

		await act(async () => {
			const res = await result.current.mutateAsync({ temp_token: "t" });
			expect(res.data.ok).toBe(true);
		});
	});

	it("Given el backend falla When mutate Then propaga el error", async () => {
		server.use(
			http.post(`${API}/auth`, () =>
				HttpResponse.json(
					{ error: "RATE_LIMITED", code: 4290, message: "demasiado pronto" },
					{ status: 429 },
				),
			),
		);
		const { wrapper } = makeHookWrapper();
		const { result } = renderHook(() => useResendCode(), { wrapper });

		const error = await act(async () =>
			result.current.mutateAsync({ temp_token: "t" }).catch((e: unknown) => e),
		);

		expect(error).toBeInstanceOf(Error);
	});
});

describe("useSessionRefresh", () => {
	it("Given refresh en el store When mutate Then setea access + refresh nuevos", async () => {
		useAuthStore.setState({
			refreshToken: makeJwt({ sub: "usr_01", exp: nowSec() + 2_592_000 }),
		});
		const { wrapper } = makeHookWrapper();
		const { result } = renderHook(() => useSessionRefresh(), { wrapper });

		await act(async () => {
			await result.current.mutateAsync();
		});

		await waitFor(() => {
			expect(useAuthStore.getState().accessToken).not.toBe(null);
		});
	});
});
