/**
 * @module format/number
 * @description Formateo de numeros con Intl (locale es por defecto).
 */

/**
 * @function formatNumber
 * @description Formatea un numero con separadores de miles.
 * @param {number | null | undefined} value - Numero a formatear
 * @param {string} locale - BCP 47 locale (default 'es')
 * @returns {string} Numero formateado, o '0' si value es nulo
 * @example
 *   formatNumber(12345)  // "12.345" (es) / "12,345" (en)
 */
export function formatNumber(
	value: number | null | undefined,
	locale = "es",
): string {
	if (value === null || value === undefined || Number.isNaN(value)) {
		return "0";
	}
	return new Intl.NumberFormat(locale).format(value);
}

/**
 * @function formatPercent
 * @description Formatea una fraccion (0..1) como porcentaje.
 * @param {number | null | undefined} value - Fraccion (0.42 -> "42%")
 * @param {number} fractionDigits - Decimales (default 0)
 * @param {string} locale - BCP 47 locale (default 'es')
 * @returns {string} Porcentaje formateado, o '0%' si value es nulo
 * @example
 *   formatPercent(0.4235, 1)  // "42,4 %"
 */
export function formatPercent(
	value: number | null | undefined,
	fractionDigits = 0,
	locale = "es",
): string {
	if (value === null || value === undefined || Number.isNaN(value)) {
		return "0%";
	}
	return new Intl.NumberFormat(locale, {
		style: "percent",
		minimumFractionDigits: fractionDigits,
		maximumFractionDigits: fractionDigits,
	}).format(value);
}
