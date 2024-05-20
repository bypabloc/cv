import { db, eq, Languages, LanguagesUsers, sql } from "astro:db";

/**
 * Consulta que devuelve todos los idiomas del usuario.
 *
 * @param {string} status - Estado del usuario para filtrar.
 * @param {object} user - Usuario para filtrar.
 * @returns {Promise<object>} - Resultado de la consulta.
 */
export const getLanguages = async ({
  status,
  user,
}: {
  status?: string;
  user: { id: string };
}): Promise<ResponseFunction> => {
  try {
    let query = db
      .select({
        id: LanguagesUsers.id,
        language: Languages,
        status: LanguagesUsers.status,
        fluency: LanguagesUsers.fluency,
      })
      .from(LanguagesUsers)
      .leftJoin(Languages, eq(Languages.id, LanguagesUsers.languageId))
      .where(eq(LanguagesUsers.userId, user.id));

    if (status) {
      query = query.where(eq(LanguagesUsers.status, status));
    }

    const languages = await query.execute();

    // console.log(
    //   "Certificados obtenidos correctamente",
    //   JSON.stringify(languages, null, 2)
    // );

    return {
      isValid: true,
      data: {
        languages,
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
