/**
 * @module lib/metrics-query-keys
 * @description Namespace raiz de las query keys de TODAS las features de
 *   metricas (`['metrics', <feature>, <action>, params]`). Cada feature
 *   deriva su factory de aqui para que la invalidacion coordinada y la
 *   exclusion del persister (data con PII) funcionen por prefijo.
 *
 *   El persister NO persiste queries cuyo `queryKey[0] === 'metrics'` y la
 *   feature es de PII (`contacts`, `sessions`): ver query-provider. El resto
 *   (agregadas) si se persiste (24h) para una UX rapida al recargar.
 */

/** Prefijo raiz de todas las queries de metricas. */
export const METRICS_KEY = "metrics" as const;

/**
 * @function metricsKey
 * @description Construye una query key bajo el namespace `metrics`:
 *   `['metrics', feature, action, params?]`.
 *
 * @param feature - dominio (`analytics`, `events`, `sessions`, ...)
 * @param action - accion (`overview`, `list`, `by-country`, ...)
 * @param params - params de la query (range, paginacion, filtros)
 */
export function metricsKey<P extends object>(
	feature: string,
	action: string,
	params?: P,
): readonly unknown[] {
	return params === undefined
		? [METRICS_KEY, feature, action]
		: [METRICS_KEY, feature, action, params];
}

/** Features de metricas con PII: no se persisten en el query persister. */
export const METRICS_PII_FEATURES: readonly string[] = ["contacts", "sessions"];
