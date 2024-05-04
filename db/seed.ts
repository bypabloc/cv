import {
  db,
  like,
  not,
  eq,
  and,
  inArray,
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
} from "astro:db";

import jsonData from "./data";
import { registerNewRecords } from "./utils/registerNewRecords";

// Aquí van tus datos JSON como un objeto JS directamente en el script para simplificar

// Función asíncrona para insertar los datos
export default async function () {
  // astro db execute "./db/seed.ts" --remote
  /**
    Networks
    Users
    typeFiles
    Institutions
    Issuers
    Publishers
    Languages
    Keywords
    Employers
    JobTypes
  */
  const requestList: any[] = [];

  /**
  Networks
  Users
  typeFiles
  Institutions
  Issuers
  Publishers
  Languages
  GroupsFiles
  Skills
  Keywords
  Employers
  JobTypes
  Interests
   */
  const users = await registerNewRecords(Users, "username", jsonData.users);
  console.log("users", users);

  const networks = await registerNewRecords(
    Networks,
    "codeName",
    jsonData.networks
  );
  console.log("networks", networks);

  const typeFiles = await registerNewRecords(
    TypeFiles,
    "codeName",
    jsonData.typeFiles
  );
  console.log("typeFiles", typeFiles);

  const institutions = await registerNewRecords(
    Institutions,
    "codeName",
    jsonData.institutions
  );
  console.log("institutions", institutions);

  const issuers = await registerNewRecords(
    Issuers,
    "codeName",
    jsonData.issuers
  );
  console.log("issuers", issuers);

  const publishers = await registerNewRecords(
    Publishers,
    "codeName",
    jsonData.publishers
  );
  console.log("publishers", publishers);

  const languages = await registerNewRecords(
    Languages,
    "codeName",
    jsonData.languages
  );
  console.log("languages", languages);

  const keywords = await registerNewRecords(
    Keywords,
    "codeName",
    jsonData.keywords
  );
  console.log("keywords", keywords);

  const employers = await registerNewRecords(
    Employers,
    "codeName",
    jsonData.employers
  );
  console.log("employers", employers);

  const jobTypes = await registerNewRecords(
    JobTypes,
    "codeName",
    jsonData.jobTypes
  );
  console.log("jobTypes", jobTypes);

  const groupsFiles = await registerNewRecords(
    GroupsFiles,
    "codeName",
    jsonData.groupsFiles
  );
  console.log("groupsFiles", groupsFiles);

  const skills = await registerNewRecords(Skills, "codeName", jsonData.skills);
  console.log("skills", skills);

  const interests = await registerNewRecords(
    Interests,
    "codeName",
    jsonData.interests
  );
  console.log("interests", interests);
}
