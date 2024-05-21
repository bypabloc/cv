export default {
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
      attributesTypes
    */
  users: [
    {
      username: "bypabloc",
    },
  ],
  groupsFiles: [
    {
      codeName: "profile",
      name: "Profile",
    },
    {
      codeName: "projects",
      name: "Projects",
    },
  ],
  networks: [
    {
      codeName: "phone",
      name: "Teléfono",
      url: "tel",
      config: {
        description:
          "Comunicarse con {attributes.names.value} {attributes.lastName.value} a través de {name}",
        icon: {
          default: "i-material-symbols-phone-enabled-outline",
          dark: "i-material-symbols-phone-enabled",
        },
        web: {
          visible: true,
          template: "{url}:{contactInfo}",
        },
        print: {
          visible: false,
          template: "{contactInfo}",
        },
      },
    },
    {
      codeName: "email",
      name: "Correo Electrónico",
      url: "mailto",
      config: {
        description:
          "Comunicarse con {attributes.names.value} {attributes.lastName.value} a través del {name}",
        icon: {
          default: "i-material-symbols-mail-outline",
          dark: "i-material-symbols-mail",
        },
        web: {
          visible: true,
          template: "{url}:{contactInfo}",
        },
        print: {
          visible: true,
          template: "{contactInfo}",
        },
      },
    },
    {
      codeName: "whatsapp",
      name: "WhatsApp",
      url: "https://wa.me",
      config: {
        icon: {
          default: "i-mdi-whatsapp",
          dark: "i-mdi-whatsapp",
        },
        description:
          "Comunicarse con {attributes.names.value} {attributes.lastName.value} a través {name}",
        web: {
          visible: true,
          template: "{url}/{contactInfo}",
        },
        print: {
          visible: true,
          template: "+{contactInfo}",
        },
      },
    },
    {
      codeName: "linkedin",
      name: "LinkedIn",
      url: "https://linkedin.com/in",
      config: {
        description:
          "Visitar el perfil de {attributes.names.value} {attributes.lastName.value} en {name}",
        icon: {
          default: "i-ant-design-linkedin-outlined",
          dark: "i-ant-design-linkedin-filled",
        },
        web: {
          visible: true,
          template: "{url}/{contactInfo}",
        },
        print: {
          visible: true,
          link: true,
          template: "{url}/{contactInfo}",
        },
      },
    },
    {
      codeName: "github",
      name: "GitHub",
      url: "https://github.com",
      config: {
        description:
          "Visitar el perfil de {attributes.names.value} {attributes.lastName.value} en {name}",
        icon: {
          default: "i-ant-design-github-outlined",
          dark: "i-ant-design-github-filled",
        },
        web: {
          visible: true,
          template: "{url}/{contactInfo}",
        },
        print: {
          visible: true,
          link: true,
          template: "{url}/{contactInfo}",
        },
      },
    },
  ],
  networksUsers: [
    {
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        networkId: {
          table: "networks",
          field: "codeName",
          value: "phone",
        },
      },
      contactInfo: "51918490148",
    },
    {
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        networkId: {
          table: "networks",
          field: "codeName",
          value: "whatsapp",
        },
      },
      contactInfo: "51918490148",
    },
    {
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        networkId: {
          table: "networks",
          field: "codeName",
          value: "email",
        },
      },
      contactInfo: "pacg1991@gmail.com",
    },
    {
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        networkId: {
          table: "networks",
          field: "codeName",
          value: "linkedin",
        },
      },
      contactInfo: "bypabloc",
    },
    {
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        networkId: {
          table: "networks",
          field: "codeName",
          value: "github",
        },
      },
      contactInfo: "bypabloc",
    },
  ],
  typeFiles: [
    {
      codeName: "avif",
      name: "AVIF",
      extension: "avif",
      mime: "image/avif",
      tag: "source",
      priority: 100,
    },
    {
      codeName: "webp",
      name: "WebP",
      extension: "webp",
      mime: "image/webp",
      tag: "source",
      priority: 70,
    },
    {
      codeName: "jp2",
      name: "JPEG2000",
      extension: "jp2",
      mime: "image/jpeg2000",
      tag: "source",
      priority: 50,
    },
    {
      codeName: "jpeg",
      name: "JPEG",
      extension: "jpg",
      mime: "image/jpeg",
      tag: "img",
      priority: 20,
    },
  ],
  institutions: [
    {
      codeName: "uptyab",
      name: "Universidad Politécnica Territorial de Yaracuy Arístides Bastidas (UPTYAB)",
      url: "http://www.uptyab.edu.ve/web/index.php",
      locationUrl: "https://maps.app.goo.gl/kKW1WfPh1YmCb495A",
      mapEmbed:
        '<iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3925.130375903552!2d-68.75705208540283!3d10.3314499212098!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x8e80c8d433543891%3A0x5d6f1945598c22ac!2sUniversidad%20Polit%C3%A9cnica%20Territorial%20de%20Yaracuy%20Ar%C3%ADstides%20Bastidas%20(UPTYAB)!5e0!3m2!1ses!2spe!4v1714485380993!5m2!1ses!2spe" width="600" height="450" style="border:0;" allowfullscreen="" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe>',
    },
    {
      codeName: "youtube",
      name: "YouTube",
      url: "https://youtube.com",
    },
    {
      codeName: "udemy",
      name: "Udemy",
      url: "https://udemy.com",
    },
  ],
  issuers: [
    {
      codeName: "udemy",
      name: "Udemy",
      url: "https://udemy.com",
    },
    {
      codeName: "devtalles",
      name: "DevTalles",
      url: "https://cursos.devtalles.com",
    },
  ],
  publishers: [
    {
      codeName: "medium",
      name: "Medium",
      url: "https://medium.com",
    },
  ],
  languages: [
    {
      codeName: "es",
      name: "Español",
      code: "es",
    },
    {
      codeName: "en",
      name: "Inglés",
      code: "en",
    },
  ],
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
  keywords: [
    {
      codeName: "devops",
      name: "DevOps",
      keys: ["devops"],
    },
    {
      codeName: "docker",
      name: "Docker",
      keys: ["docker"],
    },
    {
      codeName: "data-analysis",
      name: "Data Analysis",
      keys: ["data analysis", "data-analysis"],
    },
    {
      codeName: "kubernetes",
      name: "Kubernetes",
      keys: ["kubernetes"],
    },
    {
      codeName: "sql",
      name: "SQL",
      keys: ["sql"],
    },
    {
      codeName: "node",
      name: "Node.js",
      keys: ["node", "nodejs"],
    },
    {
      codeName: "react",
      name: "React",
      keys: ["react"],
    },
    {
      codeName: "javascript",
      name: "JavaScript",
      keys: ["javascript", "js"],
    },
    // destácame - arquitecto frontend
    {
      codeName: "python",
      name: "Python",
      keys: ["python", "py"],
    },
    {
      codeName: "django",
      name: "Django",
      keys: ["django"],
    },
    {
      codeName: "microservices",
      name: "Microservices",
      keys: ["microservices"],
    },
    {
      codeName: "aws",
      name: "AWS",
      keys: ["aws", "amazon web services"],
    },
    {
      codeName: "frontend-architecture",
      name: "Frontend Architecture",
      keys: ["frontend architecture", "frontend-architecture"],
    },

    // destácame - desarrollador web frontend
    {
      codeName: "vue",
      name: "Vue.js",
      keys: ["vue", "vuejs"],
    },
    {
      codeName: "nuxt",
      name: "Nuxt.js",
      keys: ["nuxt", "nuxtjs"],
    },
    {
      codeName: "typescript",
      name: "TypeScript",
      keys: ["typescript", "ts"],
    },
    {
      codeName: "frontend-development",
      name: "Frontend Development",
      keys: ["frontend development", "frontend-development"],
    },
    {
      codeName: "web-development",
      name: "Web Development",
      keys: ["web development", "web-development"],
    },

    // appinteli - proyecto personal
    {
      codeName: "erp",
      name: "ERP",
      keys: ["erp"],
    },
    {
      codeName: "project-management",
      name: "Project Management",
      keys: ["project management", "project-management"],
    },
    {
      codeName: "ecommerce",
      name: "E-commerce",
      keys: ["ecommerce", "e-commerce"],
    },
    {
      codeName: "automation",
      name: "Automation",
      keys: ["automation"],
    },
    {
      codeName: "startup",
      name: "Startup",
      keys: ["startup"],
    },

    // goodmeal - desarrollador web full stack
    {
      codeName: "full-stack-development",
      name: "Full Stack Development",
      keys: ["full stack development", "full-stack-development"],
    },
    {
      codeName: "vue3",
      name: "Vue 3",
      keys: ["vue3", "vue 3"],
    },
    {
      codeName: "scrum",
      name: "Scrum",
      keys: ["scrum"],
    },
    {
      codeName: "bug-fixing",
      name: "Bug Fixing",
      keys: ["bug fixing", "bug-fixing"],
    },
    {
      codeName: "web-application",
      name: "Web Application",
      keys: ["web application", "web-application"],
    },

    // dibal - líder de equipo de desarrollo
    {
      codeName: "team-leadership",
      name: "Team Leadership",
      keys: ["team leadership", "team-leadership"],
    },
    {
      codeName: "aws-deployment",
      name: "AWS Deployment",
      keys: ["aws deployment", "aws-deployment"],
    },
    {
      codeName: "laravel",
      name: "Laravel",
      keys: ["laravel"],
    },
    {
      codeName: "system-architecture",
      name: "System Architecture",
      keys: ["system architecture", "system-architecture"],
    },
    {
      codeName: "microfrontend",
      name: "Microfrontend",
      keys: ["microfrontend"],
    },

    // cofasa - desarrollador de sistemas web
    {
      codeName: "production-monitoring",
      name: "Production Monitoring",
      keys: ["production monitoring", "production-monitoring"],
    },
    {
      codeName: "productivity-analysis",
      name: "Productivity Analysis",
      keys: ["productivity analysis", "productivity-analysis"],
    },
    {
      codeName: "local-network",
      name: "Local Network",
      keys: ["local network", "local-network"],
    },
    {
      codeName: "jquery",
      name: "jQuery",
      keys: ["jquery", "jq"],
    },
    {
      codeName: "web-platform",
      name: "Web Platform",
      keys: ["web platform", "web-platform"],
    },

    // iai - freelance proyectos de grado
    {
      codeName: "graduation-project",
      name: "Graduation Project",
      keys: ["graduation project", "graduation-project"],
    },
    {
      codeName: "technical-challenges",
      name: "technical Challenges",
      keys: ["technical challenges", "technical-challenges"],
    },
    {
      codeName: "project-direction",
      name: "Project Direction",
      keys: ["project direction", "project-direction"],
    },
    {
      codeName: "solution-implementation",
      name: "Solution Implementation",
      keys: ["solution implementation", "solution-implementation"],
    },
    {
      codeName: "team-collaboration",
      name: "Team Collaboration",
      keys: ["team collaboration", "team-collaboration"],
    },

    // iai - freelance desarrollo de software y arquitectura
    {
      codeName: "infrastructure-management",
      name: "Infrastructure Management",
      keys: ["infrastructure management", "infrastructure-management"],
    },
    {
      codeName: "network-architecture",
      name: "Network Architecture",
      keys: ["network architecture", "network-architecture"],
    },
    {
      codeName: "project-planning",
      name: "Project Planning",
      keys: ["project planning", "project-planning"],
    },
    {
      codeName: "work-management",
      name: "Work Management",
      keys: ["work management", "work-management"],
    },
    {
      codeName: "budget-management",
      name: "Budget Management",
      keys: ["budget management", "budget-management"],
    },

    // ipasme - desarrollador de software
    {
      codeName: "medical-records",
      name: "Medical Records",
      keys: ["medical records", "medical-records"],
    },
    {
      codeName: "desktop-application",
      name: "Desktop Application",
      keys: ["desktop application", "desktop-application"],
    },
    {
      codeName: "java",
      name: "Java",
      keys: ["java"],
    },
    {
      codeName: "object-oriented-programming",
      name: "Object Oriented Programming",
      keys: ["object oriented programming", "object-oriented-programming"],
    },
    {
      codeName: "requirements-gathering",
      name: "Requirements Gathering",
      keys: ["requirements gathering", "requirements-gathering"],
    },

    // corpoelec - desarrollador web
    {
      codeName: "inventory-management",
      name: "Inventory Management",
      keys: ["inventory management", "inventory-management"],
    },
    {
      codeName: "php",
      name: "PHP",
      keys: ["php"],
    },
    {
      codeName: "crud",
      name: "CRUD",
      keys: ["crud"],
    },
    {
      codeName: "offline-system",
      name: "Offline System",
      keys: ["offline system", "offline-system"],
    },
    {
      codeName: "asset-management",
      name: "Asset Management",
      keys: ["asset management", "asset-management"],
    },

    {
      codeName: "machine-learning",
      name: "Machine Learning",
      keys: ["machine learning", "ml"],
    },
    {
      codeName: "cloud-computing",
      name: "Cloud Computing",
      keys: ["cloud computing", "cloud-computing"],
    },
    {
      codeName: "blockchain",
      name: "Blockchain",
      keys: ["blockchain"],
    },
    {
      codeName: "ai-chatbots",
      name: "AI Chatbots",
      keys: ["ai chatbots", "chatbots"],
    },
    {
      codeName: "internet-of-things",
      name: "Internet of Things (IoT)",
      keys: ["internet of things", "iot"],
    },
    {
      codeName: "edge-computing",
      name: "Edge Computing",
      keys: ["edge computing", "edge-computing"],
    },
    {
      codeName: "mobile-development",
      name: "Mobile Development",
      keys: ["mobile development", "mobile-development"],
    },
    {
      codeName: "game-development",
      name: "Game Development",
      keys: ["game development", "game-development"],
    },
    {
      codeName: "security-engineering",
      name: "Security Engineering",
      keys: ["security engineering", "security-engineering"],
    },
    {
      codeName: "robotics",
      name: "Robotics",
      keys: ["robotics"],
    },
    {
      codeName: "ar-vr",
      name: "AR/VR",
      keys: ["ar", "vr", "augmented reality", "virtual reality"],
    },
  ],
  interests: [
    {
      codeName: "devops",
      name: "DevOps",
    },
    {
      codeName: "bot-creation",
      name: "Creación de Bots",
    },
    {
      codeName: "scraping",
      name: "Scraping",
    },
    {
      codeName: "kubernetes",
      name: "Kubernetes",
    },
    {
      codeName: "machine-learning",
      name: "Machine Learning",
    },
    {
      codeName: "cloud-computing",
      name: "Cloud Computing",
    },
    {
      codeName: "blockchain",
      name: "Blockchain",
    },
    {
      codeName: "ai-chatbots",
      name: "AI Chatbots",
    },
    {
      codeName: "microservices",
      name: "Microservicios",
    },
    {
      codeName: "internet-of-things",
      name: "Internet of Things (IoT)",
    },
    {
      codeName: "frontend-development",
      name: "Frontend Development",
    },
    {
      codeName: "backend-development",
      name: "Backend Development",
    },
    {
      codeName: "data-engineering",
      name: "Data Engineering",
    },
    {
      codeName: "serverless-computing",
      name: "Serverless Computing",
    },
    {
      codeName: "edge-computing",
      name: "Edge Computing",
    },
    {
      codeName: "mobile-development",
      name: "Mobile Development",
    },
    {
      codeName: "game-development",
      name: "Game Development",
    },
    {
      codeName: "security-engineering",
      name: "Security Engineering",
    },
    {
      codeName: "robotics",
      name: "Robotics",
    },
    {
      codeName: "ar-vr",
      name: "AR/VR",
    },
  ],
  skills: [
    {
      codeName: "docker",
      name: "Docker",
      description:
        "Plataforma de contenedores para el desarrollo de aplicaciones.",
      type: "technical",
    },
    {
      codeName: "kubernetes",
      name: "Kubernetes",
      description:
        "Orquestador de contenedores para el despliegue de aplicaciones.",
      type: "technical",
    },
    {
      codeName: "react",
      name: "React",
      description:
        "Framework JavaScript para la creación de interfaces de usuario.",
      type: "technical",
    },
    {
      codeName: "node",
      name: "Node.js",
      description:
        "Entorno de ejecución de JavaScript para el desarrollo de aplicaciones backend.",
      type: "technical",
    },
    {
      codeName: "sql",
      name: "SQL",
      description: "Lenguaje de consulta estructurado para bases de datos.",
      type: "technical",
    },
    {
      codeName: "python",
      name: "Python",
      description:
        "Lenguaje de programación utilizado en el desarrollo de microservicios.",
      type: "technical",
    },
    {
      codeName: "django",
      name: "Django",
      description:
        "Framework web para Python utilizado en el desarrollo de backend.",
      type: "technical",
    },
    {
      codeName: "microservices",
      name: "Microservices",
      description:
        "Arquitectura de microservicios para el desarrollo de aplicaciones escalables.",
      type: "technical",
    },
    {
      codeName: "aws",
      name: "AWS",
      description:
        "Plataforma de servicios en la nube utilizada para implementación y despliegue.",
      type: "technical",
    },
    {
      codeName: "frontend-architecture",
      name: "Frontend Architecture",
      description: "Diseño de la arquitectura de la aplicación frontend.",
      type: "technical",
    },
    {
      codeName: "optimization",
      name: "Optimization",
      description: "Mejora de la eficiencia y el rendimiento de los sistemas.",
      type: "technical",
    },
    {
      codeName: "automation",
      name: "Automation",
      description: "Automatización de procesos para mejorar la eficiencia.",
      type: "technical",
    },
    {
      codeName: "fintech",
      name: "Fintech",
      description: "Conocimiento específico del mercado financiero.",
      type: "soft",
    },
    {
      codeName: "strategic-planning",
      name: "Strategic Planning",
      description: "Planificación estratégica para la entrega de soluciones.",
      type: "soft",
    },
    {
      codeName: "vue",
      name: "Vue.js",
      description:
        "Framework JavaScript para la creación de interfaces de usuario.",
      type: "technical",
    },
    {
      codeName: "nuxt",
      name: "Nuxt.js",
      description: "Framework de desarrollo web basado en Vue.js.",
      type: "technical",
    },
    {
      codeName: "typescript",
      name: "TypeScript",
      description: "Lenguaje de programación tipado.",
      type: "technical",
    },
    {
      codeName: "frontend-development",
      name: "Frontend Development",
      description:
        "Desarrollo frontend para mejorar la experiencia del usuario.",
      type: "technical",
    },
    {
      codeName: "web-development",
      name: "Web Development",
      description: "Desarrollo de aplicaciones web.",
      type: "technical",
    },
    {
      codeName: "quality-improvement",
      name: "Quality Improvement",
      description: "Mejora de la calidad en el desarrollo de software.",
      type: "technical",
    },
    {
      codeName: "backend-development",
      name: "Backend Development",
      description: "Desarrollo de aplicaciones backend con Python y Django.",
      type: "technical",
    },
    {
      codeName: "learning-agility",
      name: "Learning Agility",
      description: "Habilidad para aprender y aplicar nuevas tecnologías.",
      type: "soft",
    },
    {
      codeName: "erp",
      name: "ERP",
      description:
        "Desarrollo de sistemas de planificación de recursos empresariales.",
      type: "technical",
    },
    {
      codeName: "ecommerce",
      name: "E-commerce",
      description: "Desarrollo de soluciones de comercio electrónico.",
      type: "technical",
    },
    {
      codeName: "startup",
      name: "Startup",
      description: "Gestión y desarrollo de startups.",
      type: "soft",
    },
    {
      codeName: "technical-knowledge",
      name: "technical Knowledge",
      description: "Conocimientos técnicos en múltiples áreas.",
      type: "technical",
    },
    {
      codeName: "sales",
      name: "Sales",
      description: "Manejo de ventas y clientes.",
      type: "soft",
    },
    {
      codeName: "business-management",
      name: "Business Management",
      description: "Gestión empresarial.",
      type: "soft",
    },
    {
      codeName: "customer-relationship",
      name: "Customer Relationship",
      description: "Gestión de relaciones con los clientes.",
      type: "soft",
    },
    {
      codeName: "self-motivation",
      name: "Self Motivation",
      description:
        "Automotivación y capacidad para gestionar proyectos personales.",
      type: "soft",
    },
    {
      codeName: "full-stack-development",
      name: "Full Stack Development",
      description: "Desarrollo frontend y backend.",
      type: "technical",
    },
    {
      codeName: "javascript",
      name: "JavaScript",
      description: "Lenguaje de programación utilizado en el desarrollo web.",
      type: "technical",
    },
    {
      codeName: "vue3",
      name: "Vue 3",
      description:
        "Framework JavaScript para la creación de interfaces de usuario.",
      type: "technical",
    },
    {
      codeName: "scrum",
      name: "Scrum",
      description: "Framework de desarrollo ágil.",
      type: "technical",
    },
    {
      codeName: "bug-fixing",
      name: "Bug Fixing",
      description: "Corrección de errores de software.",
      type: "technical",
    },
    {
      codeName: "web-application",
      name: "Web Application",
      description: "Desarrollo de aplicaciones web.",
      type: "technical",
    },
    {
      codeName: "adaptability-startups",
      name: "Adaptability to Startups",
      description: "Adaptación a los cambios en entornos de startups.",
      type: "soft",
    },
    {
      codeName: "problem-solving",
      name: "Problem Solving",
      description: "Habilidad para solucionar problemas técnicos complejos.",
      type: "soft",
    },
    {
      codeName: "teamwork",
      name: "Teamwork",
      description: "Colaboración efectiva con un equipo de desarrollo.",
      type: "soft",
    },
    {
      codeName: "team-leadership",
      name: "Team Leadership",
      description: "Liderazgo efectivo de equipos de desarrollo.",
      type: "soft",
    },
    {
      codeName: "aws-deployment",
      name: "AWS Deployment",
      description: "Despliegue de aplicaciones en Amazon Web Services.",
      type: "technical",
    },
    {
      codeName: "laravel",
      name: "Laravel",
      description: "Framework PHP para el desarrollo backend.",
      type: "technical",
    },
    {
      codeName: "system-architecture",
      name: "System Architecture",
      description: "Diseño de arquitectura de sistemas.",
      type: "technical",
    },
    {
      codeName: "microfrontend",
      name: "Microfrontend",
      description: "Arquitectura de microfrontends.",
      type: "technical",
    },
    {
      codeName: "ecommerce-development",
      name: "E-commerce Development",
      description: "Desarrollo de soluciones de comercio electrónico.",
      type: "technical",
    },
    {
      codeName: "cloud-computing",
      name: "Cloud Computing",
      description:
        "Uso de tecnologías en la nube para el desarrollo y despliegue.",
      type: "technical",
    },
    {
      codeName: "agile-methodologies",
      name: "Agile Methodologies",
      description: "Metodologías ágiles para gestión de proyectos.",
      type: "soft",
    },
    {
      codeName: "team-management",
      name: "Team Management",
      description: "Gestión efectiva de equipos.",
      type: "soft",
    },
    {
      codeName: "customer-oriented",
      name: "Customer Oriented",
      description: "Enfoque en la experiencia del cliente.",
      type: "soft",
    },
    {
      codeName: "production-monitoring",
      name: "Production Monitoring",
      description: "Monitoreo de la producción en sistemas de manufactura.",
      type: "technical",
    },
    {
      codeName: "productivity-analysis",
      name: "Productivity Analysis",
      description: "Análisis de productividad para la mejora continua.",
      type: "technical",
    },
    {
      codeName: "local-network",
      name: "Local Network",
      description: "Gestión de redes locales.",
      type: "technical",
    },
    {
      codeName: "jquery",
      name: "jQuery",
      description: "Biblioteca JavaScript para manipulación de DOM.",
      type: "technical",
    },
    {
      codeName: "web-platform",
      name: "Web Platform",
      description: "Desarrollo de plataformas web.",
      type: "technical",
    },
    {
      codeName: "business-analytics",
      name: "Business Analytics",
      description: "Análisis de datos empresariales.",
      type: "technical",
    },
    {
      codeName: "security-management",
      name: "Security Management",
      description: "Gestión de seguridad en sistemas empresariales.",
      type: "technical",
    },
    {
      codeName: "data-analysis",
      name: "Data Analysis",
      description: "Análisis de datos para la mejora de procesos.",
      type: "technical",
    },
    {
      codeName: "team-collaboration",
      name: "Team Collaboration",
      description: "Colaboración efectiva en equipo.",
      type: "soft",
    },
    {
      codeName: "graduation-project",
      name: "Graduation Project",
      description: "Dirección e implementación de proyectos de grado.",
      type: "technical",
    },
    {
      codeName: "technical-challenges",
      name: "technical Challenges",
      description: "Resolución de desafíos técnicos complejos.",
      type: "technical",
    },
    {
      codeName: "project-direction",
      name: "Project Direction",
      description: "Dirección y gestión de proyectos.",
      type: "soft",
    },
    {
      codeName: "solution-implementation",
      name: "Solution Implementation",
      description: "Implementación de soluciones técnicas.",
      type: "technical",
    },
    {
      codeName: "technical-consulting",
      name: "technical Consulting",
      description: "Asesoramiento técnico para proyectos de grado.",
      type: "soft",
    },
    {
      codeName: "technical-writing",
      name: "technical Writing",
      description: "Redacción técnica para documentación de proyectos.",
      type: "technical",
    },
    {
      codeName: "time-management",
      name: "Time Management",
      description: "Gestión efectiva del tiempo para cumplir con los plazos.",
      type: "soft",
    },
    {
      codeName: "infrastructure-management",
      name: "Infrastructure Management",
      description: "Gestión de infraestructuras de sistemas.",
      type: "technical",
    },
    {
      codeName: "network-architecture",
      name: "Network Architecture",
      description: "Diseño de arquitecturas de redes.",
      type: "technical",
    },
    {
      codeName: "project-planning",
      name: "Project Planning",
      description: "Planificación efectiva de proyectos.",
      type: "soft",
    },
    {
      codeName: "work-management",
      name: "Work Management",
      description: "Gestión de proyectos y tareas.",
      type: "soft",
    },
    {
      codeName: "budget-management",
      name: "Budget Management",
      description: "Gestión de presupuestos de proyectos.",
      type: "soft",
    },
    {
      codeName: "system-design",
      name: "System Design",
      description: "Diseño de sistemas informáticos.",
      type: "technical",
    },
    {
      codeName: "software-development",
      name: "software Development",
      description: "Desarrollo de aplicaciones de software.",
      type: "technical",
    },
    {
      codeName: "data-management",
      name: "Data Management",
      description: "Gestión de datos para aplicaciones empresariales.",
      type: "technical",
    },
    {
      codeName: "project-management",
      name: "Project Management",
      description: "Gestión de proyectos técnicos.",
      type: "soft",
    },
    {
      codeName: "collaborative-work",
      name: "Collaborative Work",
      description: "Trabajo colaborativo para el desarrollo de proyectos.",
      type: "soft",
    },
    {
      codeName: "medical-records",
      name: "Medical Records",
      description: "Gestión de historias médicas electrónicas.",
      type: "technical",
    },
    {
      codeName: "desktop-application",
      name: "Desktop Application",
      description: "Desarrollo de aplicaciones de escritorio.",
      type: "technical",
    },
    {
      codeName: "java",
      name: "Java",
      description: "Lenguaje de programación para desarrollo de aplicaciones.",
      type: "technical",
    },
    {
      codeName: "object-oriented-programming",
      name: "Object Oriented Programming",
      description: "Programación orientada a objetos.",
      type: "technical",
    },
    {
      codeName: "requirements-gathering",
      name: "Requirements Gathering",
      description: "Levantamiento de requerimientos técnicos.",
      type: "technical",
    },
    {
      codeName: "software-design",
      name: "software Design",
      description: "Diseño de aplicaciones de software.",
      type: "technical",
    },
    {
      codeName: "technical-communication",
      name: "technical Communication",
      description: "Comunicación efectiva para el desarrollo técnico.",
      type: "soft",
    },
    {
      codeName: "analytical-thinking",
      name: "Analytical Thinking",
      description: "Pensamiento analítico para soluciones técnicas.",
      type: "soft",
    },
    {
      codeName: "adaptability",
      name: "Adaptability",
      description: "Adaptación a tecnologías y desafíos nuevos.",
      type: "soft",
    },
    {
      codeName: "inventory-management",
      name: "Inventory Management",
      description: "Gestión de inventarios para aplicaciones empresariales.",
      type: "technical",
    },
    {
      codeName: "php",
      name: "PHP",
      description: "Lenguaje de programación para desarrollo web.",
      type: "technical",
    },
    {
      codeName: "crud",
      name: "CRUD",
      description: "Operaciones CRUD para bases de datos.",
      type: "technical",
    },
    {
      codeName: "offline-system",
      name: "Offline System",
      description: "Desarrollo de sistemas para operar sin conexión.",
      type: "technical",
    },
    {
      codeName: "asset-management",
      name: "Asset Management",
      description: "Gestión de activos para aplicaciones empresariales.",
      type: "technical",
    },
    {
      codeName: "data-entry",
      name: "Data Entry",
      description: "Entrada y manipulación de datos.",
      type: "technical",
    },
    {
      codeName: "database-management",
      name: "Database Management",
      description: "Gestión de bases de datos.",
      type: "technical",
    },
  ],
  attributesTypes: [
    {
      codeName: "email",
      name: "Email",
      type: "text",
    },
    {
      codeName: "phone",
      name: "Phone",
      type: "text",
    },
    {
      codeName: "url",
      name: "URL",
      type: "text",
    },
    {
      codeName: "label",
      name: "Label",
      type: "text",
    },
    {
      codeName: "names",
      name: "Names",
      type: "text",
    },
    {
      codeName: "lastName",
      name: "Last Name",
      type: "text",
    },
    {
      codeName: "summary",
      name: "Summary",
      type: "text",
    },
    {
      codeName: "location",
      name: "Location",
      type: "object",
    },
  ],
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
      usersAttributes
    */
  usersAttributes: [
    {
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        attributeTypeId: {
          table: "attributesTypes",
          field: "codeName",
          value: "names",
        },
      },
      attributeValue: "Pablo Alexander",
    },
    {
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        attributeTypeId: {
          table: "attributesTypes",
          field: "codeName",
          value: "lastName",
        },
      },
      attributeValue: "Contreras Guevara",
    },
    {
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        attributeTypeId: {
          table: "attributesTypes",
          field: "codeName",
          value: "email",
        },
      },
      attributeValue: "pacg1991@gmail.com",
    },
    {
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        attributeTypeId: {
          table: "attributesTypes",
          field: "codeName",
          value: "phone",
        },
      },
      attributeValue: "+51 918490148",
    },
    {
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        attributeTypeId: {
          table: "attributesTypes",
          field: "codeName",
          value: "url",
        },
      },
      attributeValue: "https://pablo-c.com",
    },
    {
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        attributeTypeId: {
          table: "attributesTypes",
          field: "codeName",
          value: "label",
        },
      },
      attributeValue: "Ingeniero de software con más de 8 años de experiencia",
    },
    {
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        attributeTypeId: {
          table: "attributesTypes",
          field: "codeName",
          value: "summary",
        },
      },
      attributeValue:
        "Ingeniero de software con más de 8 años de experiencia, especializado en desarrollo Full Stack con Python y JavaScript. Experto en crear soluciones tecnológicas con Vue, Django, microservicios y AWS, he desarrollado con éxito y liderado la implementación de sistemas ERP y plataformas fintech, mejorando significativamente la eficiencia operativa y la experiencia del usuario. Habilidoso en la coordinación y motivación de equipos, me adapto fácilmente a entornos dinámicos y desafiantes, siempre enfocado en la calidad y la innovación.",
    },
    {
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        attributeTypeId: {
          table: "attributesTypes",
          field: "codeName",
          value: "location",
        },
      },
      attributeValue: {
        address: "",
        postalCode: "15009",
        city: "Lima",
        countryCode: "PE",
        region: "Perú",
      },
    },
  ],
  files: [
    {
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        groupFileId: {
          table: "groupsFiles",
          field: "codeName",
          value: "profile",
        },
        fileTypeId: {
          table: "typeFiles",
          field: "codeName",
          value: "avif",
        },
      },
      url: "https://images-bypabloc.s3.sa-east-1.amazonaws.com/cv/2.avif",
      priority: 2,
    },
    {
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        groupFileId: {
          table: "groupsFiles",
          field: "codeName",
          value: "profile",
        },
        fileTypeId: {
          table: "typeFiles",
          field: "codeName",
          value: "webp",
        },
      },
      url: "https://images-bypabloc.s3.sa-east-1.amazonaws.com/cv/2.webp",
      priority: 2,
    },
    {
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        groupFileId: {
          table: "groupsFiles",
          field: "codeName",
          value: "profile",
        },
        fileTypeId: {
          table: "typeFiles",
          field: "codeName",
          value: "jp2",
        },
      },
      url: "https://images-bypabloc.s3.sa-east-1.amazonaws.com/cv/2.jp2",
      priority: 2,
    },
    {
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        groupFileId: {
          table: "groupsFiles",
          field: "codeName",
          value: "profile",
        },
        fileTypeId: {
          table: "typeFiles",
          field: "codeName",
          value: "jpeg",
        },
      },
      url: "https://images-bypabloc.s3.sa-east-1.amazonaws.com/cv/2.jpg",
      priority: 2,
    },
    {
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        groupFileId: {
          table: "groupsFiles",
          field: "codeName",
          value: "profile",
        },
        fileTypeId: {
          table: "typeFiles",
          field: "codeName",
          value: "avif",
        },
      },
      url: "https://images-bypabloc.s3.sa-east-1.amazonaws.com/cv/1.avif",
      priority: 1,
    },
    {
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        groupFileId: {
          table: "groupsFiles",
          field: "codeName",
          value: "profile",
        },
        fileTypeId: {
          table: "typeFiles",
          field: "codeName",
          value: "webp",
        },
      },
      url: "https://images-bypabloc.s3.sa-east-1.amazonaws.com/cv/1.webp",
      priority: 1,
    },
    {
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        groupFileId: {
          table: "groupsFiles",
          field: "codeName",
          value: "profile",
        },
        fileTypeId: {
          table: "typeFiles",
          field: "codeName",
          value: "jp2",
        },
      },
      url: "https://images-bypabloc.s3.sa-east-1.amazonaws.com/cv/1.jp2",
      priority: 1,
    },
    {
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        groupFileId: {
          table: "groupsFiles",
          field: "codeName",
          value: "profile",
        },
        fileTypeId: {
          table: "typeFiles",
          field: "codeName",
          value: "jpeg",
        },
      },
      url: "https://images-bypabloc.s3.sa-east-1.amazonaws.com/cv/1.jpg",
      priority: 1,
    },
  ],
  works: [
    {
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        employerId: {
          table: "employers",
          field: "codeName",
          value: "destacame",
        },
        jobTypeId: {
          table: "jobTypes",
          field: "codeName",
          value: "fullTime",
        },
      },
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
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        employerId: {
          table: "employers",
          field: "codeName",
          value: "destacame",
        },
        jobTypeId: {
          table: "jobTypes",
          field: "codeName",
          value: "fullTime",
        },
      },
      codeName: "destacame-frontend",
      name: "Destacame",
      position: "Desarrollador Web Frontend",
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
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        jobTypeId: {
          table: "jobTypes",
          field: "codeName",
          value: "personalProject",
        },
      },
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
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        employerId: {
          table: "employers",
          field: "codeName",
          value: "goodmeal",
        },
        jobTypeId: {
          table: "jobTypes",
          field: "codeName",
          value: "fullTime",
        },
      },
      codeName: "goodmeal",
      name: "GoodMeal",
      position: "Desarrollador Web Full Stack",
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
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        employerId: {
          table: "employers",
          field: "codeName",
          value: "dibal",
        },
        jobTypeId: {
          table: "jobTypes",
          field: "codeName",
          value: "fullTime",
        },
      },
      codeName: "dibal",
      name: "Dibal",
      position: "Líder de Equipo de Desarrollo y Desarrollador",
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
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        employerId: {
          table: "employers",
          field: "codeName",
          value: "cofasa",
        },
        jobTypeId: {
          table: "jobTypes",
          field: "codeName",
          value: "freelance",
        },
      },
      codeName: "cofasa",
      name: "LABORATORIO COFASA S.A.",
      position: "Desarrollador de Sistemas Web",
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
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        jobTypeId: {
          table: "jobTypes",
          field: "codeName",
          value: "freelance",
        },
      },
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
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        jobTypeId: {
          table: "jobTypes",
          field: "codeName",
          value: "freelance",
        },
      },
      codeName: "iai",
      name: "Freelance > Instituto Autónomo de Infraestructura (IAI)",
      position: "Líder de Desarrollo de software y Arquitectura de Sistemas",
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
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        jobTypeId: {
          table: "jobTypes",
          field: "codeName",
          value: "freelance",
        },
      },
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
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        jobTypeId: {
          table: "jobTypes",
          field: "codeName",
          value: "freelance",
        },
      },
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
  educations: [
    {
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        institutionId: {
          table: "institutions",
          field: "codeName",
          value: "youtube",
        },
      },
      area: "Desarrollo Web",
      learn:
        "En Udemy he tomado varios cursos de desarrollo web, entre ellos: JavaScript, React, Vue, Node, SQL, entre otros.",
      studyType: "course",
      startDate: "2017-04-01",
    },
    {
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        institutionId: {
          table: "institutions",
          field: "codeName",
          value: "udemy",
        },
      },
      area: "Desarrollo Web",
      learn:
        "Cuando comencé a introducirme en el curso de programación en 2013, accedí a material gratuito y de paga que existía en ese momento en linea, hasta el día de hoy no paro de aprender",
      studyType: "course",
      startDate: "2012-04-20",
    },
    {
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        institutionId: {
          table: "institutions",
          field: "codeName",
          value: "uptyab",
        },
      },
      area: "Ingeniería Informática",
      learn:
        "Estudié Ingeniería Informática en la UPTYAB, donde adquirí conocimientos en programación, bases de datos, redes, sistemas operativos, entre otros.",
      studyType: "bachelorDegree",
      startDate: "2011-03-01",
      endDate: "2016-03-01",
    },
  ],
  awards: [
    {
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
      },
      title: "Premio a Innovador del año 2023 en Destacame",
      date: "2024-01-24",
      awarder: "Destacame",
      summary:
        "Por liderar la implementación de soluciones tecnológicas innovadoras en la empresa, mejorando significativamente la eficiencia operativa y la experiencia del usuario.",
      url: "https://heyzine.com/flip-book/cdc911b3d1.html",
    },
    {
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
      },
      title: "Desafío Triple Alianza Lima",
      date: "2020-11-18",
      awarder: "Incubagraria, 1551, StartUpUni",
      summary:
        'Por haber obtenido el 1er lugar en el sector Comercio del "Desafío Triple Alianza COVID-19", esto sucedió en mi experiencia en DIBAL.',
      url: "https://1drv.ms/b/s!AoZaJmtucTrahbFAsRnMKiJDAxBlKg?e=9MKGjP",
    },
  ],
  certificates: [
    {
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        issuerId: {
          table: "issuers",
          field: "codeName",
          value: "devtalles",
        },
      },
      title: "Docker - Guía práctica de uso para desarrolladores",
      date: "2023-04-20",
      url: "https://cursos.devtalles.com/certificates/f7qc3ju28w",
    },
    {
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        issuerId: {
          table: "issuers",
          field: "codeName",
          value: "devtalles",
        },
      },
      title: "Node - Autenticación Rest con Clean Architecture",
      date: "2023-08-15",
      url: "https://cursos.devtalles.com/certificates/91cxyahzil",
    },
    {
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        issuerId: {
          table: "issuers",
          field: "codeName",
          value: "devtalles",
        },
      },
      title: "Principios SOLID y Clean Code",
      date: "2023-11-05",
      url: "http://ude.my/UC-ddf92744-e69f-47ab-b28d-c4f7b569b7d4",
    },
    {
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        issuerId: {
          table: "issuers",
          field: "codeName",
          value: "udemy",
        },
      },
      title: "Next.js: El framework de React para producción",
      date: "2024-01-04",
      url: "http://ude.my/UC-8297be13-d656-4e62-b64b-642819930c71",
    },
    {
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        issuerId: {
          table: "issuers",
          field: "codeName",
          value: "udemy",
        },
      },
      title: "React: De cero a experto ( Hooks y MERN )",
      date: "2023-11-13",
      url: "http://ude.my/UC-6f8fa099-e631-459d-a139-989d441a1b21",
    },
    {
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        issuerId: {
          table: "issuers",
          field: "codeName",
          value: "udemy",
        },
      },
      title: "Vue.js - Intermedio: Lleva tus bases al siguiente nivel",
      date: "2023-03-22",
      url: "http://ude.my/UC-b8d6554e-4cb9-49dd-becb-a5dbfdcf6f26",
    },
    {
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        issuerId: {
          table: "issuers",
          field: "codeName",
          value: "udemy",
        },
      },
      title: "Vue.js: De cero a experto",
      date: "2023-05-30",
      url: "http://ude.my/UC-a217906e-84eb-40dc-9303-36de5b71e0cc",
    },
    {
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        issuerId: {
          table: "issuers",
          field: "codeName",
          value: "udemy",
        },
      },
      title: "SQL de cero: Tu guía práctica con PostgreSQL",
      date: "2023-02-12",
      url: "http://ude.my/UC-afb98ee6-8704-4b20-9e1f-15bdacf2c76d",
    },
    {
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        issuerId: {
          table: "issuers",
          field: "codeName",
          value: "udemy",
        },
      },
      title: "NodeJS: De cero a experto",
      date: "2023-02-12",
      url: "http://ude.my/UC-9acb44f1-27c6-402e-9dae-8a04bf3d424b",
    },
    {
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        issuerId: {
          table: "issuers",
          field: "codeName",
          value: "udemy",
        },
      },
      title: "Nest: Desarrollo backend escalable con Node",
      date: "2023-02-12",
      url: "http://ude.my/UC-810baa94-7f51-4c54-b631-d62b4af77806",
    },
    {
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        issuerId: {
          table: "issuers",
          field: "codeName",
          value: "udemy",
        },
      },
      title: "JavaScript moderno: Guía para dominar el lenguaje",
      date: "2023-07-29",
      url: "http://ude.my/UC-516bd9e6-59a0-4f28-b3bf-db2539d158d9",
    },
  ],
  publications: [
    {
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        publisherId: {
          table: "publishers",
          field: "codeName",
          value: "medium",
        },
      },
      name: "Instalando Docker y Docker-compose en WSL2 Ubuntu sin Naufragar en el Intento",
      releaseDate: "2023-06-04",
      url: "https://bypablo.medium.com/un-viaje-épico-en-código-instalando-docker-y-docker-compose-en-wsl2-ubuntu-sin-naufragar-en-el-b21f38a9571",
      summary: "¿Como instalar Docker y Docker-compose en WSL2 sin fallar?",
    },
    {
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        publisherId: {
          table: "publishers",
          field: "codeName",
          value: "medium",
        },
      },
      name: "Explorando 'type' e 'interface' en TypeScript: Un Enfoque en el Universo Marvel",
      releaseDate: "2023-05-28",
      url: "https://bypablo.medium.com/explorando-type-e-interface-en-typescript-un-enfoque-en-el-universo-marvel-4ad47317838e",
      summary:
        "¿Cuál es la diferencia entre 'type' e 'interface' en TypeScript? ¿Cómo se aplican en el Universo Marvel?",
    },
    {
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        publisherId: {
          table: "publishers",
          field: "codeName",
          value: "medium",
        },
      },
      name: "JavaScript vs TypeScript: ¡El choque de titanes que desencadena una guerra de tipos!",
      releaseDate: "2023-05-29",
      url: "https://bypablo.medium.com/javascript-vs-typescript-el-choque-de-titanes-que-desencadena-una-guerra-de-tipos-dadc70c06766",
      summary:
        "¿Cuál es la diferencia entre JavaScript y TypeScript? ¿Cuál es mejor?",
    },
    {
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        publisherId: {
          table: "publishers",
          field: "codeName",
          value: "medium",
        },
      },
      name: '¡Bienvenidos a TypeScript, no más "undefined"!',
      releaseDate: "2023-05-30",
      url: "https://bypablo.medium.com/bienvenidos-a-typescript-no-más-undefined-5e473f0f4670",
      summary:
        "¿Qué es TypeScript? ¿Cómo se usa? ¿Por qué es mejor que JavaScript?",
    },
    {
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        publisherId: {
          table: "publishers",
          field: "codeName",
          value: "medium",
        },
      },
      name: "Dominando el Mundo de los Tipos en TypeScript",
      releaseDate: "2023-05-31",
      url: "https://bypablo.medium.com/dominando-el-mundo-de-los-tipos-en-typescript-e543eb42eb9c",
      summary:
        "¿Qué son los tipos en TypeScript? ¿Cómo se usan? ¿Por qué son importantes?",
    },
  ],
  languagesUsers: [
    {
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
      },
      fluency: "Nativo",
    },
    {
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
      },
      fluency: "Intermedio",
    },
  ],
  projects: [
    {
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
      },
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
  references: [
    {
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        employerId: {
          table: "employers",
          field: "codeName",
          value: "destacame",
        },
      },
      name: "Alan Vergara Bravo",
      reference: "Compañero de equipo",
      position: "software Architect Developer",
      url: "https://www.linkedin.com/in/alan-vergara-bravo-b17164145",
      scrappingRecommendation: {
        linkedin:
          "https://www.linkedin.com/in/bypabloc/details/recommendations",
        elementId:
          "profilePagedListComponent-ACoAACeoGgsB5cPxfqr-T2ylRvqy6qRWe6TgZfc-RECOMMENDATIONS-VIEW-DETAILS-profileTabSection-RECEIVED-RECOMMENDATIONS-NONE-es-ES-0",
      },
    },
    {
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        employerId: {
          table: "employers",
          field: "codeName",
          value: "destacame",
        },
      },
      name: "Alejandra Medina Briceño",
      reference: "Compañero de equipo",
      position: "Diseñadora UX/UI",
      url: "https://www.linkedin.com/in/alejandra-medinab",
      scrappingRecommendation: {
        linkedin:
          "https://www.linkedin.com/in/bypabloc/details/recommendations",
        elementId:
          "profilePagedListComponent-ACoAACeoGgsB5cPxfqr-T2ylRvqy6qRWe6TgZfc-RECOMMENDATIONS-VIEW-DETAILS-profileTabSection-RECEIVED-RECOMMENDATIONS-NONE-es-ES-1",
      },
    },
    {
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        employerId: {
          table: "employers",
          field: "codeName",
          value: "destacame",
        },
      },
      name: "Baldomero Águila",
      reference: "Compañero de equipo",
      position: "Desarrollador Mobile",
      url: "https://www.linkedin.com/in/baldomero",
    },
    {
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        employerId: {
          table: "employers",
          field: "codeName",
          value: "destacame",
        },
      },
      name: "Cristian Fuentes",
      reference: "Compañero de equipo",
      position: "Desarrollador Full Stack",
      url: "https://www.linkedin.com/in/csfuente",
    },
    {
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        employerId: {
          table: "employers",
          field: "codeName",
          value: "destacame",
        },
      },
      name: "Helis Montes",
      reference: "Compañero de equipo",
      position: "Desarrollador Full Stack",
      url: "https://www.linkedin.com/in/helis-montes",
    },
    {
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        employerId: {
          table: "employers",
          field: "codeName",
          value: "destacame",
        },
      },
      name: "Edder Ramírez",
      reference: "Compañero de equipo",
      position: "Desarrollador Full Stack",
      url: "https://www.linkedin.com/in/edderleonardo",
    },
    {
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        employerId: {
          table: "employers",
          field: "codeName",
          value: "dibal",
        },
      },
      name: "José Namoc",
      reference: "Compañero de equipo",
      position: "Desarrollador Full Stack",
      url: "https://www.linkedin.com/in/jose-namoc-lopez",
      scrappingRecommendation: {
        linkedin:
          "https://www.linkedin.com/in/bypabloc/details/recommendations",
        elementId:
          "profilePagedListComponent-ACoAACeoGgsB5cPxfqr-T2ylRvqy6qRWe6TgZfc-RECOMMENDATIONS-VIEW-DETAILS-profileTabSection-RECEIVED-RECOMMENDATIONS-NONE-es-ES-6",
      },
    },
    {
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
        employerId: {
          table: "employers",
          field: "codeName",
          value: "dibal",
        },
      },
      name: "Jacnelly Colmenarez",
      reference: "Compañera de equipo",
      position: "UI/UX Designer",
      url: "https://www.linkedin.com/in/jacnelly-colmenarez",
      scrappingRecommendation: {
        linkedin:
          "https://www.linkedin.com/in/bypabloc/details/recommendations",
        elementId:
          "profilePagedListComponent-ACoAACeoGgsB5cPxfqr-T2ylRvqy6qRWe6TgZfc-RECOMMENDATIONS-VIEW-DETAILS-profileTabSection-RECEIVED-RECOMMENDATIONS-NONE-es-ES-3",
      },
    },
    {
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
      },
      name: "Felipe Rivera",
      reference: "Trabajé en la misma empresa",
      position: "Talent Acquisition Lead",
      url: "https://www.linkedin.com/in/frtavonatti",
    },
    {
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
      },
      name: "Samuel Esponiza",
      reference:
        "Estudié en la misma universidad y trabajé en proyectos juntos",
      url: "https://www.linkedin.com/in/samuelespinozac",
      position: "Desarrollador Full Stack",
      scrappingRecommendation: {
        linkedin:
          "https://www.linkedin.com/in/bypabloc/details/recommendations",
        elementId:
          "profilePagedListComponent-ACoAACeoGgsB5cPxfqr-T2ylRvqy6qRWe6TgZfc-RECOMMENDATIONS-VIEW-DETAILS-profileTabSection-RECEIVED-RECOMMENDATIONS-NONE-es-ES-4",
      },
    },
  ],
  interestsKeywords: [
    {
      relationship: {
        interestId: {
          table: "interests",
          field: "codeName",
          value: "devops",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "automation",
        },
      },
    },
    {
      relationship: {
        interestId: {
          table: "interests",
          field: "codeName",
          value: "bot-creation",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "ai-chatbots",
        },
      },
    },
    {
      relationship: {
        interestId: {
          table: "interests",
          field: "codeName",
          value: "bot-creation",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "automation",
        },
      },
    },
    {
      relationship: {
        interestId: {
          table: "interests",
          field: "codeName",
          value: "scraping",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "scrum",
        },
      },
    },
    {
      relationship: {
        interestId: {
          table: "interests",
          field: "codeName",
          value: "kubernetes",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "cloud-computing",
        },
      },
    },
    {
      relationship: {
        interestId: {
          table: "interests",
          field: "codeName",
          value: "machine-learning",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "machine-learning",
        },
      },
    },
    {
      relationship: {
        interestId: {
          table: "interests",
          field: "codeName",
          value: "cloud-computing",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "cloud-computing",
        },
      },
    },
    {
      relationship: {
        interestId: {
          table: "interests",
          field: "codeName",
          value: "blockchain",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "blockchain",
        },
      },
    },
    {
      relationship: {
        interestId: {
          table: "interests",
          field: "codeName",
          value: "ai-chatbots",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "ai-chatbots",
        },
      },
    },
    {
      relationship: {
        interestId: {
          table: "interests",
          field: "codeName",
          value: "microservices",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "microservices",
        },
      },
    },
    {
      relationship: {
        interestId: {
          table: "interests",
          field: "codeName",
          value: "internet-of-things",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "internet-of-things",
        },
      },
    },
    {
      relationship: {
        interestId: {
          table: "interests",
          field: "codeName",
          value: "frontend-development",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "frontend-development",
        },
      },
    },
    {
      relationship: {
        interestId: {
          table: "interests",
          field: "codeName",
          value: "backend-development",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "web-development",
        },
      },
    },
    {
      relationship: {
        interestId: {
          table: "interests",
          field: "codeName",
          value: "data-engineering",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "data-analysis",
        },
      },
    },
    {
      relationship: {
        interestId: {
          table: "interests",
          field: "codeName",
          value: "serverless-computing",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "cloud-computing",
        },
      },
    },
    {
      relationship: {
        interestId: {
          table: "interests",
          field: "codeName",
          value: "edge-computing",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "edge-computing",
        },
      },
    },
    {
      relationship: {
        interestId: {
          table: "interests",
          field: "codeName",
          value: "mobile-development",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "mobile-development",
        },
      },
    },
    {
      relationship: {
        interestId: {
          table: "interests",
          field: "codeName",
          value: "game-development",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "game-development",
        },
      },
    },
    {
      relationship: {
        interestId: {
          table: "interests",
          field: "codeName",
          value: "security-engineering",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "security-engineering",
        },
      },
    },
    {
      relationship: {
        interestId: {
          table: "interests",
          field: "codeName",
          value: "robotics",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "robotics",
        },
      },
    },
    {
      relationship: {
        interestId: {
          table: "interests",
          field: "codeName",
          value: "ar-vr",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "ar-vr",
        },
      },
    },
  ],
  skillsKeywords: [
    {
      relationship: {
        skillId: {
          table: "skills",
          field: "codeName",
          value: "docker",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "docker",
        },
      },
    },
    {
      relationship: {
        skillId: {
          table: "skills",
          field: "codeName",
          value: "kubernetes",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "kubernetes",
        },
      },
    },
    {
      relationship: {
        skillId: {
          table: "skills",
          field: "codeName",
          value: "react",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "react",
        },
      },
    },
    {
      relationship: {
        skillId: {
          table: "skills",
          field: "codeName",
          value: "node",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "node",
        },
      },
    },
    {
      relationship: {
        skillId: {
          table: "skills",
          field: "codeName",
          value: "sql",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "sql",
        },
      },
    },
    {
      relationship: {
        skillId: {
          table: "skills",
          field: "codeName",
          value: "python",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "python",
        },
      },
    },
    {
      relationship: {
        skillId: {
          table: "skills",
          field: "codeName",
          value: "django",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "django",
        },
      },
    },
    {
      relationship: {
        skillId: {
          table: "skills",
          field: "codeName",
          value: "microservices",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "microservices",
        },
      },
    },
    {
      relationship: {
        skillId: {
          table: "skills",
          field: "codeName",
          value: "aws",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "aws",
        },
      },
    },
    {
      relationship: {
        skillId: {
          table: "skills",
          field: "codeName",
          value: "frontend-architecture",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "frontend-architecture",
        },
      },
    },
    {
      relationship: {
        skillId: {
          table: "skills",
          field: "codeName",
          value: "vue",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "vue",
        },
      },
    },
    {
      relationship: {
        skillId: {
          table: "skills",
          field: "codeName",
          value: "nuxt",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "nuxt",
        },
      },
    },
    {
      relationship: {
        skillId: {
          table: "skills",
          field: "codeName",
          value: "typescript",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "typescript",
        },
      },
    },
    {
      relationship: {
        skillId: {
          table: "skills",
          field: "codeName",
          value: "frontend-development",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "frontend-development",
        },
      },
    },
    {
      relationship: {
        skillId: {
          table: "skills",
          field: "codeName",
          value: "web-development",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "web-development",
        },
      },
    },
    {
      relationship: {
        skillId: {
          table: "skills",
          field: "codeName",
          value: "erp",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "erp",
        },
      },
    },
    {
      relationship: {
        skillId: {
          table: "skills",
          field: "codeName",
          value: "project-management",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "project-management",
        },
      },
    },
    {
      relationship: {
        skillId: {
          table: "skills",
          field: "codeName",
          value: "ecommerce",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "ecommerce",
        },
      },
    },
    {
      relationship: {
        skillId: {
          table: "skills",
          field: "codeName",
          value: "automation",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "automation",
        },
      },
    },
    {
      relationship: {
        skillId: {
          table: "skills",
          field: "codeName",
          value: "startup",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "startup",
        },
      },
    },
    {
      relationship: {
        skillId: {
          table: "skills",
          field: "codeName",
          value: "full-stack-development",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "full-stack-development",
        },
      },
    },
    {
      relationship: {
        skillId: {
          table: "skills",
          field: "codeName",
          value: "vue3",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "vue3",
        },
      },
    },
    {
      relationship: {
        skillId: {
          table: "skills",
          field: "codeName",
          value: "scrum",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "scrum",
        },
      },
    },
    {
      relationship: {
        skillId: {
          table: "skills",
          field: "codeName",
          value: "bug-fixing",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "bug-fixing",
        },
      },
    },
    {
      relationship: {
        skillId: {
          table: "skills",
          field: "codeName",
          value: "web-application",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "web-application",
        },
      },
    },
    {
      relationship: {
        skillId: {
          table: "skills",
          field: "codeName",
          value: "team-leadership",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "team-leadership",
        },
      },
    },
    {
      relationship: {
        skillId: {
          table: "skills",
          field: "codeName",
          value: "aws-deployment",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "aws-deployment",
        },
      },
    },
    {
      relationship: {
        skillId: {
          table: "skills",
          field: "codeName",
          value: "laravel",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "laravel",
        },
      },
    },
    {
      relationship: {
        skillId: {
          table: "skills",
          field: "codeName",
          value: "system-architecture",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "system-architecture",
        },
      },
    },
    {
      relationship: {
        skillId: {
          table: "skills",
          field: "codeName",
          value: "microfrontend",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "microfrontend",
        },
      },
    },
    {
      relationship: {
        skillId: {
          table: "skills",
          field: "codeName",
          value: "production-monitoring",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "production-monitoring",
        },
      },
    },
    {
      relationship: {
        skillId: {
          table: "skills",
          field: "codeName",
          value: "productivity-analysis",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "productivity-analysis",
        },
      },
    },
    {
      relationship: {
        skillId: {
          table: "skills",
          field: "codeName",
          value: "local-network",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "local-network",
        },
      },
    },
    {
      relationship: {
        skillId: {
          table: "skills",
          field: "codeName",
          value: "jquery",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "jquery",
        },
      },
    },
    {
      relationship: {
        skillId: {
          table: "skills",
          field: "codeName",
          value: "web-platform",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "web-platform",
        },
      },
    },
    {
      relationship: {
        skillId: {
          table: "skills",
          field: "codeName",
          value: "graduation-project",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "graduation-project",
        },
      },
    },
    {
      relationship: {
        skillId: {
          table: "skills",
          field: "codeName",
          value: "technical-challenges",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "technical-challenges",
        },
      },
    },
    {
      relationship: {
        skillId: {
          table: "skills",
          field: "codeName",
          value: "project-direction",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "project-direction",
        },
      },
    },
    {
      relationship: {
        skillId: {
          table: "skills",
          field: "codeName",
          value: "solution-implementation",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "solution-implementation",
        },
      },
    },
    {
      relationship: {
        skillId: {
          table: "skills",
          field: "codeName",
          value: "team-collaboration",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "team-collaboration",
        },
      },
    },
    {
      relationship: {
        skillId: {
          table: "skills",
          field: "codeName",
          value: "infrastructure-management",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "infrastructure-management",
        },
      },
    },
    {
      relationship: {
        skillId: {
          table: "skills",
          field: "codeName",
          value: "network-architecture",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "network-architecture",
        },
      },
    },
    {
      relationship: {
        skillId: {
          table: "skills",
          field: "codeName",
          value: "project-planning",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "project-planning",
        },
      },
    },
    {
      relationship: {
        skillId: {
          table: "skills",
          field: "codeName",
          value: "work-management",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "work-management",
        },
      },
    },
    {
      relationship: {
        skillId: {
          table: "skills",
          field: "codeName",
          value: "budget-management",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "budget-management",
        },
      },
    },
    {
      relationship: {
        skillId: {
          table: "skills",
          field: "codeName",
          value: "medical-records",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "medical-records",
        },
      },
    },
    {
      relationship: {
        skillId: {
          table: "skills",
          field: "codeName",
          value: "desktop-application",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "desktop-application",
        },
      },
    },
    {
      relationship: {
        skillId: {
          table: "skills",
          field: "codeName",
          value: "java",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "java",
        },
      },
    },
    {
      relationship: {
        skillId: {
          table: "skills",
          field: "codeName",
          value: "object-oriented-programming",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "object-oriented-programming",
        },
      },
    },
    {
      relationship: {
        skillId: {
          table: "skills",
          field: "codeName",
          value: "requirements-gathering",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "requirements-gathering",
        },
      },
    },
    {
      relationship: {
        skillId: {
          table: "skills",
          field: "codeName",
          value: "inventory-management",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "inventory-management",
        },
      },
    },
    {
      relationship: {
        skillId: {
          table: "skills",
          field: "codeName",
          value: "php",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "php",
        },
      },
    },
    {
      relationship: {
        skillId: {
          table: "skills",
          field: "codeName",
          value: "crud",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "crud",
        },
      },
    },
    {
      relationship: {
        skillId: {
          table: "skills",
          field: "codeName",
          value: "offline-system",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "offline-system",
        },
      },
    },
    {
      relationship: {
        skillId: {
          table: "skills",
          field: "codeName",
          value: "asset-management",
        },
        keywordId: {
          table: "keywords",
          field: "codeName",
          value: "asset-management",
        },
      },
    },
  ],

  /**
      UsersInterests
      WorkstechnicalSkills
      WorkssoftSkills
     */
  usersInterests: [
    {
      relationship: {
        interestId: {
          table: "interests",
          field: "codeName",
          value: "devops",
        },
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
      },
    },
    {
      relationship: {
        interestId: {
          table: "interests",
          field: "codeName",
          value: "bot-creation",
        },
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
      },
    },
    {
      relationship: {
        interestId: {
          table: "interests",
          field: "codeName",
          value: "scraping",
        },
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
      },
    },
    {
      relationship: {
        interestId: {
          table: "interests",
          field: "codeName",
          value: "kubernetes",
        },
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
      },
    },
    {
      relationship: {
        interestId: {
          table: "interests",
          field: "codeName",
          value: "machine-learning",
        },
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
      },
    },
    {
      relationship: {
        interestId: {
          table: "interests",
          field: "codeName",
          value: "cloud-computing",
        },
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
      },
    },
    {
      relationship: {
        interestId: {
          table: "interests",
          field: "codeName",
          value: "blockchain",
        },
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
      },
    },
    {
      relationship: {
        interestId: {
          table: "interests",
          field: "codeName",
          value: "ai-chatbots",
        },
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
      },
    },
    {
      relationship: {
        interestId: {
          table: "interests",
          field: "codeName",
          value: "microservices",
        },
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
      },
    },
    {
      relationship: {
        interestId: {
          table: "interests",
          field: "codeName",
          value: "internet-of-things",
        },
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
      },
    },
    {
      relationship: {
        interestId: {
          table: "interests",
          field: "codeName",
          value: "frontend-development",
        },
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
      },
    },
    {
      relationship: {
        interestId: {
          table: "interests",
          field: "codeName",
          value: "backend-development",
        },
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
      },
    },
    {
      relationship: {
        interestId: {
          table: "interests",
          field: "codeName",
          value: "data-engineering",
        },
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
      },
    },
    {
      relationship: {
        interestId: {
          table: "interests",
          field: "codeName",
          value: "serverless-computing",
        },
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
      },
    },
    {
      relationship: {
        interestId: {
          table: "interests",
          field: "codeName",
          value: "edge-computing",
        },
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
      },
    },
    {
      relationship: {
        interestId: {
          table: "interests",
          field: "codeName",
          value: "mobile-development",
        },
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
      },
    },
    {
      relationship: {
        interestId: {
          table: "interests",
          field: "codeName",
          value: "game-development",
        },
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
      },
    },
    {
      relationship: {
        interestId: {
          table: "interests",
          field: "codeName",
          value: "security-engineering",
        },
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
      },
    },
    {
      relationship: {
        interestId: {
          table: "interests",
          field: "codeName",
          value: "robotics",
        },
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
      },
    },
    {
      relationship: {
        interestId: {
          table: "interests",
          field: "codeName",
          value: "ar-vr",
        },
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
      },
    },
  ],
  worksTechnicalSkills: [
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "destacame-architect",
        },
        technicalSkillId: {
          table: "skills",
          field: "codeName",
          value: "frontend-architecture",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "destacame-architect",
        },
        technicalSkillId: {
          table: "skills",
          field: "codeName",
          value: "typescript",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "destacame-architect",
        },
        technicalSkillId: {
          table: "skills",
          field: "codeName",
          value: "frontend-development",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "destacame-architect",
        },
        technicalSkillId: {
          table: "skills",
          field: "codeName",
          value: "python",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "destacame-architect",
        },
        technicalSkillId: {
          table: "skills",
          field: "codeName",
          value: "django",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "destacame-architect",
        },
        technicalSkillId: {
          table: "skills",
          field: "codeName",
          value: "microservices",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "destacame-architect",
        },
        technicalSkillId: {
          table: "skills",
          field: "codeName",
          value: "aws",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "destacame-architect",
        },
        technicalSkillId: {
          table: "skills",
          field: "codeName",
          value: "frontend-architecture",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "destacame-frontend",
        },
        technicalSkillId: {
          table: "skills",
          field: "codeName",
          value: "vue",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "destacame-frontend",
        },
        technicalSkillId: {
          table: "skills",
          field: "codeName",
          value: "nuxt",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "destacame-frontend",
        },
        technicalSkillId: {
          table: "skills",
          field: "codeName",
          value: "typescript",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "destacame-frontend",
        },
        technicalSkillId: {
          table: "skills",
          field: "codeName",
          value: "frontend-development",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "destacame-frontend",
        },
        technicalSkillId: {
          table: "skills",
          field: "codeName",
          value: "web-development",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "appinteli",
        },
        technicalSkillId: {
          table: "skills",
          field: "codeName",
          value: "erp",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "appinteli",
        },
        technicalSkillId: {
          table: "skills",
          field: "codeName",
          value: "ecommerce",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "appinteli",
        },
        technicalSkillId: {
          table: "skills",
          field: "codeName",
          value: "automation",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "appinteli",
        },
        technicalSkillId: {
          table: "skills",
          field: "codeName",
          value: "technical-knowledge",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "goodmeal",
        },
        technicalSkillId: {
          table: "skills",
          field: "codeName",
          value: "full-stack-development",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "goodmeal",
        },
        technicalSkillId: {
          table: "skills",
          field: "codeName",
          value: "vue3",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "goodmeal",
        },
        technicalSkillId: {
          table: "skills",
          field: "codeName",
          value: "scrum",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "goodmeal",
        },
        technicalSkillId: {
          table: "skills",
          field: "codeName",
          value: "bug-fixing",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "goodmeal",
        },
        technicalSkillId: {
          table: "skills",
          field: "codeName",
          value: "web-application",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "dibal",
        },
        technicalSkillId: {
          table: "skills",
          field: "codeName",
          value: "aws-deployment",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "dibal",
        },
        technicalSkillId: {
          table: "skills",
          field: "codeName",
          value: "laravel",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "dibal",
        },
        technicalSkillId: {
          table: "skills",
          field: "codeName",
          value: "system-architecture",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "dibal",
        },
        technicalSkillId: {
          table: "skills",
          field: "codeName",
          value: "microfrontend",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "dibal",
        },
        technicalSkillId: {
          table: "skills",
          field: "codeName",
          value: "ecommerce-development",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "dibal",
        },
        technicalSkillId: {
          table: "skills",
          field: "codeName",
          value: "cloud-computing",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "cofasa",
        },
        technicalSkillId: {
          table: "skills",
          field: "codeName",
          value: "production-monitoring",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "cofasa",
        },
        technicalSkillId: {
          table: "skills",
          field: "codeName",
          value: "productivity-analysis",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "cofasa",
        },
        technicalSkillId: {
          table: "skills",
          field: "codeName",
          value: "local-network",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "cofasa",
        },
        technicalSkillId: {
          table: "skills",
          field: "codeName",
          value: "jquery",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "cofasa",
        },
        technicalSkillId: {
          table: "skills",
          field: "codeName",
          value: "web-platform",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "iai",
        },
        technicalSkillId: {
          table: "skills",
          field: "codeName",
          value: "graduation-project",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "iai",
        },
        technicalSkillId: {
          table: "skills",
          field: "codeName",
          value: "technical-challenges",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "iai",
        },
        technicalSkillId: {
          table: "skills",
          field: "codeName",
          value: "solution-implementation",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "iai",
        },
        technicalSkillId: {
          table: "skills",
          field: "codeName",
          value: "technical-writing",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "iai",
        },
        technicalSkillId: {
          table: "skills",
          field: "codeName",
          value: "infrastructure-management",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "iai",
        },
        technicalSkillId: {
          table: "skills",
          field: "codeName",
          value: "software-development",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "iai",
        },
        technicalSkillId: {
          table: "skills",
          field: "codeName",
          value: "data-management",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "ipasme",
        },
        technicalSkillId: {
          table: "skills",
          field: "codeName",
          value: "medical-records",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "ipasme",
        },
        technicalSkillId: {
          table: "skills",
          field: "codeName",
          value: "desktop-application",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "ipasme",
        },
        technicalSkillId: {
          table: "skills",
          field: "codeName",
          value: "java",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "ipasme",
        },
        technicalSkillId: {
          table: "skills",
          field: "codeName",
          value: "object-oriented-programming",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "ipasme",
        },
        technicalSkillId: {
          table: "skills",
          field: "codeName",
          value: "requirements-gathering",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "corpoelec",
        },
        technicalSkillId: {
          table: "skills",
          field: "codeName",
          value: "inventory-management",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "corpoelec",
        },
        technicalSkillId: {
          table: "skills",
          field: "codeName",
          value: "php",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "corpoelec",
        },
        technicalSkillId: {
          table: "skills",
          field: "codeName",
          value: "crud",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "corpoelec",
        },
        technicalSkillId: {
          table: "skills",
          field: "codeName",
          value: "offline-system",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "corpoelec",
        },
        technicalSkillId: {
          table: "skills",
          field: "codeName",
          value: "asset-management",
        },
      },
    },
  ],
  worksSoftSkills: [
    // Destácame - Arquitecto Frontend y Desarrollador de Microservicios
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "destacame-architect",
        },
        skillId: {
          table: "skills",
          field: "codeName",
          value: "fintech",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "destacame-architect",
        },
        skillId: {
          table: "skills",
          field: "codeName",
          value: "strategic-planning",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "destacame-architect",
        },
        skillId: {
          table: "skills",
          field: "codeName",
          value: "adaptability",
        },
      },
    },

    // Destácame - Desarrollador Web Frontend
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "destacame-frontend",
        },
        skillId: {
          table: "skills",
          field: "codeName",
          value: "problem-solving",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "destacame-frontend",
        },
        skillId: {
          table: "skills",
          field: "codeName",
          value: "learning-agility",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "destacame-frontend",
        },
        skillId: {
          table: "skills",
          field: "codeName",
          value: "teamwork",
        },
      },
    },

    // AppInteli - Proyecto Personal
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "appinteli",
        },
        skillId: {
          table: "skills",
          field: "codeName",
          value: "project-management",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "appinteli",
        },
        skillId: {
          table: "skills",
          field: "codeName",
          value: "startup",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "appinteli",
        },
        skillId: {
          table: "skills",
          field: "codeName",
          value: "sales",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "appinteli",
        },
        skillId: {
          table: "skills",
          field: "codeName",
          value: "business-management",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "appinteli",
        },
        skillId: {
          table: "skills",
          field: "codeName",
          value: "customer-relationship",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "appinteli",
        },
        skillId: {
          table: "skills",
          field: "codeName",
          value: "self-motivation",
        },
      },
    },

    // GoodMeal - Desarrollador Web Full Stack
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "goodmeal",
        },
        skillId: {
          table: "skills",
          field: "codeName",
          value: "project-management",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "goodmeal",
        },
        skillId: {
          table: "skills",
          field: "codeName",
          value: "time-management",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "goodmeal",
        },
        skillId: {
          table: "skills",
          field: "codeName",
          value: "adaptability",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "goodmeal",
        },
        skillId: {
          table: "skills",
          field: "codeName",
          value: "problem-solving",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "goodmeal",
        },
        skillId: {
          table: "skills",
          field: "codeName",
          value: "teamwork",
        },
      },
    },

    // Dibal - Líder de Equipo de Desarrollo
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "dibal",
        },
        skillId: {
          table: "skills",
          field: "codeName",
          value: "team-leadership",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "dibal",
        },
        skillId: {
          table: "skills",
          field: "codeName",
          value: "agile-methodologies",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "dibal",
        },
        skillId: {
          table: "skills",
          field: "codeName",
          value: "team-management",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "dibal",
        },
        skillId: {
          table: "skills",
          field: "codeName",
          value: "customer-oriented",
        },
      },
    },

    // Cofasa - Desarrollador de Sistemas Web
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "cofasa",
        },
        skillId: {
          table: "skills",
          field: "codeName",
          value: "team-collaboration",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "cofasa",
        },
        skillId: {
          table: "skills",
          field: "codeName",
          value: "problem-solving",
        },
      },
    },

    // IAI - Freelance Proyectos de Grado
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "projects-degrees",
        },
        skillId: {
          table: "skills",
          field: "codeName",
          value: "project-direction",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "projects-degrees",
        },
        skillId: {
          table: "skills",
          field: "codeName",
          value: "team-collaboration",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "projects-degrees",
        },
        skillId: {
          table: "skills",
          field: "codeName",
          value: "technical-consulting",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "projects-degrees",
        },
        skillId: {
          table: "skills",
          field: "codeName",
          value: "time-management",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "projects-degrees",
        },
        skillId: {
          table: "skills",
          field: "codeName",
          value: "problem-solving",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "projects-degrees",
        },
        skillId: {
          table: "skills",
          field: "codeName",
          value: "adaptability",
        },
      },
    },

    // IAI - Freelance Desarrollo de Software y Arquitectura
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "iai",
        },
        skillId: {
          table: "skills",
          field: "codeName",
          value: "project-planning",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "iai",
        },
        skillId: {
          table: "skills",
          field: "codeName",
          value: "work-management",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "iai",
        },
        skillId: {
          table: "skills",
          field: "codeName",
          value: "budget-management",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "iai",
        },
        skillId: {
          table: "skills",
          field: "codeName",
          value: "project-management",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "iai",
        },
        skillId: {
          table: "skills",
          field: "codeName",
          value: "collaborative-work",
        },
      },
    },

    // IPASME - Desarrollador de Software
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "ipasme",
        },
        skillId: {
          table: "skills",
          field: "codeName",
          value: "technical-communication",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "ipasme",
        },
        skillId: {
          table: "skills",
          field: "codeName",
          value: "analytical-thinking",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "ipasme",
        },
        skillId: {
          table: "skills",
          field: "codeName",
          value: "problem-solving",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "ipasme",
        },
        skillId: {
          table: "skills",
          field: "codeName",
          value: "adaptability",
        },
      },
    },

    // Corpoelec - Desarrollador Web
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "corpoelec",
        },
        skillId: {
          table: "skills",
          field: "codeName",
          value: "problem-solving",
        },
      },
    },
    {
      relationship: {
        workId: {
          table: "works",
          field: "codeName",
          value: "corpoelec",
        },
        skillId: {
          table: "skills",
          field: "codeName",
          value: "team-collaboration",
        },
      },
    },
  ],
};
