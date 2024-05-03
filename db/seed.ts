import {
  db,
  like,
  not,
  eq,
  and,
  inArray,
  Awards,
  Basics,
  Certificates,
  Educations,
  Employers,
  Images,
  Institutions,
  Interests,
  Issuers,
  JobTypes,
  Keywords,
  KeywordsInterests,
  Languages,
  LanguagesUsers,
  Networks,
  NetworksUsers,
  Projects,
  Publications,
  Publishers,
  References,
  Skills,
  SkillsUsers,
  SkillsUsersKeywords,
  SoftSkills,
  TechnicalSkills,
  typeFiles,
  Users,
  Works,
  WorksSoftSkills,
  WorksTechnicalSkills,
} from "astro:db";

/**
# Estructura de la Base de Datos

## Tabla: Users
- **id:** text (Primary Key)
- **status:** text (Default: "active")
- **createdAt:** date (Default: NOW)
- **updatedAt:** date (Default: NOW)
- **username:** text (Unique)

## Tabla: Networks
- **id:** text (Primary Key)
- **status:** text (Default: "active")
- **createdAt:** date (Default: NOW)
- **updatedAt:** date (Default: NOW)
- **codeName:** text (Unique)
- **name:** text
- **url:** text

## Tabla: typeFiles
- **id:** text (Primary Key)
- **status:** text (Default: "active")
- **createdAt:** date (Default: NOW)
- **updatedAt:** date (Default: NOW)
- **codeName:** text (Unique)
- **name:** text
- **extension:** text
- **mime:** text
- **priority:** number

## Tabla: Institutions
- **id:** text (Primary Key)
- **status:** text (Default: "active")
- **createdAt:** date (Default: NOW)
- **updatedAt:** date (Default: NOW)
- **codeName:** text (Unique)
- **name:** text
- **url:** text
- **locationUrl:** text (Optional)
- **mapEmbed:** text (Optional)

## Tabla: Issuers
- **id:** text (Primary Key)
- **status:** text (Default: "active")
- **createdAt:** date (Default: NOW)
- **updatedAt:** date (Default: NOW)
- **codeName:** text (Unique)
- **name:** text
- **url:** text

## Tabla: Publishers
- **id:** text (Primary Key)
- **status:** text (Default: "active")
- **createdAt:** date (Default: NOW)
- **updatedAt:** date (Default: NOW)
- **codeName:** text (Unique)
- **name:** text
- **url:** text

## Tabla: Languages
- **id:** text (Primary Key)
- **status:** text (Default: "active")
- **createdAt:** date (Default: NOW)
- **updatedAt:** date (Default: NOW)
- **codeName:** text (Unique)
- **name:** text

## Tabla: Keywords
- **id:** text (Primary Key)
- **status:** text (Default: "active")
- **createdAt:** date (Default: NOW)
- **updatedAt:** date (Default: NOW)
- **codeName:** text (Unique)
- **name:** text

## Tabla: Interests
- **id:** text (Primary Key)
- **status:** text (Default: "active")
- **createdAt:** date (Default: NOW)
- **updatedAt:** date (Default: NOW)
- **codeName:** text (Unique)
- **name:** text
- **keywords:** json

## Tabla: Skills
- **id:** text (Primary Key)
- **status:** text (Default: "active")
- **createdAt:** date (Default: NOW)
- **updatedAt:** date (Default: NOW)
- **codeName:** text (Unique)
- **name:** text

## Tabla: Basics
- **id:** text (Primary Key)
- **status:** text (Default: "active")
- **createdAt:** date (Default: NOW)
- **updatedAt:** date (Default: NOW)
- **userId:** text (References: Users.id)
- **names:** text
- **lastName:** text
- **label:** text
- **image:** text
- **email:** text
- **phone:** text
- **url:** text
- **summary:** text
- **location:** json

## Tabla: Images
- **id:** text (Primary Key)
- **status:** text (Default: "active")
- **createdAt:** date (Default: NOW)
- **updatedAt:** date (Default: NOW)
- **userId:** text (References: Users.id)
- **type:** text
- **sort:** number
- **path:** json

## Tabla: NetworksUsers
- **id:** text (Primary Key)
- **status:** text (Default: "active")
- **createdAt:** date (Default: NOW)
- **updatedAt:** date (Default: NOW)
- **networkId:** text (References: Networks.id)
- **userId:** text (References: Users.id)
- **username:** text

## Tabla: Employers
- **id:** text (Primary Key)
- **status:** text (Default: "active")
- **createdAt:** date (Default: NOW)
- **updatedAt:** date (Default: NOW)
- **userId:** text (References: Users.id, Optional)
- **codeName:** text (Unique)
- **name:** text
- **url:** text
- **description:** text (Optional)
- **serviceStatus:** text (Default: "active")

## Tabla: JobTypes
- **id:** text (Primary Key)
- **status:** text (Default: "active")
- **createdAt:** date (Default: NOW)
- **updatedAt:** date (Default: NOW)
- **codeName:** text (Unique)
- **name:** text

## Tabla: Works
- **id:** text (Primary Key)
- **status:** text (Default: "active")
- **createdAt:** date (Default: NOW)
- **updatedAt:** date (Default: NOW)
- **userId:** text (References: Users.id)
- **employerId:** text (References: Employers.id, Optional)
- **codeName:** text (Unique)
- **name:** text
- **position:** text
- **startDate:** date
- **endDate:** date (Optional)
- **jobTypeId:** text (References: JobTypes.id)
- **summary:** text (Optional)
- **responsibilitiesNProjects:** json (Optional)
- **achievements:** json (Optional)

## Tabla: WorksTechnicalSkills
- **workId:** text (References: Works.id)
- **technicalSkillId:** text (References: Skills.id)

## Tabla: WorksSoftSkills
- **workId:** text (References: Works.id)
- **softSkillId:** text (References: SoftSkills.id)

## Tabla: Educations
- **id:** text (Primary Key)
- **status:** text (Default: "active")
- **createdAt:** date (Default: NOW)
- **updatedAt:** date (Default: NOW)
- **userId:** text (References: Users.id)
- **institutionId:** text (References: Institutions.id)
- **area:** text
- **learn:** text
- **studyType:** text
- **startDate:** date
- **endDate:** date

## Tabla: Awards
- **id:** text (Primary Key)
- **status:** text (Default: "active")
- **createdAt:** date (Default: NOW)
- **updatedAt:** date (Default: NOW)
- **userId:** text (References: Users.id)
- **title:** text
- **date:** date
- **awarder:** text
- **summary:** text
- **url:** text

## Tabla: Certificates
- **id:** text (Primary Key)
- **status:** text (Default: "active")
- **createdAt:** date (Default: NOW)
- **updatedAt:** date (Default: NOW)
- **userId:** text (References: Users.id)
- **title:** text
- **date:** date
- **IssuersId:** text (References: Issuers.id)
- **url:** text

## Tabla: Publications
- **id:** text (Primary Key)
- **status:** text (Default: "active")
- **createdAt:** date (Default: NOW)
- **updatedAt:** date (Default: NOW)
- **userId:** text (References: Users.id)
- **name:** text
- **publisherId:** text (References: Publishers.id)
- **releaseDate:** date
- **url:** text
- **summary:** text

## Tabla: LanguagesUsers
- **id:** text (Primary Key)
- **status:** text (Default: "active")
- **createdAt:** date (Default: NOW)
- **updatedAt:** date (Default: NOW)
- **userId:** text (References: Users.id)
- **languageId:** text (References: Languages.id)
- **fluency:** text

## Tabla: UsersInterests
- **userId:** text (References: Users.id)
- **interestId:** text (References: Interests.id)

## Tabla: Projects
- **id:** text (Primary Key)
- **status:** text (Default: "active")
- **createdAt:** date (Default: NOW)
- **updatedAt:** date (Default: NOW)
- **userId:** text (References: Users.id)
- **name:** text
- **description:** text
- **highlights:** json
- **url:** text
- **serviceStatus:** text (Default: "active")

## Tabla: References
- **id:** text (Primary Key)
- **status:** text (Default: "active")
- **createdAt:** date (Default: NOW)
- **updatedAt:** date (Default: NOW)
- **userId:** text (References: Users.id)
- **name:** text
- **reference:** text
- **position:** text
- **url:** text

## Tabla: SkillsUsers
- **id:** text (Primary Key)
- **status:** text (Default: "active")
- **createdAt:** date (Default: NOW)
- **updatedAt:** date (Default: NOW)
- **userId:** text (References: Users.id)
- **skillId:** text (References: Skills.id)
- **level:** text

## Tabla: SkillsUsersKeywords
- **id:** text (Primary Key)
- **status:** text (Default: "active")
- **createdAt:** date (Default: NOW)
- **updatedAt:** date (Default: NOW)
- **skillUserId:** text (References: SkillsUsers.id)
- **keywordId:** text (References: Keywords.id)
 */

