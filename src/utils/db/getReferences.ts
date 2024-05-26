import {
  db,
  eq,
  sql,
  References,
  Employers,
  Translations,
  Languages,
} from "astro:db";

/**
 * Consulta que devuelve todas las referencias del usuario, incluyendo traducciones.
 *
 * @param {string} status - Estado del usuario para filtrar.
 * @param {object} user - Usuario para filtrar.
 * @param {string} [languageCode="es"] - Código del idioma para las traducciones.
 * @returns {Promise<object>} - Resultado de la consulta.
 */
export const getReferences = async ({
  status,
  user,
  languageCode = "es",
}: {
  status?: string;
  user: { id: string };
  languageCode?: string;
}): Promise<ResponseFunction> => {
  try {
    // Obtener el ID del idioma correspondiente al código de idioma
    const languageQuery = db
      .select({ id: Languages.id })
      .from(Languages)
      .where(eq(Languages.codeName, languageCode));

    const languageResult = await languageQuery.execute();
    const languageId = languageResult[0]?.id;

    if (!languageId) {
      return {
        isValid: false,
        error: `Language code ${languageCode} not found`,
      };
    }

    // Consulta para obtener las referencias del usuario incluyendo traducciones
    let query = db
      .select({
        id: References.id,
        employers: Employers,
        name: sql`COALESCE(
          (SELECT ${Translations.translatedValue}
           FROM ${Translations}
           WHERE ${Translations.recordId} = ${References.id}
             AND ${Translations.tableName} = 'References'
             AND ${Translations.field} = 'name'
             AND ${Translations.languageId} = ${languageId}),
          ${References.name}) AS name`,
        reference: sql`COALESCE(
          (SELECT ${Translations.translatedValue}
           FROM ${Translations}
           WHERE ${Translations.recordId} = ${References.id}
             AND ${Translations.tableName} = 'References'
             AND ${Translations.field} = 'reference'
             AND ${Translations.languageId} = ${languageId}),
          ${References.reference}) AS reference`,
        position: sql`COALESCE(
          (SELECT ${Translations.translatedValue}
           FROM ${Translations}
           WHERE ${Translations.recordId} = ${References.id}
             AND ${Translations.tableName} = 'References'
             AND ${Translations.field} = 'position'
             AND ${Translations.languageId} = ${languageId}),
          ${References.position}) AS position`,
        url: References.url,
        scrappingRecommendation: References.scrappingRecommendation,
      })
      .from(References)
      .leftJoin(Employers, eq(Employers.id, References.employerId))
      .where(eq(References.userId, user.id));

    if (status) {
      query = query.where(eq(References.status, status));
    }

    const references = await query.execute();

    return {
      isValid: true,
      data: {
        references,
      },
    };
  } catch (error) {
    console.error("Error al obtener las referencias:", error);
    return {
      isValid: false,
      error: "Error al obtener las referencias",
    };
  }
};
