import { describe, expect, it } from "vitest";
import {
	changePasswordSchema,
	setPasswordSchema,
} from "@/features/settings/validation";

/**
 * @module tests/unit/features/settings/validation
 * @description Verifica los refines de confirmacion de contrasena: tanto el
 *   cambio (con current) como el set inicial exigen new_password == confirm.
 */

describe("setPasswordSchema", () => {
	it("Given confirm distinto When se valida Then falla con Las contrasenas no coinciden", () => {
		// Arrange + Act
		const result = setPasswordSchema.safeParse({
			new_password: "una-clave-larga-123",
			confirm: "otra-clave-larga-123",
		});

		// Assert
		expect(result.success).toBe(false);
		expect(result.success ? "" : result.error.issues[0]?.message).toBe(
			"Las contrasenas no coinciden",
		);
	});

	it("Given confirm igual When se valida Then pasa", () => {
		// Arrange + Act + Assert
		expect(
			setPasswordSchema.safeParse({
				new_password: "una-clave-larga-123",
				confirm: "una-clave-larga-123",
			}).success,
		).toBe(true);
	});
});

describe("changePasswordSchema", () => {
	it("Given confirm distinto When se valida Then falla en el path confirm", () => {
		// Arrange + Act
		const result = changePasswordSchema.safeParse({
			current_password: "la-actual-123",
			new_password: "una-clave-larga-123",
			confirm: "no-coincide-123",
		});

		// Assert
		expect(result.success).toBe(false);
		const issue = result.success ? undefined : result.error.issues[0];
		expect(issue?.path).toEqual(["confirm"]);
		expect(issue?.message).toBe("Las contrasenas no coinciden");
	});
});
