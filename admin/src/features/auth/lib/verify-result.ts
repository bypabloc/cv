import type { AuthResponse, VerifyResult } from "@/types/api";

/**
 * @module features/auth/lib/verify-result
 * @description Discrimina el resultado de un verify del checklist de login.
 *   El backend devuelve UNO de dos shapes en el mismo campo `data`:
 *   - AuthResponse: el login quedo completo (trae `access_token` + a veces
 *     `mfa_complete: true`).
 *   - TempTokenResponse: faltan factores; trae un `temp_token` NUEVO (rolling)
 *     y la lista de `methods` pendientes.
 */

/**
 * @function isAuthResponse
 * @description True si el VerifyResult cierra el login (tokens). Discrimina
 *   por la presencia de `access_token` (el marcador canonico) y, como respaldo,
 *   por `mfa_complete === true`.
 */
export function isAuthResponse(data: VerifyResult): data is AuthResponse {
	return "access_token" in data && typeof data.access_token === "string";
}
