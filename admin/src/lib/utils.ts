import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * @function cn
 * @description Combina clases condicionales (clsx) + resuelve conflictos
 *   de Tailwind (tailwind-merge). Helper canonico de shadcn.
 *
 * @param {ClassValue[]} inputs - Clases a combinar
 * @returns {string} String de clases final, sin conflictos Tailwind
 *
 * @example
 *   cn('px-2', condition && 'px-4')  // "px-4" si condition
 */
export function cn(...inputs: ClassValue[]): string {
	return twMerge(clsx(inputs));
}
