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
    let query = db.select().from(Works);

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

    // Cargar habilidades técnicas asociadas
    const technicalSkillsPromises = works.map((work) =>
      db
        .select()
        .from(WorksTechnicalSkills)
        .innerJoin(
          TechnicalSkills,
          eq(WorksTechnicalSkills.technicalSkillId, TechnicalSkills.id)
        )
        .where(eq(WorksTechnicalSkills.workId, work.id))
        .execute()
    );
    const technicalSkillsResults = await Promise.all(technicalSkillsPromises);

    // Cargar habilidades blandas asociadas
    const softSkillsPromises = works.map((work) =>
      db
        .select()
        .from(WorksSoftSkills)
        .innerJoin(SoftSkills, eq(WorksSoftSkills.skillId, SoftSkills.id))
        .where(eq(WorksSoftSkills.workId, work.id))
        .execute()
    );
    const softSkillsResults = await Promise.all(softSkillsPromises);

    // Combinar habilidades con las experiencias laborales
    works.forEach((work, index) => {
      work.technicalSkills = technicalSkillsResults[index];
      work.softSkills = softSkillsResults[index];
    });

    console.log("Experiencias laborales obtenidas:", works);

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
