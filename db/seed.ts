import { asDrizzleTable } from "@astrojs/db/utils";
import { db } from "astro:db";

import {
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
} from "./config"; // Asume que tus definiciones de tabla están en 'config.ts'

// Aquí van tus datos JSON como un objeto JS directamente en el script para simplificar
const jsonData = {
  networks: [
    {
      codeName: "linkedin",
      name: "LinkedIn",
      url: "https://linkedin.com/in",
    },
    {
      codeName: "github",
      name: "GitHub",
      url: "https://github.com",
    },
  ],
  basics: {
    username: "pablo-c",
    name: "Pablo Contreras",
    label: "Ingeniero de software con más de 8 años de experiencia",
    image: "/me.webp",
    email: "pacg1991@gmail.com",
    phone: "+51 918490148",
    url: "https://pablo-c.com",
    location: {
      address: "",
      postalCode: "15009",
      city: "Lima",
      countryCode: "PE",
      region: "Perú",
    },
    summary:
      "Ingeniero de software con más de 8 años de experiencia, especializado en desarrollo Full Stack con Python y JavaScript. Experto en crear soluciones tecnológicas con Vue, Django, microservicios y AWS, he desarrollado con éxito y liderado la implementación de sistemas ERP y plataformas fintech, mejorando significativamente la eficiencia operativa y la experiencia del usuario. Habilidoso en la coordinación y motivación de equipos, me adapto fácilmente a entornos dinámicos y desafiantes, siempre enfocado en la calidad y la innovación.",
  },
  profiles: [
    {
      network: "LinkedIn",
      username: "bypabloc",
      url: "https://linkedin.com/in/bypabloc",
    },
    {
      network: "GitHub",
      username: "bypabloc",
      url: "https://github.com/bypabloc",
    },
  ],
  work: [
    // tus datos de work
  ],
  education: [
    // tus datos de education
  ],
  skills: [
    // tus datos de skills
  ],
  interests: [
    // tus datos de interests
  ],
  projects: [
    // tus datos de projects
  ],
  awards: [
    // tus datos de awards
  ],
  certificates: [
    // tus datos de certificates
  ],
  publications: [
    // tus datos de publications
  ],
};

// Función asíncrona para insertar los datos
export default async function () {
  // astro db execute "./db/seed.ts" --remote
  const typeSafeProfiles = asDrizzleTable("Users", Users);
  // const profilesIds = await db
  //   .insert(typeSafeProfiles)
  //   .values(jsonData.profiles);
  // console.log("profilesIds", profilesIds);

  const profiles = await db.select().from(typeSafeProfiles);
  console.log("profiles", profiles);

  // // Insertar datos básicos
  // const typeSafeBasics = asDrizzleTable("Basics", Basics);
  // const basicsId = await db.insert(typeSafeBasics).values([jsonData.basics]);

  // console.log(basicsId);

  //   // Insertar datos de trabajo
  //   for (const item of jsonData.work) {
  //     await db.insert(Work).values(item);
  //   }

  //   // Insertar datos educativos
  //   for (const item of jsonData.education) {
  //     await db.insert(Education).values(item);
  //   }

  //   // Insertar habilidades
  //   for (const item of jsonData.skills) {
  //     await db.insert(Skills).values(item);
  //   }

  //   // Insertar intereses
  //   for (const item of jsonData.interests) {
  //     await db.insert(Interests).values(item);
  //   }

  //   // Insertar proyectos
  //   for (const item of jsonData.projects) {
  //     await db.insert(Projects).values(item);
  //   }

  //   // Insertar premios
  //   for (const item of jsonData.awards) {
  //     await db.insert(Awards).values(item);
  //   }

  //   // Insertar certificados
  //   for (const item of jsonData.certificates) {
  //     await db.insert(Certificates).values(item);
  //   }

  //   // Insertar publicaciones
  //   for (const item of jsonData.publications) {
  //     await db.insert(Publications).values(item);
  //   }
}
