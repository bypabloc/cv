import { db, eq, sql, Languages, LanguagesUsers, Translations } from "astro:db";

/**
 * Consulta que devuelve todos los idiomas del usuario, incluyendo traducciones.
 *
 * @param {string} status - Estado del usuario para filtrar.
 * @param {object} user - Usuario para filtrar.
 * @param {string} [languageCode="es"] - Código del idioma para las traducciones.
 * @returns {Promise<object>} - Resultado de la consulta.
 */
export const getLanguages = async ({
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

    // Consulta para obtener los idiomas del usuario incluyendo traducciones
    let query = db
      .select({
        id: LanguagesUsers.id,
        language: Languages,
        status: LanguagesUsers.status,
        fluency: sql`COALESCE(
          (
            SELECT ${Translations.translatedValue}
            FROM ${Translations}
            WHERE ${Translations.recordId} = ${LanguagesUsers.id}
              AND ${Translations.tableName} = 'LanguagesUsers'
              AND ${Translations.field} = 'fluency'
              AND ${Translations.languageId} = ${languageId}
          ),
          ${LanguagesUsers.fluency}) AS fluency`,
      })
      .from(LanguagesUsers)
      .leftJoin(Languages, eq(Languages.id, LanguagesUsers.languageId))
      .where(eq(LanguagesUsers.userId, user.id));

    if (status) {
      query = query.where(eq(LanguagesUsers.status, status));
    }

    const languages = await query.execute();

    return {
      isValid: true,
      data: {
        languages,
      },
    };
  } catch (error) {
    console.error("Error al obtener los idiomas:", error);
    return {
      isValid: false,
      error: "Error al obtener los idiomas",
    };
  }
};
