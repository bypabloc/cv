import { db, eq, Educations, Institutions, sql } from "astro:db";

/**
 * Consulta que devuelve todas las experiencias educativas de un usuario.
 *
 * @param {string} status - Estado del usuario para filtrar.
 * @param {object} user - Usuario para filtrar.
 * @returns {Promise<object>} - Resultado de la consulta de las experiencias educativas.
 */
export const getEducations = async ({
  status,
  user,
}: {
  status?: string;
  user: { id: string };
}): Promise<ResponseFunction> => {
  try {
    let query = db
      .select({
        id: Educations.id,
        institution: Institutions,
        area: Educations.area,
        learn: Educations.learn,
        studyType: Educations.studyType,
        startDate: Educations.startDate,
        endDate: Educations.endDate,
      })
      .from(Educations)
      .where(eq(Educations.userId, user.id))
      .leftJoin(Institutions, eq(Institutions.id, Educations.institutionId))
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

    if (status) {
      query = query.where(eq(Educations.status, status));
    }

    const educations = await query.execute();

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
