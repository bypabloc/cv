import { z } from "zod";
import { emailSchema, passwordSchema } from "@/lib/validation/auth";

/**
 * @module features/settings/validation
 * @description Zod schemas de los forms de settings. Reusa `emailSchema` y
 *   `passwordSchema` (min 12) del feature auth.
 */

export const profileSchema = z.object({
	display_name: z
		.string()
		.min(1, "El nombre es obligatorio")
		.max(120, "El nombre es demasiado largo"),
});
export type ProfileInput = z.infer<typeof profileSchema>;

export const changeEmailSchema = z.object({
	new_email: emailSchema,
});
export type ChangeEmailInput = z.infer<typeof changeEmailSchema>;

export const confirmEmailChangeSchema = z.object({
	token: z.string().min(1, "El token es obligatorio"),
});
export type ConfirmEmailChangeInput = z.infer<typeof confirmEmailChangeSchema>;

export const changePasswordSchema = z
	.object({
		current_password: z.string().min(1, "La contrasena actual es obligatoria"),
		new_password: passwordSchema,
		confirm: z.string(),
	})
	.refine((d) => d.new_password === d.confirm, {
		message: "Las contrasenas no coinciden",
		path: ["confirm"],
	});
export type ChangePasswordInput = z.infer<typeof changePasswordSchema>;
