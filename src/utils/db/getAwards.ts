import { db, eq, sql, Awards, Translations, Languages } from "astro:db";

/**
 * Consulta que devuelve todos los premios.
 *
 * @param {string} status - Estado del usuario para filtrar.
 * @param {object} user - Usuario para filtrar.
 * @returns {Promise<object>} - Resultado de la consulta de las experiencias educativas.
 */
export const getAwards = async ({
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

    let query = db
      .select({
        id: Awards.id,
        title: sql`COALESCE(
          (SELECT ${Translations.translatedValue}
           FROM ${Translations}
           WHERE ${Translations.recordId} = Awards.${Awards.id}
             AND ${Translations.tableName} = 'Awards'
             AND ${Translations.field} = 'title'
             AND ${Translations.languageId} = ${languageId}),
          ${Awards.title}) AS title`,
        summary: sql`COALESCE(
          (SELECT ${Translations.translatedValue}
            FROM ${Translations}
            WHERE ${Translations.recordId} = Awards.${Awards.id}
              AND ${Translations.tableName} = 'Awards'
              AND ${Translations.field} = 'summary'
              AND ${Translations.languageId} = ${languageId}),
          ${Awards.summary}) AS summary`,
        date: Awards.date,
        awarder: Awards.awarder,
        url: Awards.url,
      })
      .from(Awards)
      .where(eq(Awards.userId, user.id))
      .orderBy(
        sql`
          ${Awards.date} DESC
        `
      );

    if (status) {
      query = query.where(eq(Awards.status, status));
    }

    const awards = await query.execute();

    // console.log(
    //   "Premios obtenidos correctamente",
    //   JSON.stringify(awards, null, 2)
    // );

    return {
      isValid: true,
      data: {
        awards,
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
