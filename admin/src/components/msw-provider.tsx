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
		// previa. Si no, el SW huerfano intercepta las requests RSC `.txt`
		// del client navigation de Next y corta el stream -> "Connection
		// closed" + la app se cuelga en "Verificando sesion". Tras
		// desregistrar hay que RECARGAR: el SW sigue controlando esta carga
		// hasta el proximo navigate, asi que sin reload el usuario queda
		// colgado en la pagina rota. El kill-switch SW del deploy
		// (scripts/sw-kill-switch.js) cubre el mismo caso desde el server;
		// este es el cinturon de seguridad del lado cliente.
		if (!useMsw) {
			void navigator.serviceWorker?.getRegistrations?.().then((regs) => {
				let killed = false;
				for (const reg of regs) {
					const url =
						reg.active?.scriptURL ??
						reg.waiting?.scriptURL ??
						reg.installing?.scriptURL ??
						"";
					if (url.includes("mockServiceWorker")) {
						killed = true;
						void reg.unregister();
					}
				}
				if (killed) window.location.reload();
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
