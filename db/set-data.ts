import {
  Users,
  UsersAttributes,
  AttributesTypes,
  Awards,
  GroupsFiles,
  Files,
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
  UsersInterests,
  Networks,
  NetworksUsers,
  Projects,
  Publications,
  Translations,
  Publishers,
  References,
  Skills,
  Works,
  SkillsKeywords,
  WorksSoftSkills,
  WorksTechnicalSkills,
  InterestsKeywords,
} from "astro:db";

import jsonData from "./data";
import { registerNewRecords } from "./utils/registerNewRecords";
import { registerRecordsWithRelations } from "./utils/registerRecordsWithRelations";

// Función asíncrona para insertar los datos
export default async function () {
  // // astro db execute "./db/seed.ts" --remote

  /**  
    sqlRaw > select "id", "status", "createdAt", "updatedAt", "userId", "employerId", "codeName", "name", "position", "startDate", "endDate", "jobTypeId", "summary", "responsibilitiesNProjects", "achievements" from "Works" where ?
    paramsRaw > [ "codeName = 'destacame-architect'" ]
   */

  /*
  const columns = Works[Symbol.for("drizzle:Columns")];
  const keysColumns = Object.keys(columns);

  console.log("--------- Columns ---------", columns);
  console.log("--------- Keys Columns ---------", keysColumns);
  console.log("--------- Keys Columns ---------", columns.achievements);

  // example columns.achievements.config.customTypeParams

  console.log(
    "----------------------- achievements -----------------------",
    columns.achievements
  );

  console.log(
    "--------- customTypeParams ---------",
    columns.startDate.config.customTypeParams.dataType()
  );

  if (true) {
    return;
  }
  */

  const tables: Record<string, any> = {};

  tables["users"] = {
    records: await registerNewRecords(Users, "username", jsonData.users),
    model: Users,
  };

  tables["networks"] = {
    records: await registerNewRecords(Networks, "codeName", jsonData.networks),
    model: Networks,
  };

  tables["typeFiles"] = {
    records: await registerNewRecords(
      TypeFiles,
      "codeName",
      jsonData.typeFiles
    ),
    model: TypeFiles,
  };

  tables["institutions"] = {
    records: await registerNewRecords(
      Institutions,
      "codeName",
      jsonData.institutions
    ),
    model: Institutions,
  };

  tables["issuers"] = {
    records: await registerNewRecords(Issuers, "codeName", jsonData.issuers),
    model: Issuers,
  };

  tables["publishers"] = {
    records: await registerNewRecords(
      Publishers,
      "codeName",
      jsonData.publishers
    ),
    model: Publishers,
  };

  tables["languages"] = {
    records: await registerNewRecords(
      Languages,
      "codeName",
      jsonData.languages
    ),
    model: Languages,
  };

  tables["keywords"] = {
    records: await registerNewRecords(Keywords, "codeName", jsonData.keywords),
    model: Keywords,
  };

  tables["employers"] = {
    records: await registerNewRecords(
      Employers,
      "codeName",
      jsonData.employers
    ),
    model: Employers,
  };

  tables["jobTypes"] = {
    records: await registerNewRecords(JobTypes, "codeName", jsonData.jobTypes),
    model: JobTypes,
  };

  tables["groupsFiles"] = {
    records: await registerNewRecords(
      GroupsFiles,
      "codeName",
      jsonData.groupsFiles
    ),
    model: GroupsFiles,
  };

  tables["skills"] = {
    records: await registerNewRecords(Skills, "codeName", jsonData.skills),
    model: Skills,
  };

  tables["interests"] = {
    records: await registerNewRecords(
      Interests,
      "codeName",
      jsonData.interests
    ),
    model: Interests,
  };

  tables["attributesTypes"] = {
    records: await registerNewRecords(
      AttributesTypes,
      "codeName",
      jsonData.attributesTypes
    ),
    model: AttributesTypes,
  };

  /**
      Basics
      NetworksUsers
      Works
      Educations
      Awards
      Certificates
      Publications
      LanguagesUsers
      Projects
      References
      Files
      SkillsKeywords
      InterestsKeywords
    */
  tables["usersAttributes"] = {
    records: await registerRecordsWithRelations(
      UsersAttributes,
      jsonData.usersAttributes,
      tables
    ),
    model: UsersAttributes,
  };

  tables["usersAttributesTranslations"] = {
    records: await registerRecordsWithRelations(
      Translations,
      jsonData.usersAttributesTranslations,
      tables
    ),
    model: Translations,
  };

  tables["networksUsers"] = {
    records: await registerRecordsWithRelations(
      NetworksUsers,
      jsonData.networksUsers,
      tables
    ),
    model: NetworksUsers,
  };

  tables["works"] = {
    records: await registerRecordsWithRelations(
      Works,
      jsonData.works,
      tables
      // "codeName"
    ),
    model: Works,
  };

  tables["educations"] = {
    records: await registerRecordsWithRelations(
      Educations,
      jsonData.educations,
      tables
    ),
    model: Educations,
  };

  tables["awards"] = {
    records: await registerRecordsWithRelations(
      Awards,
      jsonData.awards,
      tables
    ),
    model: Awards,
  };

  tables["certificates"] = {
    records: await registerRecordsWithRelations(
      Certificates,
      jsonData.certificates,
      tables
    ),
    model: Certificates,
  };

  tables["publications"] = {
    records: await registerRecordsWithRelations(
      Publications,
      jsonData.publications,
      tables
    ),
    model: Publications,
  };

  tables["languagesUsers"] = {
    records: await registerRecordsWithRelations(
      LanguagesUsers,
      jsonData.languagesUsers,
      tables
    ),
    model: LanguagesUsers,
  };

  tables["projects"] = {
    records: await registerRecordsWithRelations(
      Projects,
      jsonData.projects,
      tables
    ),
    model: Projects,
  };

  tables["references"] = {
    records: await registerRecordsWithRelations(
      References,
      jsonData.references,
      tables
    ),
    model: References,
  };

  tables["files"] = {
    records: await registerRecordsWithRelations(Files, jsonData.files, tables),
    model: Files,
  };

  tables["skillsKeywords"] = {
    records: await registerRecordsWithRelations(
      SkillsKeywords,
      jsonData.skillsKeywords,
      tables
    ),
    model: SkillsKeywords,
  };

  tables["interestsKeywords"] = {
    records: await registerRecordsWithRelations(
      InterestsKeywords,
      jsonData.interestsKeywords,
      tables
    ),
    model: InterestsKeywords,
  };

  tables["usersInterests"] = {
    records: await registerRecordsWithRelations(
      UsersInterests,
      jsonData.usersInterests,
      tables
    ),
    model: UsersInterests,
  };

  tables["worksSoftSkills"] = {
    records: await registerRecordsWithRelations(
      WorksSoftSkills,
      jsonData.worksSoftSkills,
      tables
    ),
    model: WorksSoftSkills,
  };

  tables["worksTechnicalSkills"] = {
    records: await registerRecordsWithRelations(
      WorksTechnicalSkills,
      jsonData.worksTechnicalSkills,
      tables
    ),
    model: WorksTechnicalSkills,
  };

  // - Keywords
  // - Works
  // - Skills
  // - Educations
  // - Awards
  // - Languages
  // - Interests
  // - References
  // - UsersAttributes

  tables["keywordsTranslations"] = {
    records: await registerRecordsWithRelations(
      Translations,
      jsonData.keywordsTranslations,
      tables
    ),
    model: Translations,
  };

  tables["interestsTranslations"] = {
    records: await registerRecordsWithRelations(
      Translations,
      jsonData.interestsTranslations,
      tables
    ),
    model: Translations,
  };

  tables["worksTranslations"] = {
    records: await registerRecordsWithRelations(
      Translations,
      jsonData.worksTranslations,
      tables
    ),
    model: Translations,
  };

  tables["skillsTranslations"] = {
    records: await registerRecordsWithRelations(
      Translations,
      jsonData.skillsTranslations,
      tables
    ),
    model: Translations,
  };

  tables["educationsTranslations"] = {
    records: await registerRecordsWithRelations(
      Translations,
      jsonData.educationsTranslations,
      tables
    ),
    model: Translations,
  };

  tables["awardsTranslations"] = {
    records: await registerRecordsWithRelations(
      Translations,
      jsonData.awardsTranslations,
      tables
    ),
    model: Translations,
  };

  tables["languagesUsersTranslations"] = {
    records: await registerRecordsWithRelations(
      Translations,
      jsonData.languagesUsersTranslations,
      tables
    ),
    model: Translations,
  };

  tables["referencesTranslations"] = {
    records: await registerRecordsWithRelations(
      Translations,
      jsonData.referencesTranslations,
      tables
    ),
    model: Translations,
  };
}
