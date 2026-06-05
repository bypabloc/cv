import { describe, expect, it } from "vitest";
import { isAuthResponse } from "@/features/auth/lib/verify-result";
import type { AuthResponse, TempTokenResponse } from "@/types/api";

/**
 * @module tests/unit/features/auth/lib/verify-result
 * @description Verifica el discriminador isAuthResponse: true cuando el
 *   VerifyResult cierra el login (trae `access_token`), false cuando es un
 *   TempTokenResponse rolling (trae `temp_token` + `methods` pendientes).
 */

describe("isAuthResponse", () => {
	it("Given un AuthResponse con access_token When se discrimina Then true", () => {
		// Arrange
		const data: AuthResponse = {
			access_token: "acc-123",
			refresh_token: "ref-123",
			expires_in: 900,
			mfa_complete: true,
		};

		// Act
		const result = isAuthResponse(data);

		// Assert
		expect(result).toBe(true);
	});

	it("Given un TempTokenResponse con methods pendientes When se discrimina Then false", () => {
		// Arrange
		const data: TempTokenResponse = {
			temp_token: "tmp-next",
			step: 2,
			mfa_complete: false,
			methods: ["totp"],
		};

		// Act
		const result = isAuthResponse(data);

		// Assert
		expect(result).toBe(false);
	});

	it("Given un objeto sin access_token (solo temp) When se discrimina Then false", () => {
		// Arrange: respaldo del shape minimo del temp.
		const data: TempTokenResponse = { temp_token: "only-temp" };

		// Act
		const result = isAuthResponse(data);

		// Assert
		expect(result).toBe(false);
	});

	it("Given access_token no string When se discrimina Then false (typeof guard)", () => {
		// Arrange: el guard exige typeof string, no solo la presencia de la key.
		const data = { access_token: 123 } as unknown as TempTokenResponse;

		// Act
		const result = isAuthResponse(data);

		// Assert
		expect(result).toBe(false);
	});
});
