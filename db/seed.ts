import { v5 as uuidV5 } from "uuid";

import {
  db,
  like,
  not,
  eq,
  and,
  inArray,
  Users,
  Basics,
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
  Networks,
  NetworksUsers,
  Projects,
  Publications,
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

// Aquí van tus datos JSON como un objeto JS directamente en el script para simplificar

// Función asíncrona para insertar los datos
export default async function () {
  // astro db execute "./db/seed.ts" --remote

  let userByPabloC = await db
    .select()
    .from(Users)
    .where(eq(Users.username, "bypabloc"))
    .execute();

  if (!userByPabloC.length) {
    await db.insert(Users).values([
      {
        username: "bypabloc",
      },
    ]);
    userByPabloC = await db
      .select()
      .from(Users)
      .where(eq(Users.username, "bypabloc"))
      .execute();
  }

  const userOne = userByPabloC[0];
  console.log("userOne", userOne);

  const basics = await db
    .select()
    .from(Basics)
    .where(eq(Basics.userId, userOne.id))
    .execute();
  console.log("basics", basics);
  if (basics.length) {
    return;
  }

  await db.insert(Basics).values([
    {
      names: "Pablo Alexander",
      lastName: "Contreras Guevara",
      label: "Ingeniero de software con más de 8 años de experiencia",
      email: "pacg1991@gmail.com",
      phone: "+51 918490148",
      url: "https://pablo-c.com",
      summary:
        "Ingeniero de software con más de 8 años de experiencia, especializado en desarrollo Full Stack con Python y JavaScript. Experto en crear soluciones tecnológicas con Vue, Django, microservicios y AWS, he desarrollado con éxito y liderado la implementación de sistemas ERP y plataformas fintech, mejorando significativamente la eficiencia operativa y la experiencia del usuario. Habilidoso en la coordinación y motivación de equipos, me adapto fácilmente a entornos dinámicos y desafiantes, siempre enfocado en la calidad y la innovación.",
      location: {
        address: "",
        postalCode: "15009",
        city: "Lima",
        countryCode: "PE",
        region: "Perú",
      },
      userId: userOne.id,
    },
  ]);

  const basicsList = await db
    .select()
    .from(Basics)
    .where(eq(Basics.userId, userOne.id))
    .execute();
  console.log("basicsList", basicsList);

  if (true) {
    return;
  }

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

  tables["basics"] = {
    records: await registerRecordsWithRelations(
      Basics,
      jsonData.basics,
      tables
    ),
    model: Basics,
  };
  console.log(tables["basics"]);
}
