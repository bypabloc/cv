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

export const Users = defineTable({
  columns: {
    ...base,
    username: column.text({ unique: true }),
  },
});

export const Networks = defineTable({
  columns: {
    ...base,
    codeName: column.text({ unique: true }),
    name: column.text(),
    url: column.text(),
  },
});

export const TypeFiles = defineTable({
  columns: {
    ...base,
    codeName: column.text({ unique: true }),
    name: column.text(),
    extension: column.text(),
    mime: column.text({ optional: true }),
    tag: column.text({ optional: true }),
    priority: column.number({ optional: true }),
  },
});

export const GroupsFiles = defineTable({
  columns: {
    ...base,
    name: column.text({ unique: true }),
    description: column.text({ optional: true }),
    priority: column.number({ optional: true }),
  },
});

export const Files = defineTable({
  columns: {
    ...base,
    groupFileId: column.text({
      references: () => GroupsFiles.columns.id,
    }),
    userId: column.text({
      references: () => Users.columns.id,
    }),
    fileTypeId: column.text({
      references: () => TypeFiles.columns.id,
    }),
    url: column.text(),
    priority: column.number({ optional: true }),
    description: column.text({ optional: true }),
  },
});

export const Institutions = defineTable({
  columns: {
    ...base,
    codeName: column.text({ unique: true }),
    name: column.text(),
    url: column.text(),
    locationUrl: column.text({ optional: true }),
    mapEmbed: column.text({ optional: true }),
  },
});

export const Issuers = defineTable({
  columns: {
    ...base,
    codeName: column.text({ unique: true }),
    name: column.text(),
    url: column.text(),
  },
});

export const Publishers = defineTable({
  columns: {
    ...base,
    codeName: column.text({ unique: true }),
    name: column.text(),
    url: column.text(),
  },
});

export const Languages = defineTable({
  columns: {
    ...base,
    codeName: column.text({ unique: true }),
    name: column.text(),
  },
});

export const Keywords = defineTable({
  columns: {
    ...base,
    codeName: column.text({ unique: true }),
    name: column.text(),
    keys: column.json(),
  },
});

export const Interests = defineTable({
  columns: {
    ...base,
    codeName: column.text({ unique: true }),
    name: column.text(),
  },
});

export const InterestsKeywords = defineTable({
  columns: {
    interestId: column.text({
      references: () => Interests.columns.id,
    }),
    keywordId: column.text({
      references: () => Keywords.columns.id,
    }),
  },
});

export const Skills = defineTable({
  columns: {
    ...base,
    codeName: column.text({ unique: true }),
    name: column.text(),
    description: column.text({ optional: true }),
    type: column.text(), // Tipo de habilidad, por ejemplo, 'Technical', 'Soft', etc.
  },
});

export const SkillsKeywords = defineTable({
  columns: {
    skillId: column.text({
      references: () => Skills.columns.id,
    }),
    keywordId: column.text({
      references: () => Keywords.columns.id,
    }),
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
    email: column.text({ unique: true }),
    phone: column.text(),
    url: column.text(),
    summary: column.text(),
    location: column.json(),
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
    username: column.text(),
  },
});

export const Employers = defineTable({
  columns: {
    ...base,
    userId: column.text({
      references: () => Users.columns.id,
      optional: true,
    }),
    codeName: column.text({ unique: true }),
    name: column.text(),
    url: column.text({ optional: true }),
    description: column.text({ optional: true }),
    serviceStatus: column.text({ default: "active" }),
  },
});

export const JobTypes = defineTable({
  columns: {
    ...base,
    codeName: column.text({ unique: true }),
    name: column.text(),
  },
});

export const Works = defineTable({
  columns: {
    ...base,
    userId: column.text({
      references: () => Users.columns.id,
    }),
    employerId: column.text({
      references: () => Employers.columns.id,
      optional: true,
    }),
    codeName: column.text({ unique: true }),
    name: column.text(),
    position: column.text(),
    startDate: column.date(),
    endDate: column.date({ optional: true }),
    jobTypeId: column.text({
      references: () => JobTypes.columns.id,
    }),
    summary: column.text({ optional: true }),
    responsibilitiesNProjects: column.json({ optional: true }),
    achievements: column.json({ optional: true }),
  },
});

export const WorksTechnicalSkills = defineTable({
  columns: {
    workId: column.text({
      references: () => Works.columns.id,
    }),
    technicalSkillId: column.text({
      references: () => Skills.columns.id,
    }),
  },
});

export const WorksSoftSkills = defineTable({
  columns: {
    workId: column.text({
      references: () => Works.columns.id,
    }),
    skillId: column.text({
      references: () => Skills.columns.id,
    }),
  },
});

export const Educations = defineTable({
  columns: {
    ...base,
    userId: column.text({
      references: () => Users.columns.id,
    }),
    institutionId: column.text({
      references: () => Institutions.columns.id,
    }),
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

export const UsersInterests = defineTable({
  columns: {
    userId: column.text({
      references: () => Users.columns.id,
    }),
    interestId: column.text({
      references: () => Interests.columns.id,
    }),
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
    serviceStatus: column.text({ default: "active" }),
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
    employerId: column.text({
      references: () => Employers.columns.id,
      optional: true,
    }),
    scrappingRecommendation: column.json({ optional: true }),
  },
});

export default defineDb({
  tables: {
    Awards,
    GroupsFiles,
    Files,
    Basics,
    Certificates,
    Educations,
    TypeFiles,
    Employers,
    Institutions,
    Interests,
    Issuers,
    JobTypes,
    Keywords,
    Languages,
    LanguagesUsers,
    Networks,
    NetworksUsers,
    Projects,
    Publications,
    Publishers,
    References,
    Skills,
    Users,
    Works,
    SkillsKeywords,
    WorksSoftSkills,
    WorksTechnicalSkills,
    InterestsKeywords,
  },
});
