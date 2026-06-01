/**
 * @module refresh-mutex
 * @description Mutex: garantiza que solo UN `/session/refresh` este in-flight.
 *   Si N requests fallan con 401 a la vez, solo se dispara 1 refresh; los
 *   demas esperan ese resultado. Sin esto, refresh concurrentes hacen que el
 *   backend revoque la familia entera (RFC 9700 reuse detection).
 */
let inFlight: Promise<boolean> | null = null;

/**
 * @function withRefreshMutex
 * @param {() => Promise<boolean>} refreshFn - Ejecuta el refresh; true si OK
 * @returns {Promise<boolean>} El resultado del unico refresh in-flight
 */
export async function withRefreshMutex(
	refreshFn: () => Promise<boolean>,
): Promise<boolean> {
	if (inFlight) return inFlight;
	inFlight = (async () => {
		try {
			return await refreshFn();
		} finally {
			inFlight = null;
		}
	})();
	return inFlight;
}
