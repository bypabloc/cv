import { db, eq, sql, Languages } from "astro:db";

/**
 * Consulta que devuelve todos los idiomas del usuario, incluyendo traducciones.
 *
 * @param {string} status - Estado del usuario para filtrar.
 * @returns {Promise<object>} - Resultado de la consulta.
 */
export const getTranslations = async ({
  status,
}: {
  status?: string;
} = {}): Promise<ResponseFunction> => {
  try {
    const languageQuery = db
      .select({
        id: Languages.id,
        name: Languages.name,
        codeName: Languages.codeName,
        status: Languages.status,
      })
      .from(Languages);

    const languageResult = await languageQuery.execute();
    const languagesByCodeName = languageResult.reduce(
      (acc, language) => ({
        ...acc,
        [language.codeName]: language.name,
      }),
      {}
    );
    const codeNames = languageResult.map((language) => language.codeName);

    return {
      isValid: true,
      data: {
        languages: languageResult,
        codeNames,
        languagesByCodeName,
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
