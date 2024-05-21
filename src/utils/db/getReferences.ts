import { db, eq, References, Employers, sql } from "astro:db";

/**
 * Consulta que devuelve todos los intereses del usuario.
 *
 * @param {string} status - Estado del usuario para filtrar.
 * @param {object} user - Usuario para filtrar.
 * @returns {Promise<object>} - Resultado de la consulta.
 */
export const getReferences = async ({
  status,
  user,
}: {
  status?: string;
  user: { id: string };
}): Promise<ResponseFunction> => {
  try {
    let query = db
      .select({
        id: References.id,
        employers: Employers,
        name: References.name,
        reference: References.reference,
        position: References.position,
        url: References.url,
        scrappingRecommendation: References.scrappingRecommendation,
      })
      .from(References)
      .leftJoin(Employers, eq(Employers.id, Employers.employerId))
      .where(eq(References.userId, user.id));

    if (status) {
      query = query.where(eq(UsersInterests.status, status));
    }

    const references = await query.execute();

    console.log(
      "Referencias obtenidas correctamente",
      JSON.stringify(references, null, 2)
    );

    return {
      isValid: true,
      data: {
        references,
      },
    };
  } catch (error) {
    console.error("Error al obtener los intereses", error);
    return {
      isValid: false,
      error: "Error al obtener los intereses",
    };
  }
};
