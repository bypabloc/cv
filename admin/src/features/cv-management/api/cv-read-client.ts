import { env } from "@/lib/env";
import { SECTION_CONFIG } from "../lib/sections";
import type { CvSection } from "../types";

/**
 * @module features/cv-management/api/cv-read-client
 * @description Lectura del GET /cv PUBLICO (sin Bearer, fuera de apiFetch):
 *   `${API}/cv?operation=cv&action=<accion>[&niche=<n>]`. La respuesta llega
 *   FLAT (el array/objeto de la seccion al nivel raiz) con los datos BiLang
 *   completos. La seccion `publications` no tiene action de lectura publica:
 *   resuelve a lista vacia sin tocar la red.
 */

export class CvReadError extends Error {
	constructor(
		public readonly status: number,
		message: string,
	) {
		super(message);
		this.name = "CvReadError";
	}
}

interface FetchCvSectionOptions {
	niche?: string;
}

/**
 * @function fetchCvSection
 * @description Trae una seccion del CV publico tipada por el caller. Lanza
 *   `CvReadError` con el HTTP status si el backend responde !ok.
 */
export async function fetchCvSection<T>(
	section: CvSection,
	options: FetchCvSectionOptions = {},
): Promise<T> {
	const action = SECTION_CONFIG[section].readAction;
	if (action === null) {
		// publications: sin lectura publica -> lista vacia estable.
		return [] as unknown as T;
	}
	const params = new URLSearchParams({ operation: "cv", action });
	if (options.niche) params.set("niche", options.niche);
	const response = await fetch(
		`${env.NEXT_PUBLIC_API_ENDPOINT}/cv?${params.toString()}`,
	);
	if (!response.ok) {
		throw new CvReadError(
			response.status,
			`GET /cv action=${action} fallo con HTTP ${response.status}`,
		);
	}
	return (await response.json()) as T;
}

export const cvReadClient = {
	getSection: fetchCvSection,
};
