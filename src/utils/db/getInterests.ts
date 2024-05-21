import {
  db,
  eq,
  Interests,
  UsersInterests,
  InterestsKeywords,
  Keywords,
  sql,
} from "astro:db";

/**
 * Consulta que devuelve todos los intereses del usuario.
 *
 * @param {string} status - Estado del usuario para filtrar.
 * @param {object} user - Usuario para filtrar.
 * @returns {Promise<object>} - Resultado de la consulta.
 */
export const getInterests = async ({
  status,
  user,
}: {
  status?: string;
  user: { id: string };
}): Promise<ResponseFunction> => {
  try {
    let query = db
      .select({
        id: UsersInterests.id,
        status: UsersInterests.status,
        name: Interests.name,
        keywords: sql`json_group_array(json_object('id', ${Keywords.id}, 'name', ${Keywords.name}))`,
      })
      .from(UsersInterests)
      .leftJoin(Interests, eq(Interests.id, UsersInterests.interestId))
      .leftJoin(
        InterestsKeywords,
        eq(InterestsKeywords.interestId, Interests.id)
      )
      .leftJoin(Keywords, eq(Keywords.id, InterestsKeywords.keywordId))
      .where(eq(UsersInterests.userId, user.id))
      .groupBy(UsersInterests.id, UsersInterests.status, Interests.name);

    if (status) {
      query = query.where(eq(UsersInterests.status, status));
    }

    const interests = await query.execute();

    // Convertir el campo `keywords` de cada resultado a un array de objetos
    const formattedInterests = interests.map((interest) => {
      return {
        ...interest,
        keywords: JSON.parse(interest.keywords),
      };
    });

    // console.log(
    //   "Intereses obtenidos correctamente",
    //   JSON.stringify(formattedInterests, null, 2)
    // );

    return {
      isValid: true,
      data: {
        interests: formattedInterests,
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
