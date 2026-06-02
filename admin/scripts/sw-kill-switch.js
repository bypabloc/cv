/* eslint-disable */
/* tslint:disable */

/**
 * Kill-switch Service Worker.
 *
 * Reemplaza al `mockServiceWorker.js` de MSW en los builds donde MSW esta
 * INACTIVO (dev/stage/prod). NO sirve para mockear nada: su unico trabajo
 * es DESREGISTRARSE a si mismo y recargar los clientes.
 *
 * Por que existe: un usuario que visito el admin cuando MSW estaba activo
 * quedo con `mockServiceWorker.js` registrado en su navegador. En cada
 * navegacion el browser re-descarga ese script para chequear updates (por
 * spec del Service Worker). Si el deploy nuevo simplemente BORRA el archivo,
 * Cloudflare Pages puede seguir sirviendo el viejo (persistido de un deploy
 * anterior) -> el SW de MSW sigue vivo e intercepta las requests RSC `.txt`
 * del client navigation de Next -> el stream se corta con "Connection
 * closed" y la app se cuelga en "Verificando sesion".
 *
 * Al publicar este kill-switch en la MISMA URL (`/mockServiceWorker.js`),
 * el browser del usuario afectado descarga este script al chequear el
 * update, ejecuta el unregister + recarga, y la siguiente carga ya no tiene
 * ningun SW interceptando. Los navegadores que nunca registraron un SW no
 * descargan este archivo (no hay nada que actualizar) -> sin efecto.
 */

self.addEventListener("install", () => {
	// Activar de inmediato, sin esperar a que el SW viejo libere los clientes.
	self.skipWaiting();
});

self.addEventListener("activate", (event) => {
	event.waitUntil(
		(async () => {
			// Desregistrar esta misma registration.
			await self.registration.unregister();
			// Tomar control de los clientes abiertos y recargarlos para que
			// la pagina vuelva a cargar SIN ningun SW interceptando.
			const clients = await self.clients.matchAll({ type: "window" });
			for (const client of clients) {
				client.navigate(client.url);
			}
		})(),
	);
});

// Mientras el kill-switch este activo (entre activate y la recarga), NO
// interceptar ninguna request: passthrough total a la red. Esto evita que
// el SW toque las requests RSC `.txt` que rompian el stream.
self.addEventListener("fetch", () => {
	// Sin respondWith() -> el browser maneja la request normalmente (red).
});
