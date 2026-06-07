import { describe, expect, it } from "vitest";
import { authClient } from "@/features/auth/api/auth-client";

/**
 * @module tests/unit/features/auth/api/auth-client-enable-required
 * @description Cubre las 5 actions soft-enable / set-required del cliente auth
 *   (mfa.enable, mfa.set-required, webauthn.enable, webauthn.disable,
 *   webauthn.set-required) contra el MSW handler. Cada una hace POST /auth con
 *   su `{operation, action}` y devuelve el envelope. No tenian cobertura.
 */

describe("authClient enable / set-required actions", () => {
	it("Given mfaEnable When llamado Then resuelve el envelope (is_valid)", async () => {
		// Act
		const res = await authClient.mfaEnable({ kind: "totp" });

		// Assert
		expect(res.is_valid).toBe(true);
	});

	it("Given mfaSetRequired When llamado Then resuelve el envelope", async () => {
		// Act
		const res = await authClient.mfaSetRequired({
			kind: "totp",
			required: true,
		});

		// Assert
		expect(res.is_valid).toBe(true);
	});

	it("Given webauthnEnable When llamado Then resuelve el envelope", async () => {
		// Act
		const res = await authClient.webauthnEnable({ credential_id: "cred-1" });

		// Assert
		expect(res.is_valid).toBe(true);
	});

	it("Given webauthnDisable When llamado Then resuelve el envelope", async () => {
		// Act
		const res = await authClient.webauthnDisable({ credential_id: "cred-1" });

		// Assert
		expect(res.is_valid).toBe(true);
	});

	it("Given webauthnSetRequired When llamado Then resuelve el envelope", async () => {
		// Act
		const res = await authClient.webauthnSetRequired({
			credential_id: "cred-1",
			required: false,
		});

		// Assert
		expect(res.is_valid).toBe(true);
	});
});
