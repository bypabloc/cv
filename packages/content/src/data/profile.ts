/**
 * @module profile
 * @description Profile singleton de Pablo Contreras.
 *   Origen: cache JSON generado por `scripts/fetch-cv-cache.mjs`
 *   (API GET /cv?action=profile).
 *
 * Para modificar el profile: hacerlo en la DB (Lambda db, command seed)
 * y regenerar el cache JSON. NO editar el cache a mano.
 */
import raw from '../data-cache/profile.json'
import { type Profile, ProfileSchema } from '../schemas'

export const profile: Profile = ProfileSchema.parse(raw)
