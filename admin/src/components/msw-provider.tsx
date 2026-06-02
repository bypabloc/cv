"use client";

import { type ReactNode, useEffect, useState } from "react";

/**
 * @component MswProvider
 * @description Arranca el worker MSW en el browser cuando
 *   `NEXT_PUBLIC_USE_MSW === 'true'`. En cualquier otro caso es passthrough
 *   inmediato. Bloquea el render hasta que el worker este listo SOLO si MSW
 *   esta activo (evita requests sin mock en el arranque).
 *
 * @props {ReactNode} children - Arbol de la app
 */
export function MswProvider({ children }: { children: ReactNode }) {
	const useMsw = process.env.NEXT_PUBLIC_USE_MSW === "true";
	const [ready, setReady] = useState(!useMsw);

	useEffect(() => {
		if (typeof window === "undefined") return;

		// MSW INACTIVO (dev/stage/prod): des-registrar cualquier
		// mockServiceWorker.js que haya quedado registrado en una visita
		// previa. Si no, el SW huerfano intercepta requests y cierra el
		// canal postMessage -> "Connection closed" + la app se cuelga.
		if (!useMsw) {
			void navigator.serviceWorker?.getRegistrations?.().then((regs) => {
				for (const reg of regs) {
					if (reg.active?.scriptURL.includes("mockServiceWorker")) {
						void reg.unregister();
					}
				}
			});
			return;
		}

		let active = true;
		void (async () => {
			const { worker } = await import("@tests/mocks/browser");
			await worker.start({ onUnhandledRequest: "bypass" });
			if (active) setReady(true);
		})();
		return () => {
			active = false;
		};
	}, [useMsw]);

	if (!ready) return null;
	return <>{children}</>;
}
