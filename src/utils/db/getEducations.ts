import {
  db,
  eq,
  innerJoin,
  inArray,
  Works,
  Skills,
  WorksTechnicalSkills,
  Skills as TechnicalSkills,
  WorksSoftSkills,
  Keywords,
  Skills as SoftSkills,
  SkillsKeywords,
  Educations,
  Users,
  Employers,
  Institutions,
} from "astro:db";

/**
 * Consulta que devuelve todos los proyectos de un usuario.
 *
 * @param {string} status - Estado del usuario para filtrar.
 * @returns {Promise<object>} - Resultado de la consulta de los proyectos.
 */
export const getEducations = async ({
  status,
  user,
}: {
  status?: string;
} = {}): Promise<ResponseFunction> => {
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
      .leftJoin(Institutions, eq(Institutions.id, Educations.institutionId));

    if (status) {
      query = query.where(eq(Educations.status, status));
    }

    const educations = await query;

    console.log("educations:", JSON.stringify(educations, null, 2));

    return {
      isValid: true,
      data: {
        educations: educations || [],
      },
    };
  } catch (error) {
    console.error("Error al obtener las experiencias laborales:", error);
    return {
      isValid: false,
      error: "Error al obtener las experiencias laborales",
    };
  }
};
