import { z } from "zod";

/**
 * @config env.ts
 * @description Valida las NEXT_PUBLIC_* en cold start (fail-fast en build).
 *   Importar `env` desde el resto del codigo; NUNCA usar process.env directo.
 */
const envSchema = z.object({
	NEXT_PUBLIC_API_ENDPOINT: z
		.string()
		.url()
		.describe("Lambda backend base URL"),
	NEXT_PUBLIC_TURNSTILE_SITEKEY: z
		.string()
		.min(10)
		.describe("Cloudflare Turnstile sitekey (publico)"),
	NEXT_PUBLIC_ADMIN_URL: z
		.string()
		.url()
		.describe("Self URL del admin, para callbacks"),
	NEXT_PUBLIC_AUTH_REFRESH_LEAD_MS: z.coerce
		.number()
		.int()
		.min(5_000)
		.max(300_000)
		.default(30_000)
		.describe("Cuanto antes del exp del JWT disparar el refresh proactivo"),
	NEXT_PUBLIC_WEBAUTHN_RP_ID: z
		.string()
		.min(1)
		.describe("RP ID de WebAuthn (hostname del admin por env)"),
	NEXT_PUBLIC_FEATURE_MFA: z
		.enum(["true", "false"])
		.default("true")
		.describe("Toggle opcional de UI para la seccion MFA"),
	NEXT_PUBLIC_E2E_BYPASS: z
		.enum(["true", "false"])
		.default("false")
		.describe(
			"SOLO E2E: cuando 'true', el form NO renderiza el Turnstile real " +
				"(auto-emite un token dummy) y apiFetch manda el bypass token " +
				"Ed25519 firmado (window.__E2E_BYPASS_TOKEN__) en el header " +
				"X-Turnstile-Bypass-Token. El backend dev acepta el bypass " +
				"con cf_turnstile_response vacio; prod lo rechaza SIEMPRE. NUNCA " +
				"setear 'true' en builds de produccion.",
		),
});

export const env = envSchema.parse({
	NEXT_PUBLIC_API_ENDPOINT: process.env.NEXT_PUBLIC_API_ENDPOINT,
	NEXT_PUBLIC_TURNSTILE_SITEKEY: process.env.NEXT_PUBLIC_TURNSTILE_SITEKEY,
	NEXT_PUBLIC_ADMIN_URL: process.env.NEXT_PUBLIC_ADMIN_URL,
	NEXT_PUBLIC_AUTH_REFRESH_LEAD_MS:
		process.env.NEXT_PUBLIC_AUTH_REFRESH_LEAD_MS,
	NEXT_PUBLIC_WEBAUTHN_RP_ID: process.env.NEXT_PUBLIC_WEBAUTHN_RP_ID,
	NEXT_PUBLIC_FEATURE_MFA: process.env.NEXT_PUBLIC_FEATURE_MFA,
	NEXT_PUBLIC_E2E_BYPASS: process.env.NEXT_PUBLIC_E2E_BYPASS,
});

export type Env = z.infer<typeof envSchema>;
