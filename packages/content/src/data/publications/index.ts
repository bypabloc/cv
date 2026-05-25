/**
 * @module publications
 * @description Articulos publicados (Medium, etc).
 *   Coleccion VACIA en la base de datos actual: no hay publications todavia.
 *   Cuando se agreguen, se publicaran via la Lambda `db` (command seed) y se
 *   expondran via GET /cv?action=publications (action a agregar en `cv_service`).
 */
import type { Publication } from '../../schemas'

export const publications: readonly Publication[] = []
