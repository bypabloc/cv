import { z } from "zod";

/**
 * @module validation/auth
 * @description Zod schemas de los forms de auth. Reglas alineadas con el
 *   backend (password min 12, code 8 chars Crockford, TOTP 6 digitos,
 *   recovery 10 chars Crockford).
 */

const CROCKFORD = /^[0-9A-HJ-NP-Z]+$/;

export const emailSchema = z
	.string()
	.min(1, "El email es obligatorio")
	.email("Email invalido");

export const loginSchema = z.object({
	email: emailSchema,
	password: z.string().optional(),
});
export type LoginInput = z.infer<typeof loginSchema>;

export const registerSchema = z.object({
	email: emailSchema,
});
export type RegisterInput = z.infer<typeof registerSchema>;

export const verifyCodeSchema = z.object({
	code: z
		.string()
		.length(8, "El codigo tiene 8 caracteres")
		.regex(CROCKFORD, "Codigo invalido"),
});
export type VerifyCodeInput = z.infer<typeof verifyCodeSchema>;

export const passwordSchema = z
	.string()
	.min(12, "La contrasena debe tener al menos 12 caracteres")
	.max(256, "La contrasena es demasiado larga");

export const loginPasswordSchema = z.object({
	password: passwordSchema,
});
export type LoginPasswordInput = z.infer<typeof loginPasswordSchema>;

export const setPasswordSchema = z
	.object({
		password: passwordSchema,
		confirm: z.string(),
	})
	.refine((d) => d.password === d.confirm, {
		message: "Las contrasenas no coinciden",
		path: ["confirm"],
	});
export type SetPasswordInput = z.infer<typeof setPasswordSchema>;

export const totpCodeSchema = z.object({
	code: z
		.string()
		.length(6, "El codigo TOTP tiene 6 digitos")
		.regex(/^\d{6}$/, "Solo digitos"),
});
export type TotpCodeInput = z.infer<typeof totpCodeSchema>;

export const recoveryCodeSchema = z.object({
	code: z
		.string()
		.length(10, "El codigo de recuperacion tiene 10 caracteres")
		.regex(CROCKFORD, "Codigo invalido"),
});
export type RecoveryCodeInput = z.infer<typeof recoveryCodeSchema>;
