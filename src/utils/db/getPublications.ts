import { db, eq, Publications, Publishers, sql } from "astro:db";

/**
 * Consulta que devuelve todas las publicaciones.
 *
 * @param {string} status - Estado del usuario para filtrar.
 * @param {object} user - Usuario para filtrar.
 * @returns {Promise<object>} - Resultado de la consulta.
 */
export const getPublications = async ({
  status,
  user,
}: {
  status?: string;
  user: { id: string };
}): Promise<ResponseFunction> => {
  try {
    let query = db
      .select({
        id: Publications.id,
        publisher: Publishers,
        name: Publications.name,
        releaseDate: Publications.releaseDate,
        url: Publications.url,
        summary: Publications.summary,
      })
      .from(Publications)
      .leftJoin(Publishers, eq(Publishers.id, Publications.publisherId))
      .where(eq(Publications.userId, user.id))
      .orderBy(
        sql`
        ${Publications.releaseDate} DESC
      `
      );

    if (status) {
      query = query.where(eq(Publications.status, status));
    }

    const publications = await query.execute();

    // console.log(
    //   "Publicaciones obtenidas correctamente",
    //   JSON.stringify(publications, null, 2)
    // );

    return {
      isValid: true,
      data: {
        publications,
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
