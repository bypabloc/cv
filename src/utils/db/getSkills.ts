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
  Users,
  Employers,
} from "astro:db";

/**
 * Consulta que devuelve todas las habilidades técnicas y blandas únicas.
 *
 * @param {string} status - Estado del usuario para filtrar.
 * @param {object} user - Usuario para filtrar.
 * @returns {Promise<object>} - Resultado de la consulta con habilidades técnicas y blandas únicas.
 */
export const getSkills = async ({
  status,
  user,
}: {
  status?: string;
  user: Object;
} = {}): Promise<ResponseFunction> => {
  try {
    let query = db
      .select({
        id: Works.id,
      })
      .from(Works)
      .where(eq(Works.userId, user.id));

    if (status) {
      query = query.where(eq(Works.status, status));
    }

    const rawData = await query.execute();

    if (!rawData.length) {
      console.error("Experiencias laborales no encontradas");
      return {
        isValid: false,
        error: "Experiencias laborales no encontradas",
      };
    }

    const worksIds = rawData.map((item) => item.id);

    const technicalSkills = await db
      .select({
        id: WorksTechnicalSkills.technicalSkillId,
        codeName: Skills.codeName,
        name: Skills.name,
        description: Skills.description,
        type: Skills.type,
      })
      .from(Skills)
      .innerJoin(
        WorksTechnicalSkills,
        eq(WorksTechnicalSkills.technicalSkillId, Skills.id)
      )
      .where(inArray(WorksTechnicalSkills.workId, worksIds));

    const softSkills = await db
      .select({
        id: WorksSoftSkills.skillId,
        codeName: Skills.codeName,
        name: Skills.name,
        description: Skills.description,
        type: Skills.type,
      })
      .from(Skills)
      .innerJoin(WorksSoftSkills, eq(WorksSoftSkills.skillId, Skills.id))
      .where(inArray(WorksSoftSkills.workId, worksIds));

    // Remover duplicados en habilidades técnicas
    const uniqueTechnicalSkills = [
      ...new Map(technicalSkills.map((skill) => [skill.id, skill])).values(),
    ];

    // Remover duplicados en habilidades blandas
    const uniqueSoftSkills = [
      ...new Map(softSkills.map((skill) => [skill.id, skill])).values(),
    ];

    return {
      isValid: true,
      data: {
        technical: uniqueTechnicalSkills,
        soft: uniqueSoftSkills,
      },
    };
  } catch (error) {
    console.error("Error al obtener las habilidades:", error);
    return {
      isValid: false,
      error: "Error al obtener las habilidades",
    };
  }
};
