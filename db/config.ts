import { defineDb, defineTable, column, sql, NOW } from "astro:db";

const base = {
  id: column.text({
    primaryKey: true,
    unique: true,
    default: sql`gen_random_uuid()`,
  }),
  status: column.text({ default: "active" }),
  createdAt: column.date({ default: NOW }),
  updatedAt: column.date({ default: NOW }),
};

export const Networks = defineTable({
  columns: {
    ...base,
    name: column.text({ unique: true }),
    url: column.text(),
  },
});

export const Users = defineTable({
  columns: {
    ...base,
    username: column.text({ unique: true }),
  },
});

export const Basics = defineTable({
  columns: {
    ...base,
    userId: column.text({
      references: () => Users.columns.id,
    }),
    names: column.text(),
    lastName: column.text(),
    label: column.text(),
    image: column.text(),
    email: column.text(),
    phone: column.text(),
    url: column.text(),
    summary: column.text(),
    location: column.json(),
  },
});

export const Images = defineTable({
  columns: {
    ...base,
    userId: column.text({
      references: () => Users.columns.id,
    }),
    type: column.text(),
    sort: column.number(),
    url: column.text(),
  },
});

export const NetworksUsers = defineTable({
  columns: {
    ...base,
    networkId: column.text({
      references: () => Networks.columns.id,
    }),
    userId: column.text({
      references: () => Users.columns.id,
    }),
  },
});

export const Works = defineTable({
  columns: {
    ...base,
    userId: column.text({
      references: () => Users.columns.id,
    }),
    name: column.text({ unique: true }),
    position: column.text(),
    url: column.text({ optional: true }),
    startDate: column.date(),
    responsibilitiesNProjects: column.json(),
    achievements: column.json(),
  },
});

export const TechnicalSkills = defineTable({
  columns: {
    ...base,
    userId: column.text({
      references: () => Users.columns.id,
    }),
    name: column.text(),
  },
});

export const SoftSkills = defineTable({
  columns: {
    ...base,
    userId: column.text({
      references: () => Users.columns.id,
    }),
    name: column.text(),
  },
});

export const Aptitudes = defineTable({
  columns: {
    ...base,
    userId: column.text({
      references: () => Users.columns.id,
    }),
    name: column.text(),
  },
});

export const WorksTechnicalSkills = defineTable({
  columns: {
    workId: column.text({
      references: () => Works.columns.id,
    }),
    technicalSkillId: column.text({
      references: () => TechnicalSkills.columns.id,
    }),
  },
});

export const WorksSoftSkills = defineTable({
  columns: {
    workId: column.text({
      references: () => Works.columns.id,
    }),
    softSkillId: column.text({
      references: () => SoftSkills.columns.id,
    }),
  },
});

export const WorksAptitudes = defineTable({
  columns: {
    workId: column.text({
      references: () => Works.columns.id,
    }),
    aptitudeId: column.text({
      references: () => Aptitudes.columns.id,
    }),
  },
});

export const Institution = defineTable({
  columns: {
    ...base,
    name: column.text(),
  },
});

export const Education = defineTable({
  columns: {
    ...base,
    userId: column.text({
      references: () => Users.columns.id,
    }),
    institutionId: column.text({
      references: () => Institution.columns.id,
    }),
    url: column.text(),
    area: column.text(),
    learn: column.text(),
    studyType: column.text(),
    startDate: column.date(),
    endDate: column.date(),
  },
});

export const Awards = defineTable({
  columns: {
    ...base,
    userId: column.text({
      references: () => Users.columns.id,
    }),
    title: column.text(),
    date: column.date(),
    awarder: column.text(),
    summary: column.text(),
    url: column.text(),
  },
});

export const Issuers = defineTable({
  columns: {
    ...base,
    name: column.text(),
    url: column.text(),
  },
});

export const Certificates = defineTable({
  columns: {
    ...base,
    userId: column.text({
      references: () => Users.columns.id,
    }),
    title: column.text(),
    date: column.date(),
    IssuersId: column.text({
      references: () => Issuers.columns.id,
    }),
    url: column.text(),
  },
});

export const Publishers = defineTable({
  columns: {
    ...base,
    name: column.text({ unique: true }),
    link: column.text(),
  },
});

export const Publications = defineTable({
  columns: {
    ...base,
    userId: column.text({
      references: () => Users.columns.id,
    }),
    name: column.text(),
    publisherId: column.text({
      references: () => Publishers.columns.id,
    }),
    releaseDate: column.date(),
    url: column.text(),
    summary: column.text(),
  },
});

export const Languages = defineTable({
  columns: {
    ...base,
    name: column.text({ unique: true }),
  },
});

export const LanguagesUsers = defineTable({
  columns: {
    ...base,
    userId: column.text({
      references: () => Users.columns.id,
    }),
    languageId: column.text({
      references: () => Languages.columns.id,
    }),
    fluency: column.text(),
  },
});

export const Keywords = defineTable({
  columns: {
    ...base,
    name: column.text({ unique: true }),
  },
});

export const KeywordsInterests = defineTable({
  columns: {
    userId: column.text({
      references: () => Users.columns.id,
    }),
    keywordId: column.text({
      references: () => Keywords.columns.id,
    }),
    interestId: column.text({
      references: () => Interests.columns.id,
    }),
  },
});

export const Interests = defineTable({
  columns: {
    ...base,
    name: column.text({ unique: true }),
  },
});

export const Projects = defineTable({
  columns: {
    ...base,
    userId: column.text({
      references: () => Users.columns.id,
    }),
    name: column.text(),
    description: column.text(),
    highlights: column.json(),
    url: column.text(),
  },
});

export const References = defineTable({
  columns: {
    ...base,
    userId: column.text({
      references: () => Users.columns.id,
    }),
    name: column.text(),
    reference: column.text(),
    position: column.text(),
    url: column.text(),
  },
});

export const Skills = defineTable({
  columns: {
    ...base,
    name: column.text({ unique: true }),
    level: column.text(),
  },
});

export const SkillsUsers = defineTable({
  columns: {
    ...base,
    userId: column.text({
      references: () => Users.columns.id,
    }),
    skillId: column.text({
      references: () => Skills.columns.id,
    }),
  },
});

export const SkillsUsersKeywords = defineTable({
  columns: {
    ...base,
    skillUserId: column.text({
      references: () => SkillsUsers.columns.id,
    }),
    keywordId: column.text({
      references: () => Keywords.columns.id,
    }),
  },
});

export default defineDb({
  tables: {
    Basics,
    Aptitudes,
    Awards,
    Users,
    Certificates,
    Education,
    Institution,
    Interests,
    Issuers,
    Keywords,
    KeywordsInterests,
    Languages,
    Networks,
    Projects,
    Publications,
    Publishers,
    References,
    Skills,
    SkillsUsers,
    SkillsUsersKeywords,
    SoftSkills,
    TechnicalSkills,
    Works,
    WorksAptitudes,
    WorksSoftSkills,
    WorksTechnicalSkills,
  },
});
