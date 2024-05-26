import {
  db,
  eq,
  Interests,
  UsersInterests,
  InterestsKeywords,
  Keywords,
  Translations,
  Languages,
  sql,
} from "astro:db";

/**
 * Consulta que devuelve todos los intereses del usuario, incluyendo las traducciones.
 *
 * @param {string} status - Estado del usuario para filtrar.
 * @param {object} user - Usuario para filtrar.
 * @param {string} [languageCode="en"] - Código del idioma para las traducciones.
 * @returns {Promise<object>} - Resultado de la consulta.
 */
export const getInterests = async ({
  status,
  user,
  languageCode = "es",
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

    // Realizar la consulta principal incluyendo las traducciones
    let query = db
      .select({
        id: UsersInterests.id,
        status: UsersInterests.status,
        name: sql`COALESCE(
          (SELECT ${Translations.translatedValue} 
           FROM ${Translations} 
           WHERE ${Translations.recordId} = ${Interests.id} 
             AND ${Translations.tableName} = 'Interests' 
             AND ${Translations.field} = 'name' 
             AND ${Translations.languageId} = ${languageId}), 
          ${Interests.name}) AS name`,
        keywords: sql`json_group_array(json_object(
          'id', ${Keywords.id}, 
          'name', COALESCE(
            (SELECT ${Translations.translatedValue} 
             FROM ${Translations} 
             WHERE ${Translations.recordId} = ${Keywords.id} 
               AND ${Translations.tableName} = 'Keywords' 
               AND ${Translations.field} = 'name' 
               AND ${Translations.languageId} = ${languageId}), 
            ${Keywords.name}))) AS keywords`,
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