// Aquí van tus datos JSON como un objeto JS directamente en el script para simplificar
const jsonData = {
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
  users: [
    "bypabloc",
    "pablo",
    "pablo-c",
    "pacg",
    "pabloacg",
    "pablo-contreras",
    "pablo-contreras-guevara",
  ],
  networks: {
    linkedin: {
      name: "LinkedIn",
      url: "https://linkedin.com/in",
    },
    github: {
      name: "GitHub",
      url: "https://github.com",
    },
  },
  typeFiles: {
    avif: {
      name: "AVIF",
      extension: "avif",
      mime: "image/avif",
      tag: "source",
      priority: 100,
    },
    webp: {
      name: "WebP",
      extension: "webp",
      mime: "image/webp",
      tag: "source",
      priority: 70,
    },
    jp2: {
      name: "JPEG2000",
      extension: "jp2",
      mime: "image/jpeg2000",
      tag: "source",
      priority: 50,
    },
    jpeg: {
      name: "JPEG",
      extension: "jpg",
      mime: "image/jpeg",
      tag: "img",
      priority: 20,
    },
  },
  institutions: {
    uptyab: {
      name: "Universidad Politécnica Territorial de Yaracuy Arístides Bastidas (UPTYAB)",
      url: "http://www.uptyab.edu.ve/web/index.php",
      locationUrl: "https://maps.app.goo.gl/kKW1WfPh1YmCb495A",
      mapEmbed:
        '<iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3925.130375903552!2d-68.75705208540283!3d10.3314499212098!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x8e80c8d433543891%3A0x5d6f1945598c22ac!2sUniversidad%20Polit%C3%A9cnica%20Territorial%20de%20Yaracuy%20Ar%C3%ADstides%20Bastidas%20(UPTYAB)!5e0!3m2!1ses!2spe!4v1714485380993!5m2!1ses!2spe" width="600" height="450" style="border:0;" allowfullscreen="" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe>',
    },
    youtube: {
      name: "YouTube",
      url: "https://youtube.com",
    },
    udemy: {
      name: "Udemy",
      url: "https://udemy.com",
    },
  },
  issuers: {
    udemy: {
      name: "Udemy",
      url: "https://udemy.com",
    },
    devtalles: {
      name: "DevTalles",
      url: "https://cursos.devtalles.com",
    },
  },
  publishers: {
    medium: {
      name: "Medium",
      link: "https://medium.com",
    },
  },
  languages: {
    es: {
      name: "Español",
      code: "es",
    },
    en: {
      name: "Inglés",
      code: "en",
    },
  },
  keywords: {
    programacion: {
      name: "Programación",
      list: ["programacion"],
    },
    desarrolloWeb: {
      name: "Desarrollo Web",
      list: ["desarrollo web"],
    },
    javascript: {
      name: "JavaScript",
      list: ["javascript"],
    },
    python: {
      name: "Python",
      list: ["python"],
    },
    vue: {
      name: "Vue",
      list: ["vue"],
    },
    nuxt: {
      name: "Nuxt",
      list: ["nuxt"],
    },
    django: {
      name: "Django",
      list: ["django"],
    },
    aws: {
      name: "AWS",
      list: ["aws"],
    },
    microservices: {
      name: "Microservices",
      list: ["microservices"],
    },
    microfrontends: {
      name: "Microfrontends",
      list: ["microfrontends"],
    },
    frontend: {
      name: "Frontend",
      list: ["frontend"],
    },
    laravel: {
      name: "Laravel",
      list: ["laravel"],
    },
    serverSideRendering: {
      name: "Server Side Rendering",
      list: ["server side rendering"],
    },
    metodologiasAgiles: {
      name: "Metodologías Ágiles",
      list: ["metodologias agiles"],
    },
    scrum: {
      name: "Scrum",
      list: ["scrum"],
    },
    shapeUp: {
      name: "Shape Up",
      list: ["shape up"],
    },
    java: {
      name: "Java",
      list: ["java"],
    },
    postgresql: {
      name: "Postgresql",
      list: ["postgresql"],
    },
    programacionOrientadaAObjetos: {
      name: "Programación Orientada A Objetos",
      list: ["programacion orientada a objetos"],
    },
    maquetacion: {
      name: "Maquetación",
      list: ["maquetacion"],
    },
    jquery: {
      name: "Jquery",
      list: ["jquery"],
    },
    html: {
      name: "Html",
      list: ["html"],
    },
    css: {
      name: "Css",
      list: ["css"],
    },
    php: {
      name: "Php",
      list: ["php"],
    },
    mysql: {
      name: "Mysql",
      list: ["mysql"],
    },
    git: {
      name: "Git",
      list: ["git"],
    },
    github: {
      name: "Github",
      list: ["github"],
    },
    bitbucket: {
      name: "Bitbucket",
      list: ["bitbucket"],
    },
    gitlab: {
      name: "Gitlab",
      list: ["gitlab"],
    },
    jira: {
      name: "Jira",
      list: ["jira"],
    },
    trello: {
      name: "Trello",
      list: ["trello"],
    },
    slack: {
      name: "Slack",
      list: ["slack"],
    },
    postman: {
      name: "Postman",
      list: ["postman"],
    },
    docker: {
      name: "Docker",
      list: ["docker"],
    },
    kubernetes: {
      name: "Kubernetes",
      list: ["kubernetes"],
    },
    linux: {
      name: "Linux",
      list: ["linux"],
    },
    mongodb: {
      name: "MongoDB",
      list: ["mongodb"],
    },
    nodejs: {
      name: "Node.js",
      list: ["nodejs"],
    },
    trabajoEnEquipo: {
      name: "Trabajo en Equipo",
      list: ["trabajo en equipo"],
    },
    aprendizajeDeErrores: {
      name: "Aprendizaje de Errores",
      list: ["aprendizaje de errores"],
    },
    comunicacion: {
      name: "Comunicación",
      list: ["comunicacion"],
    },
    liderazgo: {
      name: "Liderazgo",
      list: ["liderazgo"],
    },
    adaptabilidad: {
      name: "Adaptabilidad",
      list: ["adaptabilidad"],
    },
    resolucionDeProblemas: {
      name: "Resolución de Problemas",
      list: ["resolucion de problemas"],
    },
    creatividad: {
      name: "Creatividad",
      list: ["creatividad"],
    },
    pensamientoCritico: {
      name: "Pensamiento Crítico",
      list: ["pensamiento critico"],
    },
    gestionDelTiempo: {
      name: "Gestión del Tiempo",
      list: ["gestion del tiempo"],
    },
    empatia: {
      name: "Empatía",
      list: ["empatia"],
    },
    tomaDeDecisiones: {
      name: "Toma de Decisiones",
      list: ["toma de decisiones"],
    },
    aprendizajeContinuo: {
      name: "Aprendizaje Continuo",
      list: ["aprendizaje continuo"],
    },
    resiliencia: {
      name: "Resiliencia",
      list: ["resiliencia"],
    },
    proactividad: {
      name: "Proactividad",
      list: ["proactividad"],
    },
    capacidadDeAnalisis: {
      name: "Capacidad de Análisis",
      list: ["capacidad de analisis"],
    },
    capacidadDeSintesis: {
      name: "Capacidad de Síntesis",
      list: ["capacidad de sintesis"],
    },
    capacidadDeOrganizacion: {
      name: "Capacidad de Organización",
      list: ["capacidad de organizacion"],
    },
    capacidadDePlanificacion: {
      name: "Capacidad de Planificación",
      list: ["capacidad de planificacion"],
    },
    capacidadDeComunicacionEfectiva: {
      name: "Capacidad de Comunicación Efectiva",
      list: ["capacidad de comunicacion efectiva"],
    },
    capacidadDeNegociacion: {
      name: "Capacidad de Negociación",
      list: ["capacidad de negociacion"],
    },
    automatizacionDeTareas: {
      name: "Automatización de Tareas",
      list: ["automatizacion de tareas"],
    },
    innovacionTecnologica: {
      name: "Innovación Tecnológica",
      list: ["innovacion tecnologica"],
    },
    muayThai: {
      name: "Muay Thai",
      list: ["muay thai"],
    },
    karate: {
      name: "Karate",
      list: ["karate"],
    },
    fisica: {
      name: "Física",
      list: ["fisica"],
    },
    astronomia: {
      name: "Astronomía",
      list: ["astronomia"],
    },
    innovacionesTecnologicas: {
      name: "Innovaciones Tecnológicas",
      list: ["innovaciones tecnologicas"],
    },
    alimentacionSaludable: {
      name: "Alimentación Saludable",
      list: ["alimentacion saludable"],
    },
    comidaNoSaludable: {
      name: "Comida No Saludable",
      list: ["comida no saludable"],
    },
    exploracionGastronomica: {
      name: "Exploración Gastronómica",
      list: ["exploracion gastronomica"],
    },
    humor: {
      name: "Humor",
      list: ["humor"],
    },
    canalesDeHumor: {
      name: "Canales de Humor",
      list: ["canales de humor"],
    },
    backEnd: {
      name: "Backend",
      list: ["backend"],
    },
    fullStack: {
      name: "Fullstack",
      list: ["fullstack"],
    },
    spa: {
      name: "SPA",
      list: ["spa"],
    },
    vueCli: {
      name: "Vue CLI",
      list: ["vue cli"],
    },
    vueFramework: {
      name: "Vue Framework",
      list: ["vue framework"],
    },
    ssr: {
      name: "SSR",
      list: ["ssr"],
    },
    scripting: {
      name: "Scripting",
      list: ["scripting"],
    },
    webDevelopment: {
      name: "Web Development",
      list: ["web development"],
    },
    disenoResponsive: {
      name: "Diseño Responsive",
      list: ["diseno responsive"],
    },
    cloudServices: {
      name: "Cloud Services",
      list: ["cloud services"],
    },
    ec2: {
      name: "EC2",
      list: ["ec2"],
    },
    rds: {
      name: "RDS",
      list: ["rds"],
    },
    s3: {
      name: "S3",
      list: ["s3"],
    },
    ses: {
      name: "SES",
      list: ["ses"],
    },
    route53: {
      name: "Route 53",
      list: ["route 53"],
    },
    dynamodb: {
      name: "DynamoDB",
      list: ["dynamodb"],
    },
    controlDeVersiones: {
      name: "Control de Versiones",
      list: ["control de versiones"],
    },
    colaboracion: {
      name: "Colaboración",
      list: ["colaboracion"],
    },
    codigoFuente: {
      name: "Código Fuente",
      list: ["codigo fuente"],
    },
  },
  employers: [
    {
      codeName: "destacame",
      name: "Destacame",
      url: "https://destacame.cl",
    },
    {
      codeName: "appinteli",
      name: "AppInteli",
      url: "https://appinteli.com",
    },
    {
      codeName: "goodmeal",
      name: "GoodMeal",
      url: "https://www.goodmeal.app",
    },
    {
      codeName: "dibal",
      name: "Dibal",
      url: "https://dibal.pe",
    },
    {
      codeName: "cofasa",
      name: "Laboratorio Cofasa S.A.",
      url: "https://laboratoriocofasa.com",
    },
    {
      codeName: "iai",
      name: "Instituto Autónomo de Infraestructura (IAI)",
    },
    {
      codeName: "ipasme",
      name: "Ministerio de Educación 'IPASME'",
    },
    {
      codeName: "corpoelec",
      name: "CORPOELEC",
    },
  ],
  jobTypes: [
    {
      codeName: "fullTime",
      name: "Full Time",
    },
    {
      codeName: "partTime",
      name: "Part Time",
    },
    {
      codeName: "freelance",
      name: "Freelance",
    },
    {
      codeName: "internship",
      name: "Internship",
    },
    {
      codeName: "contract",
      name: "Contract",
    },
    {
      codeName: "personalProject",
      name: "Personal Project",
    },
  ],

  /**
    Interests
    Skills
    Basics
    Images
    NetworksUsers
    Works
    Educations
    Awards
    Certificates
    Publications
    LanguagesUsers
    Projects
    References
    SkillsUsers
  */
  interests: {
    desarrolladorYAutomatizacion: {
      name: "Desarrollador y Automatización",
      keywords: [
        "programacion",
        "automatizacionDeTareas",
        "innovacionTecnologica",
      ],
    },
    artesMarciales: {
      name: "Artes Marciales",
      keywords: ["muayThai", "karate"],
    },
    cienciaYTecnologia: {
      name: "Ciencia y Tecnología",
      keywords: ["fisica", "astronomia", "innovacionesTecnologicas"],
    },
    gastronomia: {
      name: "Gastronomía",
      keywords: [
        "alimentacionSaludable",
        "comidaNoSaludable",
        "exploracionGastronomica",
      ],
    },
    entretenimiento: {
      name: "Entretenimiento",
      keywords: ["humor", "canalesDeHumor"],
    },
  },
  skills: {
    vue: {
      name: "Vue",
      keywords: ["vue"],
    },
    nuxt: {
      name: "Nuxt",
      keywords: ["nuxt"],
    },
    python: {
      name: "Python",
      keywords: ["python"],
    },
    django: {
      name: "Django",
      keywords: ["django"],
    },
    aws: {
      name: "Aws",
      keywords: ["aws"],
    },
    microservices: {
      name: "Microservices",
      keywords: ["microservices"],
    },
    microfrontends: {
      name: "Microfrontends",
      keywords: ["microfrontends"],
    },
    frontend: {
      name: "Frontend",
      keywords: ["frontend"],
    },
    javascript: {
      name: "Javascript",
      keywords: ["javascript"],
    },
    laravel: {
      name: "Laravel",
      keywords: ["laravel"],
    },
    serverSideRendering: {
      name: "Server Side Rendering",
      keywords: ["serverSideRendering"],
    },
    metodologiasAgiles: {
      name: "Metodologías Ágiles",
      keywords: ["metodologiasAgiles"],
    },
    scrum: {
      name: "Scrum",
      keywords: ["scrum"],
    },
    shapeUp: {
      name: "Shape Up",
      keywords: ["shape up"],
    },
    java: {
      name: "Java",
      keywords: ["java"],
    },
    postgresql: {
      name: "Postgresql",
      keywords: ["postgresql"],
    },
    programacionOrientadaAObjetos: {
      name: "Programación Orientada A Objetos",
      keywords: ["programacion orientada a objetos"],
    },
    maquetacion: {
      name: "Maquetación",
      keywords: ["maquetacion"],
    },
    jquery: {
      name: "Jquery",
      keywords: ["jquery"],
    },
    html: {
      name: "Html",
      keywords: ["html"],
    },
    css: {
      name: "Css",
      keywords: ["css"],
    },
    php: {
      name: "Php",
      keywords: ["php"],
    },
    mysql: {
      name: "Mysql",
      keywords: ["mysql"],
    },
    git: {
      name: "Git",
      keywords: ["git"],
    },
    github: {
      name: "Github",
      keywords: ["github"],
    },
    bitbucket: {
      name: "Bitbucket",
      keywords: ["bitbucket"],
    },
    gitlab: {
      name: "Gitlab",
      keywords: ["gitlab"],
    },
    jira: {
      name: "Jira",
      keywords: ["jira"],
    },
    trello: {
      name: "Trello",
      keywords: ["trello"],
    },
    slack: {
      name: "Slack",
      keywords: ["slack"],
    },
    postman: {
      name: "Postman",
      keywords: ["postman"],
    },
    docker: {
      name: "Docker",
      keywords: ["docker"],
    },
    kubernetes: {
      name: "Kubernetes",
      keywords: ["kubernetes"],
    },
    linux: {
      name: "Linux",
      keywords: ["linux"],
    },
    mongodb: {
      name: "Mongodb",
      keywords: ["mongodb"],
    },
    "node js": {
      name: "Node.Js",
      keywords: ["node js"],
    },
    nodejs: {
      name: "Nodejs",
      keywords: ["nodejs"],
    },
    trabajoEnEquipo: {
      name: "Trabajo En Equipo",
      keywords: ["trabajo en equipo"],
    },
    aprendizajeDeErrores: {
      name: "Aprendizaje De Errores",
      keywords: ["aprendizaje de errores"],
    },
    comunicacion: {
      name: "Comunicación",
      keywords: ["comunicacion"],
    },
    liderazgo: {
      name: "Liderazgo",
      keywords: ["liderazgo"],
    },
    adaptabilidad: {
      name: "Adaptabilidad",
      keywords: ["adaptabilidad"],
    },
    resolucionDeProblemas: {
      name: "Resolución De Problemas",
      keywords: ["resolucion de problemas"],
    },
    creatividad: {
      name: "Creatividad",
      keywords: ["creatividad"],
    },
    pensamientoCritico: {
      name: "Pensamiento Crítico",
      keywords: ["pensamiento critico"],
    },
    gestionDelTiempo: {
      name: "Gestión Del Tiempo",
      keywords: ["gestion del tiempo"],
    },
    empatia: {
      name: "Empatía",
      keywords: ["empatia"],
    },
    tomaDeDecisiones: {
      name: "Toma De Decisiones",
      keywords: ["toma de decisiones"],
    },
    aprendizajeContinuo: {
      name: "Aprendizaje Continuo",
      keywords: ["aprendizaje continuo"],
    },
    resiliencia: {
      name: "Resiliencia",
      keywords: ["resiliencia"],
    },
    proactividad: {
      name: "Proactividad",
      keywords: ["proactividad"],
    },
    capacidadDeAnalisis: {
      name: "Capacidad De Análisis",
      keywords: ["capacidad de analisis"],
    },
    capacidadDeSintesis: {
      name: "Capacidad De Síntesis",
      keywords: ["capacidad de sintesis"],
    },
    capacidadDeOrganizacion: {
      name: "Capacidad De Organización",
      keywords: ["capacidad de organizacion"],
    },
    capacidadDePlanificacion: {
      name: "Capacidad De Planificación",
      keywords: ["capacidad de planificacion"],
    },
    capacidadDeComunicacionEfectiva: {
      name: "Capacidad De Comunicación Efectiva",
      keywords: ["capacidad de comunicacion efectiva"],
    },
    capacidadDeNegociacion: {
      name: "Capacidad De Negociación",
      keywords: ["capacidad de negociacion"],
    },
  },
  basics: {
    bypabloc: {
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
    },
  },
  profiles: {
    bypabloc: [
      {
        "networks-codeName": "linkedin",
        username: "bypabloc",
        url: "https://linkedin.com/in/bypabloc",
      },
      {
        "networks-codeName": "github",
        username: "bypabloc",
        url: "https://github.com/bypabloc",
      },
    ],
  },
  images: {
    bypabloc: [
      {
        type: "profile",
        sort: 1,
        path: [
          {
            "typeFiles-codeName": "avif",
            url: "https://images-bypabloc.s3.sa-east-1.amazonaws.com/cv/2.avif",
          },
          {
            "typeFiles-codeName": "webp",
            url: "https://images-bypabloc.s3.sa-east-1.amazonaws.com/cv/2.webp",
          },
          {
            "typeFiles-codeName": "jp2",
            url: "https://images-bypabloc.s3.sa-east-1.amazonaws.com/cv/2.jp2",
          },
          {
            "typeFiles-codeName": "jpeg",
            url: "https://images-bypabloc.s3.sa-east-1.amazonaws.com/cv/2.jpg",
          },
        ],
      },
      {
        type: "profile",
        sort: 2,
        path: [
          {
            "typeFiles-codeName": "avif",
            url: "https://images-bypabloc.s3.sa-east-1.amazonaws.com/cv/1.avif",
          },
          {
            "typeFiles-codeName": "webp",
            url: "https://images-bypabloc.s3.sa-east-1.amazonaws.com/cv/1.webp",
          },
          {
            "typeFiles-codeName": "jp2",
            url: "https://images-bypabloc.s3.sa-east-1.amazonaws.com/cv/1.jp2",
          },
          {
            "typeFiles-codeName": "jpeg",
            url: "https://images-bypabloc.s3.sa-east-1.amazonaws.com/cv/1.jpg",
          },
        ],
      },
    ],
  },
  networksUsers: {
    bypabloc: [
      {
        "networks-codeName": "linkedin",
        username: "bypabloc",
        url: "https://linkedin.com/in/bypabloc",
      },
      {
        "networks-codeName": "github",
        username: "bypabloc",
        url: "https://github.com/bypabloc",
      },
    ],
  },
  works: {
    bypabloc: [
      {
        "employers-codeName": "destacame",
        "jobType-codeName": "fullTime",
        codeName: "destacame-architect",
        name: "Destacame",
        position: "Arquitecto Frontend y Desarrollador de Microservicios",
        startDate: "2022-08-01",
        responsibilitiesNProjects: [
          "Desarrollo y aprendizaje continuo en tecnologías full stack, incluyendo Python, Django y microservices, así como en el modelo de microfrontends.",
          "Participación en el desarrollo de productos en el sector fintech, como un sistema para ayudar a los usuarios a saldar deudas en Chile y otro proyecto en México para ofrecer créditos con diferentes niveles a los usuarios.",
          "Asignación a un equipo de optimización, encargado de desarrollar soluciones para mejorar el trabajo en diferentes áreas de la empresa, como un administrador de campañas que automatiza procesos que antes eran manuales.",
        ],
        achievements: [
          "Contribuí significativamente al desarrollo de productos financieros, adquiriendo conocimientos específicos del mercado fintech.",
          "Desarrollé habilidades en la creación de soluciones automatizadas, mejorando la eficiencia de procesos internos en la empresa.",
          "Adaptación a cambios y desafíos, incluyendo reducciones de personal, manteniendo un enfoque en la entrega de soluciones técnicas y estratégicas en mi actual rol en el equipo de plataforma.",
        ],
      },
      {
        "employers-codeName": "destacame",
        "jobType-codeName": "fullTime",
        codeName: "destacame-frontend",
        name: "Destacame",
        position: "Desarrollador Web Frontend",
        url: "https://destacame.cl",
        startDate: "2021-12-27",
        endDate: "2022-08-01",
        responsibilitiesNProjects: [
          "Contratado inicialmente para trabajar en el área de frontend debido a habilidades sobresalientes demostradas en pruebas técnicas.",
          "Implementación de estándares y nuevas tecnologías en el desarrollo frontend, trabajando con Vue y Nuxt.js para mejorar la experiencia del usuario.",
          "Aprendizaje y aplicación progresiva de habilidades en el backend, enfocándome en Python y Django, para expandir mis capacidades como desarrollador full stack.",
        ],
        achievements: [
          "Mejoré significativamente la calidad y eficiencia del desarrollo frontend mediante la adopción de nuevas tecnologías y estándares.",
          "Desarrollé habilidades en Python y Django, superando los desafíos iniciales de falta de experiencia en estas tecnologías.",
          "Contribuí a la versatilidad y flexibilidad del equipo de desarrollo, adaptándome a necesidades cambiantes y aprendiendo nuevas habilidades.",
        ],
      },
      {
        "employers-codeName": "appinteli",
        "jobType-codeName": "personalProject",
        codeName: "appinteli",
        name: "AppInteli (Proyecto Personal)",
        position: "Co-fundador y Desarrollador",
        startDate: "2021-01-01",
        endDate: "2023-10-01",
        status: "inactive",
        responsibilitiesNProjects: [
          "Co-fundación y desarrollo de un ERP para tiendas pequeñas, enfocado en inventarios, ventas, compras y automatización de procesos como reportes y solicitudes de mercancía.",
          "Implementación de un e-commerce sencillo y accesible como parte del sistema, mejorando la interacción cliente-tienda.",
          "Atraer aproximadamente 10 clientes, manejando tanto el desarrollo como la parte comercial del proyecto.",
        ],
        achievements: [
          "Desarrollé habilidades en la creación y gestión de un proyecto empresarial desde cero, junto con la adquisición de conocimientos técnicos y comerciales.",
          "A pesar de que el proyecto no alcanzó el éxito esperado, obtuve experiencia valiosa en aspectos de desarrollo, ventas y gestión de un negocio.",
        ],
      },
      {
        "employers-codeName": "goodmeal",
        "jobType-codeName": "fullTime",
        codeName: "goodmeal",
        name: "GoodMeal",
        position: "Desarrollador Web Full Stack",
        url: "",
        startDate: "2021-05-01",
        endDate: "2021-12-01",
        responsibilitiesNProjects: [
          "Integración en una startup en crecimiento, trabajando bajo presión para satisfacer las demandas de los Project Managers y resolver bugs de manera eficiente",
          "Colaboración estrecha con un equipo talentoso, adoptando prácticas de Scrum, realizando reuniones diarias y mejorando las habilidades de trabajo en equipo",
          "Restructuración del frontend de la aplicación web, migrándolo a Vue 3 y utilizando tecnologías de vanguardia para mejorar la eficiencia y rendimiento",
        ],
        achievements: [
          "Superé los retos de trabajar en un ambiente de startup dinámico y en rápido crecimiento, entregando soluciones eficientes bajo plazos ajustados",
          "Lideré la migración y reestructuración del frontend hacia tecnologías más modernas, mejorando significativamente la experiencia de usuario y la eficiencia de la aplicación",
        ],
      },
      {
        "employers-codeName": "dibal",
        "jobType-codeName": "fullTime",
        codeName: "dibal",
        name: "Dibal",
        position: "Líder de Equipo de Desarrollo y Desarrollador",
        url: "https://dibal.pe",
        startDate: "2018-12-01",
        endDate: "2021-09-01",
        responsibilitiesNProjects: [
          "Primer desarrollador contratado en la startup, contribuyendo al desarrollo de un sistema web para múltiples restaurantes usando jQuery y Laravel.",
          "Liderazgo del equipo de desarrollo, organizando e implementando arquitecturas adaptadas a las necesidades cambiantes del negocio.",
          "Desarrollo de un e-commerce en Vue que integra la gestión de restaurantes con la experiencia del cliente, minimizando la interacción humana.",
          "Encargado del despliegue de aplicaciones en AWS, utilizando servicios como EC2, RDS, S3, Route 53, SES, AutoScaling y LoadBalancer.",
        ],
        achievements: [
          "Contribuí al crecimiento de la startup, adaptándome y respondiendo eficazmente a las necesidades de los clientes.",
          "Lideré con éxito un equipo de desarrollo, facilitando el crecimiento de la empresa y la implementación de soluciones tecnológicas avanzadas.",
          "Implementé soluciones de comercio electrónico que mejoraron significativamente la experiencia del cliente y la eficiencia operativa de los restaurantes asociados.",
        ],
      },
      {
        "employers-codeName": "cofasa",
        "jobType-codeName": "freelance",
        codeName: "cofasa",
        name: "LABORATORIO COFASA S.A.",
        position: "Desarrollador de Sistemas Web",
        url: "https://laboratoriocofasa.com/",
        startDate: "2017-01-01",
        endDate: "2018-11-28",
        responsibilitiesNProjects: [
          "Desarrollo de un sistema web para el monitoreo del proceso de producción, registrando paradas en las máquinas para análisis de productividad.",
          "Implementación del sistema en toda la empresa en red local, con acceso seguro mediante usuario y contraseña para cada empleado.",
          "Trabajo con tecnologías como jQuery y Laravel para crear una plataforma eficiente y fácil de usar.",
        ],
        achievements: [
          "Contribuí al aumento de la productividad mediante el análisis de datos generados por el sistema, permitiendo a la empresa tomar decisiones informadas para mejorar procesos.",
          "Entendí la verdadera importancia del trabajo en equipo, lo que resultó en una colaboración más efectiva y un proyecto exitoso.",
        ],
      },
      {
        "employers-codeName": "iai",
        "jobType-codeName": "freelance",
        codeName: "projects-degrees",
        name: "Freelance > Proyectos de Grado",
        position: "Líder, Arquitecto y Desarrollador",
        startDate: "2015-01-01",
        endDate: "2015-12-01",
        responsibilitiesNProjects: [
          "Reestructuración y finalización del proyecto de grado de dos equipos que enfrentaron dificultades técnicas.",
          "Dirección e implementación completa de las soluciones necesarias para cumplir con los objetivos del proyecto.",
        ],
        achievements: [
          "Completé el proyecto que dos equipos no pudieron en meses en una semana, instruyendo sobre cada implementación y sus razones.",
        ],
      },
      {
        "employers-codeName": "iai",
        "jobType-codeName": "freelance",
        codeName: "iai",
        name: "Freelance > Instituto Autónomo de Infraestructura (IAI)",
        position: "Líder de Desarrollo de Software y Arquitectura de Sistemas",
        startDate: "2015-01-01",
        endDate: "2015-12-01",
        responsibilitiesNProjects: [
          "Liderazgo en el desarrollo e implementación de un sistema informático para la gestión de obras.",
          "Diseño y desarrollo de una arquitectura de red con una PC como servidor para acceso centralizado a datos.",
        ],
        achievements: [
          "Diseño exitoso y desarrollo de la arquitectura del sistema, garantizando una implementación eficiente y adaptada.",
          "Mejora significativa en la gestión de obras y presupuestos a través de interfaces de usuario desarrolladas.",
        ],
      },
      {
        "employers-codeName": "ipasme",
        "jobType-codeName": "freelance",
        codeName: "ipasme",
        name: "Freelance > Ministerio de Educación 'IPASME'",
        position: "Desarrollador de software",
        startDate: "2014-01-01",
        endDate: "2014-12-01",
        responsibilitiesNProjects: [
          "Desarrollo e implementación de un sistema de gestión de historias médicas para pacientes.",
          "Creación de interfaces de escritorio en Java para Windows.",
        ],
        achievements: [
          "Aplicación de conceptos de POO y CRUDs en Java, mejorando mis habilidades técnicas.",
          "Mejora de habilidades de comunicación y levantamiento de requerimientos.",
        ],
      },
      {
        "employers-codeName": "corpoelec",
        "jobType-codeName": "freelance",
        codeName: "corpoelec",
        name: "Freelance > CORPOELEC",
        position: "Desarrollador web",
        startDate: "2013-01-01",
        endDate: "2013-12-01",
        responsibilitiesNProjects: [
          "Implementación y mantenimiento de un sistema de inventario usando PHP y jQuery.",
          "Desarrollo de funcionalidades CRUD y asociación de equipos a personas.",
        ],
        achievements: [
          "Implementación exitosa del sistema en tres estados del país, operando de manera offline.",
        ],
      },
    ],
  },
  educations: {
    bypabloc: [
      {
        "institutions-codeName": "uptyab",
        area: "Desarrollo Web",
        learn:
          "Cuando comencé a introducirme en el curso de programación en 2013, accedí a material gratuito y de paga que existía en ese momento en linea, hasta el día de hoy no paro de aprender",
        studyType: "course",
        startDate: "2013-04-01",
      },
      {
        "institutions-codeName": "youtube",
        area: "Desarrollo Web",
        learn:
          "En Udemy he tomado varios cursos de desarrollo web, entre ellos: JavaScript, React, Vue, Node, SQL, entre otros.",
        studyType: "course",
        startDate: "2013-04-01",
      },
      {
        "institutions-codeName": "udemy",
        area: "Ingeniería Informática",
        learn:
          "Estudié Ingeniería Informática en la UPTYAB, donde adquirí conocimientos en programación, bases de datos, redes, sistemas operativos, entre otros.",
        studyType: "bachelorDegree",
        startDate: "2011-03-01",
        endDate: "2016-03-01",
      },
    ],
  },
  awards: {
    bypabloc: [
      {
        title: "Premio a Innovador del año 2023 en Destacame",
        date: "2024-01-24",
        awarder: "Destacame",
        summary:
          "Por liderar la implementación de soluciones tecnológicas innovadoras en la empresa, mejorando significativamente la eficiencia operativa y la experiencia del usuario.",
        url: "https://heyzine.com/flip-book/cdc911b3d1.html",
      },
      {
        title: "Desafío Triple Alianza Lima",
        date: "2020-11-18",
        awarder: "Incubagraria, 1551, StartUpUni",
        summary:
          'Por haber obtenido el 1er lugar en el sector Comercio del "Desafío Triple Alianza COVID-19", esto sucedió en mi experiencia en DIBAL.',
        url: "https://1drv.ms/b/s!AoZaJmtucTrahbFAsRnMKiJDAxBlKg?e=9MKGjP",
      },
    ],
  },
  certificates: {
    bypabloc: [
      {
        name: "Docker - Guía práctica de uso para desarrolladores",
        date: "2023-04-20",
        "issuers-codeName": "DevTalles",
        url: "https://cursos.devtalles.com/certificates/f7qc3ju28w",
      },
      {
        name: "Node - Autenticación Rest con Clean Architecture",
        date: "2023-08-15",
        "issuers-codeName": "DevTalles",
        url: "https://cursos.devtalles.com/certificates/91cxyahzil",
      },
      {
        name: "Principios SOLID y Clean Code",
        date: "2023-11-05",
        "issuers-codeName": "DevTalles",
        url: "http://ude.my/UC-ddf92744-e69f-47ab-b28d-c4f7b569b7d4",
      },
      {
        name: "Next.js: El framework de React para producción",
        date: "2024-01-04",
        "issuers-codeName": "Udemy",
        url: "http://ude.my/UC-8297be13-d656-4e62-b64b-642819930c71",
      },
      {
        name: "React: De cero a experto ( Hooks y MERN )",
        date: "2023-11-13",
        "issuers-codeName": "Udemy",
        url: "http://ude.my/UC-6f8fa099-e631-459d-a139-989d441a1b21",
      },
      {
        name: "Vue.js - Intermedio: Lleva tus bases al siguiente nivel",
        date: "2023-03-22",
        "issuers-codeName": "Udemy",
        url: "http://ude.my/UC-b8d6554e-4cb9-49dd-becb-a5dbfdcf6f26",
      },
      {
        name: "Vue.js: De cero a experto",
        date: "2023-05-30",
        "issuers-codeName": "Udemy",
        url: "http://ude.my/UC-a217906e-84eb-40dc-9303-36de5b71e0cc",
      },
      {
        name: "SQL de cero: Tu guía práctica con PostgreSQL",
        date: "2023-02-12",
        "issuers-codeName": "Udemy",
        url: "http://ude.my/UC-afb98ee6-8704-4b20-9e1f-15bdacf2c76d",
      },
      {
        name: "NodeJS: De cero a experto",
        date: "2023-02-12",
        "issuers-codeName": "Udemy",
        url: "http://ude.my/UC-9acb44f1-27c6-402e-9dae-8a04bf3d424b",
      },
      {
        name: "Nest: Desarrollo backend escalable con Node",
        date: "2023-02-12",
        "issuers-codeName": "Udemy",
        url: "http://ude.my/UC-810baa94-7f51-4c54-b631-d62b4af77806",
      },
      {
        name: "JavaScript moderno: Guía para dominar el lenguaje",
        date: "2023-07-29",
        "issuers-codeName": "Udemy",
        url: "http://ude.my/UC-516bd9e6-59a0-4f28-b3bf-db2539d158d9",
      },
    ],
  },
  publications: {
    bypabloc: [
      {
        name: "Instalando Docker y Docker-compose en WSL2 Ubuntu sin Naufragar en el Intento",
        "publishers-codeName": "Medium",
        releaseDate: "2023-06-04",
        url: "https://bypablo.medium.com/un-viaje-épico-en-código-instalando-docker-y-docker-compose-en-wsl2-ubuntu-sin-naufragar-en-el-b21f38a9571",
        summary: "¿Como instalar Docker y Docker-compose en WSL2 sin fallar?",
      },
      {
        name: "Explorando 'type' e 'interface' en TypeScript: Un Enfoque en el Universo Marvel",
        "publishers-codeName": "Medium",
        releaseDate: "2023-05-28",
        url: "https://bypablo.medium.com/explorando-type-e-interface-en-typescript-un-enfoque-en-el-universo-marvel-4ad47317838e",
        summary:
          "¿Cuál es la diferencia entre 'type' e 'interface' en TypeScript? ¿Cómo se aplican en el Universo Marvel?",
      },
      {
        name: "JavaScript vs TypeScript: ¡El choque de titanes que desencadena una guerra de tipos!",
        "publishers-codeName": "Medium",
        releaseDate: "2023-05-29",
        url: "https://bypablo.medium.com/javascript-vs-typescript-el-choque-de-titanes-que-desencadena-una-guerra-de-tipos-dadc70c06766",
        summary:
          "¿Cuál es la diferencia entre JavaScript y TypeScript? ¿Cuál es mejor?",
      },
      {
        name: '¡Bienvenidos a TypeScript, no más "undefined"!',
        "publishers-codeName": "Medium",
        releaseDate: "2023-05-30",
        url: "https://bypablo.medium.com/bienvenidos-a-typescript-no-más-undefined-5e473f0f4670",
        summary:
          "¿Qué es TypeScript? ¿Cómo se usa? ¿Por qué es mejor que JavaScript?",
      },
      {
        name: "Dominando el Mundo de los Tipos en TypeScript",
        "publishers-codeName": "Medium",
        releaseDate: "2023-05-31",
        url: "https://bypablo.medium.com/dominando-el-mundo-de-los-tipos-en-typescript-e543eb42eb9c",
        summary:
          "¿Qué son los tipos en TypeScript? ¿Cómo se usan? ¿Por qué son importantes?",
      },
    ],
  },
  skillsUsers: {
    bypabloc: [
      {
        "skills-codeName": "JavaScript",
        level: "Master",
        keywords: ["desarrollo web", "frontend", "backend", "fullstack"],
      },
      {
        "skills-codeName": "Vue",
        level: "Master",
        keywords: ["desarrollo web", "frontend", "spa", "vue cli"],
      },
      {
        "skills-codeName": "Nuxt.js",
        level: "Avanzado",
        keywords: ["desarrollo web", "frontend", "vue framework", "ssr"],
      },
      {
        "skills-codeName": "Python",
        level: "Avanzado",
        keywords: ["backend", "scripting", "web development"],
      },
      {
        "skills-codeName": "CSS",
        level: "Master",
        keywords: ["desarrollo web", "frontend", "diseño responsive"],
      },
      {
        "skills-codeName": "HTML",
        level: "Master",
        keywords: ["desarrollo web", "frontend"],
      },
      {
        "skills-codeName": "AWS",
        level: "Intermedio",
        keywords: [
          "cloud services",
          "ec2",
          "rds",
          "s3",
          "ses",
          "route 53",
          "dynamodb",
        ],
      },
      {
        "skills-codeName": "Git",
        level: "Avanzado",
        keywords: ["control de versiones", "colaboración", "código fuente"],
      },
      {
        "skills-codeName": "GitHub",
        level: "Avanzado",
        keywords: [
          "control de versiones",
          "colaboración",
          "código fuente",
          "git",
        ],
      },
      {
        "skills-codeName": "Django",
        level: "Avanzado",
        keywords: ["desarrollo web", "backend", "python framework"],
      },
      {
        "skills-codeName": "Laravel",
        level: "Avanzado",
        keywords: ["desarrollo web", "backend", "php framework"],
      },
      {
        "skills-codeName": "jQuery",
        level: "Avanzado",
        keywords: ["desarrollo web", "frontend", "javascript library"],
      },
      {
        "skills-codeName": "MySQL",
        level: "Avanzado",
        keywords: [
          "bases de datos",
          "sql",
          "almacenamiento de datos",
          "backend",
        ],
      },
      {
        "skills-codeName": "MongoDB",
        level: "Intermedio",
        keywords: ["nosql", "bases de datos", "big data"],
      },
    ],
  },
  languagesUsers: {
    bypabloc: [
      {
        "languages-codeName": "es",
        fluency: "Nativo",
      },
      {
        "languages-codeName": "en",
        fluency: "Intermedio",
      },
    ],
  },
  projects: {
    bypabloc: [
      {
        name: "ERP para pequeñas tiendas",
        description:
          "Co-fundador y desarrollador de un ERP enfocado en la automatización de procesos de inventario, ventas y compras para pequeñas tiendas.",
        highlights: [
          "Desarrollo de una plataforma de comercio electrónico integrada",
          "Gestión de cliente y proyecto desde cero",
        ],
        url: "https://appinteli.com",
        serviceStatus: "inactive",
      },
    ],
  },
  references: {
    bypabloc: [
      {
        name: "Alan Vergara Bravo",
        reference: "Compañero de equipo",
        position: "Software Architect Developer",
        "employers-codeName": "destacame",
        url: "https://www.linkedin.com/in/alan-vergara-bravo-b17164145",
        scrappingRecommendation: {
          linkedin:
            "https://www.linkedin.com/in/bypabloc/details/recommendations",
          elementId:
            "profilePagedListComponent-ACoAACeoGgsB5cPxfqr-T2ylRvqy6qRWe6TgZfc-RECOMMENDATIONS-VIEW-DETAILS-profileTabSection-RECEIVED-RECOMMENDATIONS-NONE-es-ES-0",
        },
      },
      {
        name: "Alejandra Medina Briceño",
        reference: "Compañero de equipo",
        position: "Diseñadora UX/UI",
        "employers-codeName": "destacame",
        url: "https://www.linkedin.com/in/alejandra-medinab",
        scrappingRecommendation: {
          linkedin:
            "https://www.linkedin.com/in/bypabloc/details/recommendations",
          elementId:
            "profilePagedListComponent-ACoAACeoGgsB5cPxfqr-T2ylRvqy6qRWe6TgZfc-RECOMMENDATIONS-VIEW-DETAILS-profileTabSection-RECEIVED-RECOMMENDATIONS-NONE-es-ES-1",
        },
      },
      {
        name: "Baldomero Águila",
        reference: "Compañero de equipo",
        position: "Desarrollador Mobile",
        "employers-codeName": "destacame",
        url: "https://www.linkedin.com/in/baldomero",
      },
      {
        name: "Cristian Fuentes",
        reference: "Compañero de equipo",
        position: "Desarrollador Full Stack",
        "employers-codeName": "destacame",
        url: "https://www.linkedin.com/in/csfuente",
      },
      {
        name: "Helis Montes",
        reference: "Compañero de equipo",
        position: "Desarrollador Full Stack",
        "employers-codeName": "destacame",
        url: "https://www.linkedin.com/in/helis-montes",
      },
      {
        name: "Edder Ramírez",
        reference: "Compañero de equipo",
        position: "Desarrollador Full Stack",
        "employers-codeName": "destacame",
        url: "https://www.linkedin.com/in/edderleonardo",
      },
      {
        name: "José Namoc",
        reference: "Compañero de equipo",
        position: "Desarrollador Full Stack",
        "employers-codeName": "dibal",
        url: "https://www.linkedin.com/in/jose-namoc-lopez",
        scrappingRecommendation: {
          linkedin:
            "https://www.linkedin.com/in/bypabloc/details/recommendations",
          elementId:
            "profilePagedListComponent-ACoAACeoGgsB5cPxfqr-T2ylRvqy6qRWe6TgZfc-RECOMMENDATIONS-VIEW-DETAILS-profileTabSection-RECEIVED-RECOMMENDATIONS-NONE-es-ES-6",
        },
      },
      {
        name: "Jacnelly Colmenarez",
        reference: "Compañera de equipo",
        position: "UI/UX Designer",
        "employers-codeName": "dibal",
        url: "https://www.linkedin.com/in/jacnelly-colmenarez",
        scrappingRecommendation: {
          linkedin:
            "https://www.linkedin.com/in/bypabloc/details/recommendations",
          elementId:
            "profilePagedListComponent-ACoAACeoGgsB5cPxfqr-T2ylRvqy6qRWe6TgZfc-RECOMMENDATIONS-VIEW-DETAILS-profileTabSection-RECEIVED-RECOMMENDATIONS-NONE-es-ES-2",
        },
      },
      {
        name: "Felipe Rivera",
        reference: "Trabajé en la misma empresa",
        position: "Talent Acquisition Lead",
        url: "https://www.linkedin.com/in/frtavonatti",
      },
      {
        name: "Samuel Esponiza",
        reference:
          "Estudié en la misma universidad y trabajé en proyectos juntos",
        url: "https://www.linkedin.com/in/samuelespinozac",
        position: "Desarrollador Full Stack",
        scrappingRecommendation: {
          linkedin:
            "https://www.linkedin.com/in/bypabloc/details/recommendations",
          elementId:
            "profilePagedListComponent-ACoAACeoGgsB5cPxfqr-T2ylRvqy6qRWe6TgZfc-RECOMMENDATIONS-VIEW-DETAILS-profileTabSection-RECEIVED-RECOMMENDATIONS-NONE-es-ES-3",
        },
      },
    ],
  },

  /**
    UsersInterests
    WorksTechnicalSkills
    WorksSoftSkills
   */
  usersInterests: {
    bypabloc: [
      {
        "interests-codeName": "desarrolladorYAutomatizacion",
        name: "Desarrollo y Automatización",
        keywords: ["desarrollo de software", "automatización de procesos"],
      },
      {
        "interests-codeName": "artesMarciales",
        name: "Artes Marciales",
        keywords: ["karate", "kung fu", "taekwondo"],
      },
      {
        "interests-codeName": "cienciaYTecnologia",
        name: "Ciencia y Tecnología",
        keywords: ["tecnología", "ciencia", "innovación"],
      },
      {
        "interests-codeName": "gastronomia",
        name: "Gastronomía",
        keywords: ["cocina", "recetas", "comida"],
      },
      {
        "interests-codeName": "entretenimiento",
        name: "Entretenimiento",
        keywords: ["películas", "series", "videojuegos"],
      },
    ],
  },
  worksTechnicalSkills: {
    bypabloc: [
      {
        "works-codeName": "destacame-architect",
        "skills-codeName": "frontend",
      },
      {
        "works-codeName": "destacame-architect",
        "skills-codeName": "backend",
      },
      {
        "works-codeName": "destacame-architect",
        "skills-codeName": "aws",
      },
      {
        "works-codeName": "destacame-architect",
        "skills-codeName": "microservices",
      },
      {
        "works-codeName": "destacame-architect",
        "skills-codeName": "microfrontends",
      },
      {
        "works-codeName": "destacame-architect",
        "skills-codeName": "javascript",
      },
      {
        "works-codeName": "destacame-architect",
        "skills-codeName": "vue",
      },
      {
        "works-codeName": "destacame-architect",
        "skills-codeName": "nuxt",
      },
      {
        "works-codeName": "destacame-architect",
        "skills-codeName": "python",
      },
      {
        "works-codeName": "destacame-architect",
        "skills-codeName": "django",
      },
      {
        "works-codeName": "destacame-architect",
        "skills-codeName": "shapeUp",
      },
      {
        "works-codeName": "destacame-architect",
        "skills-codeName": "java",
      },
      {
        "works-codeName": "destacame-architect",
        "skills-codeName": "postgresql",
      },
      {
        "works-codeName": "destacame-frontend",
        "skills-codeName": "frontend",
      },
      {
        "works-codeName": "destacame-frontend",
        "skills-codeName": "backend",
      },
      {
        "works-codeName": "destacame-frontend",
        "skills-codeName": "aws",
      },
      {
        "works-codeName": "destacame-frontend",
        "skills-codeName": "microservices",
      },
      {
        "works-codeName": "destacame-frontend",
        "skills-codeName": "microfrontends",
      },
      {
        "works-codeName": "destacame-frontend",
        "skills-codeName": "javascript",
      },
      {
        "works-codeName": "destacame-frontend",
        "skills-codeName": "vue",
      },
      {
        "works-codeName": "destacame-frontend",
        "skills-codeName": "nuxt",
      },
      {
        "works-codeName": "destacame-frontend",
        "skills-codeName": "python",
      },
      {
        "works-codeName": "destacame-frontend",
        "skills-codeName": "django",
      },
      {
        "works-codeName": "destacame-frontend",
        "skills-codeName": "shapeUp",
      },
      {
        "works-codeName": "destacame-frontend",
        "skills-codeName": "java",
      },
      {
        "works-codeName": "destacame-frontend",
        "skills-codeName": "postgresql",
      },
      {
        "works-codeName": "appinteli",
        "skills-codeName": "frontend",
      },
      {
        "works-codeName": "appinteli",
        "skills-codeName": "backend",
      },
      {
        "works-codeName": "appinteli",
        "skills-codeName": "aws",
      },
      {
        "works-codeName": "appinteli",
        "skills-codeName": "microservices",
      },
      {
        "works-codeName": "appinteli",
        "skills-codeName": "microfrontends",
      },
      {
        "works-codeName": "appinteli",
        "skills-codeName": "javascript",
      },
      {
        "works-codeName": "appinteli",
        "skills-codeName": "vue",
      },
      {
        "works-codeName": "appinteli",
        "skills-codeName": "nuxt",
      },
      {
        "works-codeName": "appinteli",
        "skills-codeName": "python",
      },
      {
        "works-codeName": "appinteli",
        "skills-codeName": "django",
      },
      {
        "works-codeName": "appinteli",
        "skills-codeName": "shapeUp",
      },
      {
        "works-codeName": "appinteli",
        "skills-codeName": "java",
      },
      {
        "works-codeName": "appinteli",
        "skills-codeName": "postgresql",
      },
      {
        "works-codeName": "goodmeal",
        "skills-codeName": "frontend",
      },
      {
        "works-codeName": "goodmeal",
        "skills-codeName": "backend",
      },
      {
        "works-codeName": "goodmeal",
        "skills-codeName": "aws",
      },
      {
        "works-codeName": "goodmeal",
        "skills-codeName": "microservices",
      },
      {
        "works-codeName": "goodmeal",
        "skills-codeName": "microfrontends",
      },
      {
        "works-codeName": "goodmeal",
        "skills-codeName": "javascript",
      },
      {
        "works-codeName": "goodmeal",
        "skills-codeName": "vue",
      },
      {
        "works-codeName": "dibal",
        "skills-codeName": "frontend",
      },
      {
        "works-codeName": "dibal",
        "skills-codeName": "backend",
      },
      {
        "works-codeName": "dibal",
        "skills-codeName": "aws",
      },
      {
        "works-codeName": "dibal",
        "skills-codeName": "microservices",
      },
      {
        "works-codeName": "dibal",
        "skills-codeName": "microfrontends",
      },
      {
        "works-codeName": "dibal",
        "skills-codeName": "javascript",
      },
      {
        "works-codeName": "dibal",
        "skills-codeName": "vue",
      },
      {
        "works-codeName": "dibal",
        "skills-codeName": "nuxt",
      },
      {
        "works-codeName": "dibal",
        "skills-codeName": "python",
      },
      {
        "works-codeName": "dibal",
        "skills-codeName": "django",
      },
      {
        "works-codeName": "dibal",
        "skills-codeName": "shapeUp",
      },
      {
        "works-codeName": "dibal",
        "skills-codeName": "java",
      },
      {
        "works-codeName": "dibal",
        "skills-codeName": "postgresql",
      },
      {
        "works-codeName": "cofasa",
        "skills-codeName": "frontend",
      },
      {
        "works-codeName": "cofasa",
        "skills-codeName": "backend",
      },
      {
        "works-codeName": "cofasa",
        "skills-codeName": "aws",
      },
      {
        "works-codeName": "cofasa",
        "skills-codeName": "microservices",
      },
      {
        "works-codeName": "cofasa",
        "skills-codeName": "microfrontends",
      },
      {
        "works-codeName": "cofasa",
        "skills-codeName": "javascript",
      },
      {
        "works-codeName": "cofasa",
        "skills-codeName": "vue",
      },
      {
        "works-codeName": "cofasa",
        "skills-codeName": "nuxt",
      },
      {
        "works-codeName": "cofasa",
        "skills-codeName": "python",
      },
      {
        "works-codeName": "cofasa",
        "skills-codeName": "django",
      },
      {
        "works-codeName": "cofasa",
        "skills-codeName": "shapeUp",
      },
      {
        "works-codeName": "cofasa",
        "skills-codeName": "java",
      },
      {
        "works-codeName": "cofasa",
        "skills-codeName": "postgresql",
      },
      {
        "works-codeName": "projects-degrees",
        "skills-codeName": "frontend",
      },
      {
        "works-codeName": "projects-degrees",
        "skills-codeName": "backend",
      },
      {
        "works-codeName": "projects-degrees",
        "skills-codeName": "aws",
      },
      {
        "works-codeName": "projects-degrees",
        "skills-codeName": "microservices",
      },
      {
        "works-codeName": "projects-degrees",
        "skills-codeName": "microfrontends",
      },
      {
        "works-codeName": "projects-degrees",
        "skills-codeName": "javascript",
      },
      {
        "works-codeName": "projects-degrees",
        "skills-codeName": "vue",
      },
      {
        "works-codeName": "projects-degrees",
        "skills-codeName": "nuxt",
      },
    ],
  },
  worksSoftSkills: {
    bypabloc: [
      {
        "works-codeName": "destacame-architect",
        "skills-codeName": "trabajoEnEquipo",
      },
      {
        "works-codeName": "destacame-architect",
        "skills-codeName": "aprendizajeDeErrores",
      },
      {
        "works-codeName": "destacame-architect",
        "skills-codeName": "comunicacion",
      },
      {
        "works-codeName": "destacame-architect",
        "skills-codeName": "liderazgo",
      },
      {
        "works-codeName": "destacame-architect",
        "skills-codeName": "adaptabilidad",
      },
      {
        "works-codeName": "destacame-architect",
        "skills-codeName": "resolucionDeProblemas",
      },
      {
        "works-codeName": "destacame-architect",
        "skills-codeName": "creatividad",
      },
      {
        "works-codeName": "destacame-architect",
        "skills-codeName": "pensamientoCritico",
      },
      {
        "works-codeName": "destacame-architect",
        "skills-codeName": "gestionDelTiempo",
      },
      {
        "works-codeName": "destacame-architect",
        "skills-codeName": "empatia",
      },
      {
        "works-codeName": "destacame-architect",
        "skills-codeName": "tomaDeDecisiones",
      },
      {
        "works-codeName": "destacame-architect",
        "skills-codeName": "aprendizajeContinuo",
      },
      {
        "works-codeName": "destacame-architect",
        "skills-codeName": "resiliencia",
      },
      {
        "works-codeName": "destacame-architect",
        "skills-codeName": "proactividad",
      },
      {
        "works-codeName": "destacame-architect",
        "skills-codeName": "capacidadDeAnalisis",
      },
      {
        "works-codeName": "destacame-architect",
        "skills-codeName": "capacidadDeSintesis",
      },
      {
        "works-codeName": "destacame-architect",
        "skills-codeName": "capacidadDeOrganizacion",
      },
      {
        "works-codeName": "destacame-architect",
        "skills-codeName": "capacidadDePlanificacion",
      },
      {
        "works-codeName": "destacame-architect",
        "skills-codeName": "capacidadDeComunicacionEfectiva",
      },
      {
        "works-codeName": "destacame-architect",
        "skills-codeName": "capacidadDeNegociacion",
      },
      {
        "works-codeName": "destacame-frontend",
        "skills-codeName": "trabajoEnEquipo",
      },
      {
        "works-codeName": "destacame-frontend",
        "skills-codeName": "aprendizajeDeErrores",
      },
      {
        "works-codeName": "destacame-frontend",
        "skills-codeName": "comunicacion",
      },
      {
        "works-codeName": "destacame-frontend",
        "skills-codeName": "liderazgo",
      },
      {
        "works-codeName": "destacame-frontend",
        "skills-codeName": "adaptabilidad",
      },
      {
        "works-codeName": "destacame-frontend",
        "skills-codeName": "resolucionDeProblemas",
      },
      {
        "works-codeName": "destacame-frontend",
        "skills-codeName": "creatividad",
      },
      {
        "works-codeName": "destacame-frontend",
        "skills-codeName": "pensamientoCritico",
      },
      {
        "works-codeName": "destacame-frontend",
        "skills-codeName": "gestionDelTiempo",
      },
      {
        "works-codeName": "destacame-frontend",
        "skills-codeName": "empatia",
      },
      {
        "works-codeName": "destacame-frontend",
        "skills-codeName": "tomaDeDecisiones",
      },
      {
        "works-codeName": "destacame-frontend",
        "skills-codeName": "aprendizajeContinuo",
      },
      {
        "works-codeName": "destacame-frontend",
        "skills-codeName": "resiliencia",
      },
    ],
  },
};

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
  const listUsers = await db.select().from(Users);
  let notRegisteredUsers = await db
    .select()
    .from(Users)
    .where(and(inArray(Users.username, jsonData.users)));

  for (const user of notRegisteredUsers) {
    const { username } = user;
    jsonData.users.splice(jsonData.users.indexOf(username), 1);
  }
  if (jsonData.users.length) {
    requestList.push(
      db.insert(Users).values(
        jsonData.users.map((username) => ({
          username,
        }))
      )
    );
    await db.batch(requestList);
    notRegisteredUsers = await db.select().from(Users);
  }
  console.log("notRegisteredUsers", notRegisteredUsers);
  // requestList.push(
  //   db.insert(Users).values(
  //     jsonData.users.map((username) => ({
  //       username,
  //     }))
  //   )
  // );
  // await db.batch(requestList);
  // notRegisteredUsers = await db
  //   .select()
  //   .from(Users)
  //   .where(and(inArray(Users.username, jsonData.users)));
  // console.log("notRegisteredUsers", notRegisteredUsers);
  // jsonData.networks.forEach((network) => {
  //   requestList.push(
  //     db
  //       .select()
  //       .from(Networks)
  //       .where(like(Networks.codeName, `%${network.codeName}%`))
  //   );
  // });
  // const resNetworks = await db.batch(requestList);
  // console.log("resNetworks", resNetworks);
  // if (resNetworks.length) {
  //   const createNetworks: any[] = [];
  //   resNetworks.forEach((res, index) => {
  //     if (!res.length) {
  //       createNetworks.push(
  //         db.insert(Networks).values(jsonData.networks[index])
  //       );
  //     }
  //   });
  //   // const resCreateNetworks = await db.batch(createNetworks);
  //   // console.log("resCreateNetworks", resCreateNetworks);
  // }
  /**
    Networks
    Users
    typeFiles
    Institutions
    Issuers
    Publishers
    Languages
    Keywords
    Interests
    Skills

    ------

    TechnicalSkills
    SoftSkills
    Basics
    Images
    NetworksUsers
    Works
    Educations
    Awards
    Certificates
    Publications
    LanguagesUsers
    KeywordsInterests
    Projects
    References
    SkillsUsers

    ------

    WorksTechnicalSkills
    WorksSoftSkills
    SkillsUsersKeywords
   */
}
