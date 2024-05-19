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
  Projects,
  Users,
  Employers,
} from "astro:db";

/**
 * Consulta que devuelve todos los proyectos de un usuario.
 *
 * @param {string} status - Estado del usuario para filtrar.
 * @returns {Promise<object>} - Resultado de la consulta de los proyectos.
 */
export const getProjects = async ({
  status,
  user,
}: {
  status?: string;
} = {}): Promise<ResponseFunction> => {
  try {
    let query = db
      .select({
        id: Projects.id,
        status: Projects.status,
        name: Projects.name,
        description: Projects.description,
        highlights: Projects.highlights,
        url: Projects.url,
        serviceStatus: Projects.serviceStatus,
      })
      .from(Projects);

    if (status) {
      query = query.where(eq(Works.status, status));
    }

    const projects = await query;

    return {
      isValid: true,
      data: {
        projects,
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
