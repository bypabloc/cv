"use client";

import { NAV_ITEMS, type NavItem } from "../lib/nav-items";
import { useIsAdmin } from "./use-is-admin";

/**
 * @module features/admin-shell/hooks/use-nav-items
 * @description Resuelve los items del sidebar visibles para el usuario actual:
 *   filtra los `adminOnly` cuando el usuario NO es admin (sondeo via
 *   `useIsAdmin`). Mientras el rol no esta resuelto, los items `adminOnly` se
 *   ocultan (se asume "no admin" hasta confirmar) para no mostrar un item que
 *   luego desapareceria. Centraliza el filtro para que Sidebar y MobileSidebar
 *   compartan la misma logica.
 */

/**
 * @function useVisibleNavItems
 * @description Devuelve los `NAV_ITEMS` que el usuario actual puede ver. Los
 *   items sin `adminOnly` siempre se incluyen; los `adminOnly` solo si
 *   `useIsAdmin().isAdmin === true`.
 *
 * @returns {readonly NavItem[]} items visibles
 */
export function useVisibleNavItems(): readonly NavItem[] {
	const { isAdmin } = useIsAdmin();
	return NAV_ITEMS.filter((item) => !item.adminOnly || isAdmin);
}
