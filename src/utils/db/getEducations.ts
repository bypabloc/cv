import {
  db,
  eq,
  sql,
  Educations,
  Institutions,
  Translations,
  Languages,
} from "astro:db";

/**
 * Consulta que devuelve todas las experiencias educativas de un usuario,
 * incluyendo las traducciones correspondientes.
 *
 * @param {string} status - Estado del usuario para filtrar.
 * @param {object} user - Usuario para filtrar.
 * @param {string} [languageCode="es"] - Código del idioma para las traducciones.
 * @returns {Promise<object>} - Resultado de la consulta de las experiencias educativas.
 */
export const getEducations = async ({
  status,
  user,
  languageCode = "en",
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

    console.log("languageCode", languageCode);
    console.log("Idioma obtenido correctamente", languageId);

    // Consulta principal incluyendo las traducciones
    let query = db
      .select({
        id: Educations.id,
        institution: Institutions,
        area: sql`COALESCE(
          (SELECT ${Translations.translatedValue}
           FROM ${Translations}
           WHERE ${Translations.recordId} = ${Educations.id}
             AND ${Translations.tableName} = 'Educations'
             AND ${Translations.field} = 'area'
             AND ${Translations.languageId} = ${languageId}),
          ${Educations.area}) AS area`,
        learn: sql`COALESCE(
          (SELECT ${Translations.translatedValue}
           FROM ${Translations}
           WHERE ${Translations.recordId} = ${Educations.id}
             AND ${Translations.tableName} = 'Educations'
             AND ${Translations.field} = 'learn'
             AND ${Translations.languageId} = ${languageId}),
          ${Educations.learn}) AS learn`,
        studyType: sql`COALESCE(
          (SELECT ${Translations.translatedValue}
           FROM ${Translations}
           WHERE ${Translations.recordId} = ${Educations.id}
             AND ${Translations.tableName} = 'Educations'
             AND ${Translations.field} = 'studyType'
             AND ${Translations.languageId} = ${languageId}),
          ${Educations.studyType}) AS studyType`,
        startDate: Educations.startDate,
        endDate: Educations.endDate,
      })
      .from(Educations)
      .leftJoin(Institutions, eq(Institutions.id, Educations.institutionId))
      .where(eq(Educations.userId, user.id))
      .orderBy(
        sql`
          CASE
            WHEN ${Educations.endDate} IS NULL THEN 0
            ELSE 1
          END,
          ${Educations.endDate} DESC NULLS FIRST,
          ${Educations.startDate} DESC
        `
      );

    const queryToSql = query.toSQL();
    console.log("getEducations > queryToSql", queryToSql);

    if (status) {
      query = query.where(eq(Educations.status, status));
    }

    const educations = await query.execute();

    if (!educations.length) {
      console.error("Experiencias educativas no encontradas");
      return {
        isValid: false,
        error: "Experiencias educativas no encontradas",
      };
    }

    return {
      isValid: true,
      data: {
        educations,
      },
    };
  } catch (error) {
    console.error("Error al obtener las experiencias educativas:", error);
    return {
      isValid: false,
      error: "Error al obtener las experiencias educativas",
    };
  }
};
