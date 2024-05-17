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

    const rawData = await query.execute();

    if (!rawData.length) {
      console.error("Experiencias laborales no encontradas");
      return {
        isValid: false,
        error: "Experiencias laborales no encontradas",
      };
    }

    console.log(
      "Experiencias laborales encontradas:",
      JSON.stringify(rawData, null, 2)
    );

    const worksIds = rawData.map((item) => item.id);

    // Organizar los datos en un objeto clave-valor basado en el ID de Works
    const works = {};
    rawData.forEach((item) => {
      works[item.id] = item; // Asignar cada trabajo como un valor de la clave correspondiente a su ID
    });

    const skillsIds = [];

    // Obtener habilidades técnicas asociadas a las experiencias laborales
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
        keywords: [], // Placeholder para las keywords que se asignarán más adelante
      });
      skillsIds.push(item.skillId);
    });

    console.log("technicalSkills", JSON.stringify(technicalSkills, null, 2));

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

    console.log("softSkills", JSON.stringify(softSkills, null, 2));

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
        keywords: [], // Placeholder para las keywords que se asignarán más adelante
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

    console.log("skillsKeywords:", JSON.stringify(skillsKeywords, null, 2));

    // Asignar las keywords a cada skill
    const skillsWithKeywords = {};
    skillsKeywords.forEach((item) => {
      if (!skillsWithKeywords[item.skillId]) {
        skillsWithKeywords[item.skillId] = [];
      }
      skillsWithKeywords[item.skillId].push(...item.keys);
    });

    // Asignar las keywords a cada skill en las experiencias laborales
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

    // Convertir works a un arreglo antes de devolverlo
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
