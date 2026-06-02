/**
 * @file postbuild.mjs
 * @description Postbuild del admin export (`next build` con output:'export').
 *
 * MSW NUNCA esta activo en un build de export (dev/stage/prod): el
 * `mockServiceWorker.js` real solo se usa en los unit tests con
 * `NEXT_PUBLIC_USE_MSW=true`, que corren con Vitest, no con `next build`.
 *
 * Si el build deja el `mockServiceWorker.js` de MSW en `out/`, los
 * navegadores que lo registraron en una visita previa lo seguirian usando
 * (intercepta las requests RSC `.txt` -> "Connection closed"). Por eso se
 * REEMPLAZA por el kill-switch SW (scripts/sw-kill-switch.js), que se
 * auto-desregistra y recarga al usuario afectado. Publicar el kill-switch
 * en la MISMA URL es lo que mata el SW huerfano; borrar el archivo no basta
 * (Cloudflare Pages puede seguir sirviendo el viejo de un deploy anterior).
 */
import { copyFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const killSwitch = join(here, "sw-kill-switch.js");
const target = join(here, "..", "out", "mockServiceWorker.js");

copyFileSync(killSwitch, target);
console.info(`[postbuild] kill-switch SW -> ${target}`);
