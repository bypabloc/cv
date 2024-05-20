import { db, eq, Awards, sql } from "astro:db";

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
}: {
  status?: string;
  user: { id: string };
}): Promise<ResponseFunction> => {
  try {
    let query = db.select().from(Awards).where(eq(Awards.userId, user.id));

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
