import type { AuthenticationResponseJSON } from "@simplewebauthn/browser";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook } from "@testing-library/react";
import { server } from "@tests/mocks/server";
import { HttpResponse, http } from "msw";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useWebauthnLoginVerify } from "@/features/auth/hooks/use-webauthn-login-verify";
import { useAuthStore } from "@/features/auth/store/use-auth-store";
import type { VerifyResult } from "@/types/api";

/**
 * @module tests/unit/features/auth/hooks/use-webauthn-login-verify
 * @description Cubre las ramas del hook de cierre de login con passkey:
 *   - silent (checklist): NO setea tokens ni redirige, ni en exito ni en error.
 *   - normal + AuthResponse con user: setTokens + redirect.
 *   - normal + 401 (clone detection): NO setea tokens (toast).
 */

const { replaceMock } = vi.hoisted(() => ({ replaceMock: vi.fn() }));
vi.mock("next/navigation", () => ({
	useRouter: () => ({ push: vi.fn(), replace: replaceMock }),
}));

const API = "https://api.test.the-full-stack.com";

function wrapper({ children }: { children: ReactNode }) {
	const client = new QueryClient({
		defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
	});
	return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

const FAKE_RESPONSE = {
	id: "cred",
	rawId: "cred",
	response: {},
	type: "public-key",
	clientExtensionResults: {},
} as unknown as AuthenticationResponseJSON;

describe("useWebauthnLoginVerify", () => {
	beforeEach(() => {
		replaceMock.mockClear();
		useAuthStore.getState().reset();
	});

	it("Given AuthResponse con user When mutate (no silent) Then setTokens + redirect", async () => {
		// Arrange: el handler default devuelve authPair() con user.
		const { result } = renderHook(() => useWebauthnLoginVerify(), { wrapper });

		// Act
		await act(async () => {
			await result.current.mutateAsync({
				challenge_id: "chal_02",
				response: FAKE_RESPONSE,
			});
		});

		// Assert: cierra el login (tokens + navegacion).
		expect(useAuthStore.getState().accessToken).not.toBe(null);
		expect(replaceMock).toHaveBeenCalledWith("/");
	});

	it("Given 401 clone detection When mutate (no silent) Then no setea tokens", async () => {
		// Arrange: sin refresh token, skipAuth=true en el client -> el 401 NO
		// dispara el mutex de refresh, propaga como ApiError 401.
		useAuthStore.setState({ refreshToken: null });
		server.use(
			http.post(`${API}/auth`, () =>
				HttpResponse.json(
					{
						error: "WEBAUTHN_CLONE_DETECTED",
						code: 4010,
						message: "Clone detectado",
					},
					{ status: 401 },
				),
			),
		);
		const { result } = renderHook(() => useWebauthnLoginVerify(), { wrapper });

		// Act
		await act(async () => {
			await result.current
				.mutateAsync({ challenge_id: "chal", response: FAKE_RESPONSE })
				.catch(() => undefined);
		});

		// Assert
		expect(useAuthStore.getState().accessToken).toBe(null);
		expect(useAuthStore.getState().user).toBe(null);
		expect(replaceMock).not.toHaveBeenCalled();
	});

	it("Given error NO-401 When mutate (no silent) Then no setea tokens (toast generico)", async () => {
		// Arrange: un 500 cae a la rama `toast.error(error.message)` (sin el if 401).
		useAuthStore.setState({ refreshToken: null });
		server.use(
			http.post(`${API}/auth`, () =>
				HttpResponse.json(
					{ error: "SERVER_ERROR", code: 5000, message: "boom" },
					{ status: 500 },
				),
			),
		);
		const { result } = renderHook(() => useWebauthnLoginVerify(), { wrapper });

		// Act
		await act(async () => {
			await result.current
				.mutateAsync({ challenge_id: "chal", response: FAKE_RESPONSE })
				.catch(() => undefined);
		});

		// Assert
		expect(useAuthStore.getState().accessToken).toBe(null);
		expect(replaceMock).not.toHaveBeenCalled();
	});

	it("Given silent When verify OK Then NO setea tokens ni redirige (checklist)", async () => {
		// Arrange: silent=true -> onSuccess hace `if (silent) return` antes de
		// tocar el store; el caller (checklist) lee el data via mutateAsync.
		const { result } = renderHook(
			() => useWebauthnLoginVerify({ silent: true }),
			{ wrapper },
		);

		// Act
		let resolved: VerifyResult | undefined;
		await act(async () => {
			const res = await result.current.mutateAsync({
				challenge_id: "chal_02",
				response: FAKE_RESPONSE,
			});
			resolved = res.data;
		});

		// Assert: el resultado llega al caller, el store queda intacto.
		expect(resolved !== undefined && "access_token" in resolved).toBe(true);
		expect(useAuthStore.getState().accessToken).toBe(null);
		expect(replaceMock).not.toHaveBeenCalled();
	});

	it("Given silent When verify falla con 401 Then NO toast (onError silenciado)", async () => {
		// Arrange: silent=true -> onError hace `if (silent) return`; el error se
		// propaga al caller (mutateAsync rechaza) pero el hook no muestra toast.
		useAuthStore.setState({ refreshToken: null });
		server.use(
			http.post(`${API}/auth`, () =>
				HttpResponse.json(
					{
						error: "WEBAUTHN_CLONE_DETECTED",
						code: 4010,
						message: "Clone detectado",
					},
					{ status: 401 },
				),
			),
		);
		const { result } = renderHook(
			() => useWebauthnLoginVerify({ silent: true }),
			{ wrapper },
		);

		// Act
		const error = await act(async () =>
			result.current
				.mutateAsync({ challenge_id: "chal", response: FAKE_RESPONSE })
				.catch((e: unknown) => e),
		);

		// Assert: el caller recibe el error; el store no cambia.
		expect(error).toBeInstanceOf(Error);
		expect(useAuthStore.getState().accessToken).toBe(null);
	});
});
