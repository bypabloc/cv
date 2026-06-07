"use client";

import { useEffect, useState } from "react";

/**
 * @function useMounted
 * @description true tras el primer mount en cliente. Para evitar hydration
 *   mismatch en componentes theme-aware o dependientes de window.
 * @returns {boolean} si el componente ya monto en cliente
 */
export function useMounted(): boolean {
	const [mounted, setMounted] = useState(false);
	useEffect(() => setMounted(true), []);
	return mounted;
}
