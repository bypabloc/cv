import type { RegistrationResponseJSON } from "@simplewebauthn/browser";
import { act, renderHook, waitFor } from "@testing-library/react";
import { makeHookWrapper } from "@tests/utils/hook-wrapper";
import { describe, expect, it, vi } from "vitest";
import { authKeys } from "@/features/auth/api/query-keys";
import { useConfirmTotp } from "@/features/auth/hooks/use-confirm-totp";
import { useDeleteCredential } from "@/features/auth/hooks/use-delete-credential";
import { useGenerateRecoveryCodes } from "@/features/auth/hooks/use-generate-recovery-codes";
import { useListCredentials } from "@/features/auth/hooks/use-list-credentials";
import { useMfaList } from "@/features/auth/hooks/use-mfa-list";
import { useSetPreferredMfa } from "@/features/auth/hooks/use-set-preferred-mfa";
import { useSetupEmailCode } from "@/features/auth/hooks/use-setup-email-code";
import { useSetupTotp } from "@/features/auth/hooks/use-setup-totp";
import { useWebauthnLoginOptions } from "@/features/auth/hooks/use-webauthn-login-options";
import { useWebauthnRegisterOptions } from "@/features/auth/hooks/use-webauthn-register-options";
import { useWebauthnRegisterVerify } from "@/features/auth/hooks/use-webauthn-register-verify";

/**
 * @module tests/unit/features/auth/hooks/mfa-webauthn
 * @description Happy paths + invalidaciones de los hooks de gestion MFA/WebAuthn.
 */

const FAKE_REG = {
	id: "cred",
	rawId: "cred",
	response: {},
	type: "public-key",
	clientExtensionResults: {},
} as unknown as RegistrationResponseJSON;

describe("useMfaList", () => {
	it("Given la query When se monta Then devuelve el MfaListResponse", async () => {
		const { wrapper } = makeHookWrapper();
		const { result } = renderHook(() => useMfaList(), { wrapper });
		await waitFor(() => expect(result.current.isSuccess).toBe(true));
		expect(result.current.data?.total_mfa).toBe(2);
	});
});

describe("useListCredentials", () => {
	it("Given la query When se monta Then devuelve el array de credentials", async () => {
		const { wrapper } = makeHookWrapper();
		const { result } = renderHook(() => useListCredentials(), { wrapper });
		await waitFor(() => expect(result.current.isSuccess).toBe(true));
		expect(result.current.data?.[0]?.id).toBe("cred_01");
	});
});

describe("useSetupTotp", () => {
	it("Given mutate When se ejecuta Then devuelve secret_b32 + otpauth_url", async () => {
		const { wrapper } = makeHookWrapper();
		const { result } = renderHook(() => useSetupTotp(), { wrapper });
		const res = await act(async () => result.current.mutateAsync());
		expect(res.data.secret_b32).toBe("JBSWY3DPEHPK3PXP");
	});
});

describe("useConfirmTotp", () => {
	it("Given confirm OK When mutate Then invalida authKeys.mfa()", async () => {
		const { client, wrapper } = makeHookWrapper();
		const spy = vi.spyOn(client, "invalidateQueries");
		const { result } = renderHook(() => useConfirmTotp(), { wrapper });

		await act(async () => {
			await result.current.mutateAsync({ code: "123456" });
		});

		expect(spy).toHaveBeenCalledWith({ queryKey: authKeys.mfa() });
	});
});

describe("useSetupEmailCode", () => {
	it("Given mutate When se ejecuta Then devuelve MfaListResponse", async () => {
		const { wrapper } = makeHookWrapper();
		const { result } = renderHook(() => useSetupEmailCode(), { wrapper });
		const res = await act(async () => result.current.mutateAsync());
		expect(res.data.total_mfa).toBe(1);
	});
});

describe("useSetPreferredMfa", () => {
	it("Given mutate When se ejecuta Then devuelve MfaListResponse", async () => {
		const { wrapper } = makeHookWrapper();
		const { result } = renderHook(() => useSetPreferredMfa(), { wrapper });
		const res = await act(async () =>
			result.current.mutateAsync({ kind: "totp" }),
		);
		expect(res.data.methods[0]?.is_preferred).toBe(true);
	});
});

describe("useGenerateRecoveryCodes", () => {
	it("Given mutate When se ejecuta Then devuelve 10 codes", async () => {
		const { wrapper } = makeHookWrapper();
		const { result } = renderHook(() => useGenerateRecoveryCodes(), {
			wrapper,
		});
		const res = await act(async () => result.current.mutateAsync());
		expect(res.data.codes).toHaveLength(10);
	});
});

describe("useWebauthnRegisterOptions", () => {
	it("Given mutate When se ejecuta Then devuelve challenge_id + options", async () => {
		const { wrapper } = makeHookWrapper();
		const { result } = renderHook(() => useWebauthnRegisterOptions(), {
			wrapper,
		});
		const res = await act(async () => result.current.mutateAsync());
		expect(res.data.challenge_id).toBe("chal_01");
	});
});

describe("useWebauthnRegisterVerify", () => {
	it("Given verify OK When mutate Then invalida webauthn() + mfa()", async () => {
		const { client, wrapper } = makeHookWrapper();
		const spy = vi.spyOn(client, "invalidateQueries");
		const { result } = renderHook(() => useWebauthnRegisterVerify(), {
			wrapper,
		});

		await act(async () => {
			await result.current.mutateAsync({
				challenge_id: "chal_01",
				response: FAKE_REG,
			});
		});

		expect(spy).toHaveBeenCalledWith({ queryKey: authKeys.webauthn() });
		expect(spy).toHaveBeenCalledWith({ queryKey: authKeys.mfa() });
	});
});

describe("useWebauthnLoginOptions", () => {
	it("Given mutate When se ejecuta Then devuelve challenge_id + options", async () => {
		const { wrapper } = makeHookWrapper();
		const { result } = renderHook(() => useWebauthnLoginOptions(), { wrapper });
		const res = await act(async () =>
			result.current.mutateAsync({ email: "user@test.com" }),
		);
		expect(res.data.challenge_id).toBe("chal_02");
	});
});

describe("useDeleteCredential", () => {
	it("Given delete OK When mutate Then invalida webauthn()", async () => {
		const { client, wrapper } = makeHookWrapper();
		const spy = vi.spyOn(client, "invalidateQueries");
		const { result } = renderHook(() => useDeleteCredential(), { wrapper });

		await act(async () => {
			await result.current.mutateAsync({ credential_id: "cred_01" });
		});

		expect(spy).toHaveBeenCalledWith({ queryKey: authKeys.webauthn() });
	});
});
