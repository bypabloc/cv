import {
  db,
  eq,
  sql,
  Works,
  Skills,
  WorksTechnicalSkills,
  WorksSoftSkills,
  Keywords,
  SkillsKeywords,
  Employers,
} from "astro:db";

/**
 * Consulta que devuelve todas las experiencias laborales (Works)
 * incluyendo habilidades técnicas y blandas asociadas, organizadas en un objeto donde la clave es el ID de Works.
 *
 * @param {string} status - Estado del usuario para filtrar.
 * @returns {Promise<object>} - Resultado de la consulta con experiencias laborales y habilidades asociadas.
 */
export const getWorks = async ({
  status,
  user,
}: {
  status?: string;
  user: { id: string };
} = {}): Promise<ResponseFunction> => {
  try {
    // Consulta principal para obtener los trabajos
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
        employer: Employers,
        technicalSkills: sql`(
          SELECT json_group_array(
            json_object(
              'id', Skills.id,
              'codeName', Skills.codeName,
              'name', Skills.name,
              'description', Skills.description,
              'type', Skills.type,
              'keywords', (SELECT json_group_array(json_object('id', Keywords.id, 'keys', Keywords.keys))
                          FROM SkillsKeywords
                          INNER JOIN Keywords ON Keywords.id = SkillsKeywords.keywordId
                          WHERE SkillsKeywords.skillId = Skills.id)
            )
          )
          FROM WorksTechnicalSkills
          INNER JOIN Skills ON Skills.id = WorksTechnicalSkills.technicalSkillId
          WHERE WorksTechnicalSkills.workId = Works.id
        )`,
        softSkills: sql`(
          SELECT json_group_array(
            json_object(
              'id', Skills.id,
              'codeName', Skills.codeName,
              'name', Skills.name,
              'description', Skills.description,
              'type', Skills.type,
              'keywords', (SELECT json_group_array(json_object('id', Keywords.id, 'keys', Keywords.keys))
                          FROM SkillsKeywords
                          INNER JOIN Keywords ON Keywords.id = SkillsKeywords.keywordId
                          WHERE SkillsKeywords.skillId = Skills.id)
            )
          )
          FROM WorksSoftSkills
          INNER JOIN Skills ON Skills.id = WorksSoftSkills.skillId
          WHERE WorksSoftSkills.workId = Works.id
        )`,
      })
      .from(Works)
      .leftJoin(Employers, eq(Employers.id, Works.employerId))
      .where(eq(Works.userId, user.id))
      .orderBy(
        sql`
          CASE
            WHEN ${Works.endDate} IS NULL THEN 0
            ELSE 1
          END,
          ${Works.endDate} DESC NULLS FIRST,
          ${Works.startDate} DESC
        `
      );

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

    // Convertir los campos JSON de string a arrays de objetos
    const formattedWorks = rawData.map((work) => {
      const safelyParseKeywords = (skills) => {
        return skills.map((skill) => ({
          ...skill,
          keywords: Array.isArray(skill.keywords)
            ? skill.keywords.map((k) =>
                typeof k.keys === "string" ? JSON.parse(k.keys) : k.keys
              )
            : [],
        }));
      };

      return {
        ...work,
        technicalSkills: safelyParseKeywords(JSON.parse(work.technicalSkills)),
        softSkills: safelyParseKeywords(JSON.parse(work.softSkills)),
      };
    });

    // Agrupar por empleador, pero mantener los que no tienen empleador separados
    const groupedByEmployer = formattedWorks.reduce((acc, work) => {
      const employerId = work.employer?.id;
      if (employerId) {
        if (!acc[employerId]) {
          acc[employerId] = {
            employer: work.employer,
            works: [],
          };
        }
        acc[employerId].works.push(work);
      } else {
        acc[work.id] = {
          employer: null,
          works: [work],
        };
      }
      return acc;
    }, {});

    console.log(
      "Experiencias laborales agrupadas correctamente",
      JSON.stringify(groupedByEmployer, null, 2)
    );

    return {
      isValid: true,
      data: {
        works: groupedByEmployer,
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
