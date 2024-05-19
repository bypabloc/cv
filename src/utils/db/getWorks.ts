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
  user: Object;
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
        employer: Employers,
      })
      .from(Works)
      .where(eq(Works.userId, user.id))
      .leftJoin(Employers, eq(Works.employerId, Employers.id));

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

    const works = {};
    rawData.forEach((item) => {
      works[item.id] = item;
    });

    const skillsIds = [];

    const technicalSkills = await db
      .select({
        workId: WorksTechnicalSkills.workId,
        skillId: WorksTechnicalSkills.technicalSkillId,
        skillCodeName: Skills.codeName,
        skillName: Skills.name,
        skillDescription: Skills.description,
        skillType: Skills.type,
      })
      .from(Skills)
      .innerJoin(
        WorksTechnicalSkills,
        eq(WorksTechnicalSkills.technicalSkillId, Skills.id)
      )
      .where(inArray(WorksTechnicalSkills.workId, worksIds));

    technicalSkills.forEach((item) => {
      if (!works[item.workId].technicalSkills) {
        works[item.workId].technicalSkills = [];
      }
      works[item.workId].technicalSkills.push({
        id: item.skillId,
        codeName: item.skillCodeName,
        name: item.skillName,
        description: item.skillDescription,
        type: item.skillType,
        keywords: [],
      });
      skillsIds.push(item.skillId);
    });

    const softSkills = await db
      .select({
        workId: WorksSoftSkills.workId,
        skillId: WorksSoftSkills.skillId,
        skillCodeName: Skills.codeName,
        skillName: Skills.name,
        skillDescription: Skills.description,
        skillType: Skills.type,
      })
      .from(Skills)
      .innerJoin(WorksSoftSkills, eq(WorksSoftSkills.skillId, Skills.id))
      .where(inArray(WorksSoftSkills.workId, worksIds));

    softSkills.forEach((item) => {
      if (!works[item.workId].softSkills) {
        works[item.workId].softSkills = [];
      }
      works[item.workId].softSkills.push({
        id: item.skillId,
        codeName: item.skillCodeName,
        name: item.skillName,
        description: item.skillDescription,
        type: item.skillType,
        keywords: [],
      });
      skillsIds.push(item.skillId);
    });

    const skillsIdsUniques = Array.from(new Set(skillsIds));

    const skillsKeywords = await db
      .select({
        skillId: SkillsKeywords.skillId,
        keywordId: Keywords.id,
        keys: Keywords.keys,
      })
      .from(SkillsKeywords)
      .innerJoin(Keywords, eq(Keywords.id, SkillsKeywords.keywordId))
      .where(inArray(SkillsKeywords.skillId, skillsIdsUniques));

    const skillsWithKeywords = {};
    skillsKeywords.forEach((item) => {
      if (!skillsWithKeywords[item.skillId]) {
        skillsWithKeywords[item.skillId] = [];
      }
      skillsWithKeywords[item.skillId].push(...item.keys);
    });

    Object.keys(works).forEach((workId) => {
      if (works[workId].technicalSkills) {
        works[workId].technicalSkills = works[workId].technicalSkills.map(
          (skill) => ({
            ...skill,
            keywords: skillsWithKeywords[skill.id] || [],
          })
        );
      }
      if (works[workId].softSkills) {
        works[workId].softSkills = works[workId].softSkills.map((skill) => ({
          ...skill,
          keywords: skillsWithKeywords[skill.id] || [],
        }));
      }
    });

    console.log("works:", JSON.stringify(works, null, 2));

    const worksArray = Object.values(works);

    return {
      isValid: true,
      data: {
        works: worksArray,
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
