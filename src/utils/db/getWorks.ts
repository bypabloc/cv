import {
  db,
  eq,
  innerJoin,
  Works,
  WorksTechnicalSkills,
  Skills as TechnicalSkills,
  WorksSoftSkills,
  Skills as SoftSkills,
} from "astro:db";

/**
 * Consulta que devuelve todas las experiencias laborales (Works)
 * incluyendo habilidades técnicas y blandas asociadas.
 * @param {string} status - Estado del usuario para filtrar.
 * @returns {Promise<object>} - Resultado de la consulta con experiencias laborales y habilidades asociadas.
 */
export const getWorks = async ({
  status,
}: {
  status?: string;
} = {}): Promise<ResponseFunction> => {
  try {
    let query = db
      .select({
        id: Works.id,
        codeName: Works.codeName,
        name: Works.name,
        position: Works.position,
        startDate: Works.startDate,
        endDate: Works.endDate,
        responsibilitiesNProjects: Works.responsibilitiesNProjects,
        achievements: Works.achievements,
        summary: Works.summary,
      })
      .from(Works);

    if (status) {
      query = query.where(eq(Works.status, status));
    }

    const works = await query.execute();

    if (!works.length) {
      console.error("Experiencias laborales no encontradas");
      return {
        isValid: false,
        error: "Experiencias laborales no encontradas",
      };
    }

    console.log(
      "Experiencias laborales encontradas:",
      JSON.stringify(works, null, 2)
    );

    return {
      isValid: true,
      data: {
        works,
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
