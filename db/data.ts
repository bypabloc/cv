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
    },
    {
      codeName: "en",
      name: "English",
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
      description: "Contenedores para el despliegue de aplicaciones.",
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
      codeName: "names-bypabloc",
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
      codeName: "lastName-bypabloc",
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
      codeName: "email-bypabloc",
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
      codeName: "phone-bypabloc",
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
      codeName: "url-bypabloc",
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
      codeName: "label-bypabloc",
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
      codeName: "summary-bypabloc",
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
      codeName: "location-bypabloc",
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
      responsibilitiesNProjects: JSON.stringify([
        "Desarrollo y aprendizaje continuo en tecnologías full stack, incluyendo Python, Django y microservices, así como en el modelo de microfrontends.",
        "Participación en el desarrollo de productos en el sector fintech, como un sistema para ayudar a los usuarios a saldar deudas en Chile y otro proyecto en México para ofrecer créditos con diferentes niveles a los usuarios.",
        "Asignación a un equipo de optimización, encargado de desarrollar soluciones para mejorar el trabajo en diferentes áreas de la empresa, como un administrador de campañas que automatiza procesos que antes eran manuales.",
      ]),
      achievements: JSON.stringify([
        "Contribuí significativamente al desarrollo de productos financieros, adquiriendo conocimientos específicos del mercado fintech.",
        "Desarrollé habilidades en la creación de soluciones automatizadas, mejorando la eficiencia de procesos internos en la empresa.",
        "Adaptación a cambios y desafíos, incluyendo reducciones de personal, manteniendo un enfoque en la entrega de soluciones técnicas y estratégicas en mi actual rol en el equipo de plataforma.",
      ]),
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
      responsibilitiesNProjects: JSON.stringify([
        "Contratado inicialmente para trabajar en el área de frontend debido a habilidades sobresalientes demostradas en pruebas técnicas.",
        "Implementación de estándares y nuevas tecnologías en el desarrollo frontend, trabajando con Vue y Nuxt.js para mejorar la experiencia del usuario.",
        "Aprendizaje y aplicación progresiva de habilidades en el backend, enfocándome en Python y Django, para expandir mis capacidades como desarrollador full stack.",
      ]),
      achievements: JSON.stringify([
        "Mejoré significativamente la calidad y eficiencia del desarrollo frontend mediante la adopción de nuevas tecnologías y estándares.",
        "Desarrollé habilidades en Python y Django, superando los desafíos iniciales de falta de experiencia en estas tecnologías.",
        "Contribuí a la versatilidad y flexibilidad del equipo de desarrollo, adaptándome a necesidades cambiantes y aprendiendo nuevas habilidades.",
      ]),
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
      responsibilitiesNProjects: JSON.stringify([
        "Co-fundación y desarrollo de un ERP para tiendas pequeñas, enfocado en inventarios, ventas, compras y automatización de procesos como reportes y solicitudes de mercancía.",
        "Implementación de un e-commerce sencillo y accesible como parte del sistema, mejorando la interacción cliente-tienda.",
        "Atraer aproximadamente 10 clientes, manejando tanto el desarrollo como la parte comercial del proyecto.",
      ]),
      achievements: JSON.stringify([
        "Desarrollé habilidades en la creación y gestión de un proyecto empresarial desde cero, junto con la adquisición de conocimientos técnicos y comerciales.",
        "A pesar de que el proyecto no alcanzó el éxito esperado, obtuve experiencia valiosa en aspectos de desarrollo, ventas y gestión de un negocio.",
      ]),
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
      responsibilitiesNProjects: JSON.stringify([
        "Integración en una startup en crecimiento, trabajando bajo presión para satisfacer las demandas de los Project Managers y resolver bugs de manera eficiente",
        "Colaboración estrecha con un equipo talentoso, adoptando prácticas de Scrum, realizando reuniones diarias y mejorando las habilidades de trabajo en equipo",
        "Restructuración del frontend de la aplicación web, migrándolo a Vue 3 y utilizando tecnologías de vanguardia para mejorar la eficiencia y rendimiento",
      ]),
      achievements: JSON.stringify([
        "Superé los retos de trabajar en un ambiente de startup dinámico y en rápido crecimiento, entregando soluciones eficientes bajo plazos ajustados",
        "Lideré la migración y reestructuración del frontend hacia tecnologías más modernas, mejorando significativamente la experiencia de usuario y la eficiencia de la aplicación",
      ]),
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
      responsibilitiesNProjects: JSON.stringify([
        "Primer desarrollador contratado en la startup, contribuyendo al desarrollo de un sistema web para múltiples restaurantes usando jQuery y Laravel.",
        "Liderazgo del equipo de desarrollo, organizando e implementando arquitecturas adaptadas a las necesidades cambiantes del negocio.",
        "Desarrollo de un e-commerce en Vue que integra la gestión de restaurantes con la experiencia del cliente, minimizando la interacción humana.",
        "Encargado del despliegue de aplicaciones en AWS, utilizando servicios como EC2, RDS, S3, Route 53, SES, AutoScaling y LoadBalancer.",
      ]),
      achievements: JSON.stringify([
        "Contribuí al crecimiento de la startup, adaptándome y respondiendo eficazmente a las necesidades de los clientes.",
        "Lideré con éxito un equipo de desarrollo, facilitando el crecimiento de la empresa y la implementación de soluciones tecnológicas avanzadas.",
        "Implementé soluciones de comercio electrónico que mejoraron significativamente la experiencia del cliente y la eficiencia operativa de los restaurantes asociados.",
      ]),
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
      responsibilitiesNProjects: JSON.stringify([
        "Desarrollo de un sistema web para el monitoreo del proceso de producción, registrando paradas en las máquinas para análisis de productividad.",
        "Implementación del sistema en toda la empresa en red local, con acceso seguro mediante usuario y contraseña para cada empleado.",
        "Trabajo con tecnologías como jQuery y Laravel para crear una plataforma eficiente y fácil de usar.",
      ]),
      achievements: JSON.stringify([
        "Contribuí al aumento de la productividad mediante el análisis de datos generados por el sistema, permitiendo a la empresa tomar decisiones informadas para mejorar procesos.",
        "Entendí la verdadera importancia del trabajo en equipo, lo que resultó en una colaboración más efectiva y un proyecto exitoso.",
      ]),
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
      responsibilitiesNProjects: JSON.stringify([
        "Reestructuración y finalización del proyecto de grado de dos equipos que enfrentaron dificultades técnicas.",
        "Dirección e implementación completa de las soluciones necesarias para cumplir con los objetivos del proyecto.",
      ]),
      achievements: JSON.stringify([
        "Completé el proyecto que dos equipos no pudieron en meses en una semana, instruyendo sobre cada implementación y sus razones.",
      ]),
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
      responsibilitiesNProjects: JSON.stringify([
        "Liderazgo en el desarrollo e implementación de un sistema informático para la gestión de obras.",
        "Diseño y desarrollo de una arquitectura de red con una PC como servidor para acceso centralizado a datos.",
      ]),
      achievements: JSON.stringify([
        "Diseño exitoso y desarrollo de la arquitectura del sistema, garantizando una implementación eficiente y adaptada.",
        "Mejora significativa en la gestión de obras y presupuestos a través de interfaces de usuario desarrolladas.",
      ]),
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
      responsibilitiesNProjects: JSON.stringify([
        "Desarrollo e implementación de un sistema de gestión de historias médicas para pacientes.",
        "Creación de interfaces de escritorio en Java para Windows.",
      ]),
      achievements: JSON.stringify([
        "Aplicación de conceptos de POO y CRUDs en Java, mejorando mis habilidades técnicas.",
        "Mejora de habilidades de comunicación y levantamiento de requerimientos.",
      ]),
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
      responsibilitiesNProjects: JSON.stringify([
        "Implementación y mantenimiento de un sistema de inventario usando PHP y jQuery.",
        "Desarrollo de funcionalidades CRUD y asociación de equipos a personas.",
      ]),
      achievements: JSON.stringify([
        "Implementación exitosa del sistema en tres estados del país, operando de manera offline.",
      ]),
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
          value: "udemy",
        },
      },
      codeName: "udemy-web-development-bypabloc",
      area: "Desarrollo Web",
      learn:
        "En Udemy he tomado varios cursos de desarrollo web, entre ellos: JavaScript, React, Vue, Node, SQL, entre otros. Con la misma filosofía de aprender a mi ritmo y a mi tiempo pero siempre aprendiendo.",
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
          value: "youtube",
        },
      },
      codeName: "youtube-web-development-bypabloc",
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
      codeName: "uptyab-informatics-engineering-bypabloc",
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
      codeName: "innovator-destacame-2023",
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
      codeName: "triple-alianza-lima-2020",
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
      codeName: "es-bypabloc",
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
      codeName: "en-bypabloc",
      fluency: "Intermedio en lectura y básico en escritura y habla",
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
      codeName: "extension-faststruct",
      name: "FastStruct",
      description:
        "Una extensión de VS Code para visualizar y documentar rápidamente la estructura de archivos de su proyecto. FastStruct le ayuda a crear documentación clara y bien formateada de la estructura de directorios de su proyecto, incluido el contenido de los archivos cuando sea necesario.",
      highlights: JSON.stringify([
        "Solo por ocio aprender a hacer una extensión para VS Code y que me simplificara un proceso que tenia que hacer manual a la hora de interactuar con la IA.",
      ]),
      url: "https://marketplace.visualstudio.com/items?itemName=the-full-stack.faststruct",
      serviceStatus: "active",
    },
    {
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
      },
      codeName: "cv-bypabloc",
      name: "Curriculum Vitae",
      description:
        "Desarrollo de un currículum vitae en Astro para mostrar mis habilidades y experiencia laboral.",
      highlights: JSON.stringify([
        "Practicar mis habilidades de desarrollo web con Astro",
        "Mostrar mi experiencia laboral de forma clara y concisa",
      ]),
      url: "https://the-full-stack.com/",
      serviceStatus: "active",
    },
    {
      relationship: {
        userId: {
          table: "users",
          field: "username",
          value: "bypabloc",
        },
      },
      codeName: "appinteli-bypabloc",
      name: "ERP para pequeñas tiendas",
      description:
        "Co-fundador y desarrollador de un ERP enfocado en la automatización de procesos de inventario, ventas y compras para pequeñas tiendas.",
      highlights: JSON.stringify([
        "Desarrollo de una plataforma de comercio electrónico integrada",
        "Gestión de cliente y proyecto desde cero",
      ]),
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
      codeName: "alan-vergara-bravo",
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
      codeName: "alejandra-medina-briceno",
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
      codeName: "baldomero-aguila",
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
      codeName: "cristian-fuentes",
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
      codeName: "helis-montes",
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
      codeName: "edder-ramirez",
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
      codeName: "jose-namoc",
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
      codeName: "jacnelly-colmenarez",
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
      codeName: "felipe-rivera",
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
      codeName: "samuel-esponiza",
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

  // - Keywords
  // - Interests
  // - Works
  // - Skills
  // - Educations
  // - Awards
  // - LanguagesUsers
  // - References
  // - Projects
  // - UsersAttributes
  keywordsTranslations: [
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "keywords",
          field: "codeName",
          value: "data-analysis",
        },
      },
      tableName: "Keywords",
      field: "name",
      translatedValue: "Análisis de Datos",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "keywords",
          field: "codeName",
          value: "project-management",
        },
      },
      tableName: "Keywords",
      field: "name",
      translatedValue: "Gestión de Proyectos",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "keywords",
          field: "codeName",
          value: "automation",
        },
      },
      tableName: "Keywords",
      field: "name",
      translatedValue: "Automatización",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "keywords",
          field: "codeName",
          value: "bug-fixing",
        },
      },
      tableName: "Keywords",
      field: "name",
      translatedValue: "Corrección de Errores",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "keywords",
          field: "codeName",
          value: "team-leadership",
        },
      },
      tableName: "Keywords",
      field: "name",
      translatedValue: "Liderazgo de Equipo",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "keywords",
          field: "codeName",
          value: "system-architecture",
        },
      },
      tableName: "Keywords",
      field: "name",
      translatedValue: "Arquitectura de Sistemas",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "keywords",
          field: "codeName",
          value: "production-monitoring",
        },
      },
      tableName: "Keywords",
      field: "name",
      translatedValue: "Monitoreo de Producción",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "keywords",
          field: "codeName",
          value: "productivity-analysis",
        },
      },
      tableName: "Keywords",
      field: "name",
      translatedValue: "Análisis de Productividad",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "keywords",
          field: "codeName",
          value: "local-network",
        },
      },
      tableName: "Keywords",
      field: "name",
      translatedValue: "Red Local",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "keywords",
          field: "codeName",
          value: "web-platform",
        },
      },
      tableName: "Keywords",
      field: "name",
      translatedValue: "Plataforma Web",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "keywords",
          field: "codeName",
          value: "graduation-project",
        },
      },
      tableName: "Keywords",
      field: "name",
      translatedValue: "Proyecto de Grado",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "keywords",
          field: "codeName",
          value: "technical-challenges",
        },
      },
      tableName: "Keywords",
      field: "name",
      translatedValue: "Desafíos Técnicos",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "keywords",
          field: "codeName",
          value: "project-direction",
        },
      },
      tableName: "Keywords",
      field: "name",
      translatedValue: "Dirección de Proyecto",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "keywords",
          field: "codeName",
          value: "solution-implementation",
        },
      },
      tableName: "Keywords",
      field: "name",
      translatedValue: "Implementación de Solución",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "keywords",
          field: "codeName",
          value: "team-collaboration",
        },
      },
      tableName: "Keywords",
      field: "name",
      translatedValue: "Colaboración de Equipo",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "keywords",
          field: "codeName",
          value: "infrastructure-management",
        },
      },
      tableName: "Keywords",
      field: "name",
      translatedValue: "Gestión de Infraestructura",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "keywords",
          field: "codeName",
          value: "network-architecture",
        },
      },
      tableName: "Keywords",
      field: "name",
      translatedValue: "Arquitectura de Redes",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "keywords",
          field: "codeName",
          value: "project-planning",
        },
      },
      tableName: "Keywords",
      field: "name",
      translatedValue: "Planificación de Proyecto",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "keywords",
          field: "codeName",
          value: "work-management",
        },
      },
      tableName: "Keywords",
      field: "name",
      translatedValue: "Gestión de Trabajo",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "keywords",
          field: "codeName",
          value: "budget-management",
        },
      },
      tableName: "Keywords",
      field: "name",
      translatedValue: "Gestión de Presupuesto",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "keywords",
          field: "codeName",
          value: "medical-records",
        },
      },
      tableName: "Keywords",
      field: "name",
      translatedValue: "Historias Clínicas",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "keywords",
          field: "codeName",
          value: "desktop-application",
        },
      },
      tableName: "Keywords",
      field: "name",
      translatedValue: "Aplicación de Escritorio",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "keywords",
          field: "codeName",
          value: "object-oriented-programming",
        },
      },
      tableName: "Keywords",
      field: "name",
      translatedValue: "Programación Orientada a Objetos",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "keywords",
          field: "codeName",
          value: "requirements-gathering",
        },
      },
      tableName: "Keywords",
      field: "name",
      translatedValue: "Recolección de Requisitos",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "keywords",
          field: "codeName",
          value: "inventory-management",
        },
      },
      tableName: "Keywords",
      field: "name",
      translatedValue: "Gestión de Inventario",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "keywords",
          field: "codeName",
          value: "offline-system",
        },
      },
      tableName: "Keywords",
      field: "name",
      translatedValue: "Sistema Offline",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "keywords",
          field: "codeName",
          value: "asset-management",
        },
      },
      tableName: "Keywords",
      field: "name",
      translatedValue: "Gestión de Activos",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "keywords",
          field: "codeName",
          value: "data-analysis",
        },
      },
      tableName: "Keywords",
      field: "name",
      translatedValue: "Data Analysis",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "keywords",
          field: "codeName",
          value: "project-management",
        },
      },
      tableName: "Keywords",
      field: "name",
      translatedValue: "Project Management",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "keywords",
          field: "codeName",
          value: "automation",
        },
      },
      tableName: "Keywords",
      field: "name",
      translatedValue: "Automation",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "keywords",
          field: "codeName",
          value: "bug-fixing",
        },
      },
      tableName: "Keywords",
      field: "name",
      translatedValue: "Bug Fixing",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "keywords",
          field: "codeName",
          value: "team-leadership",
        },
      },
      tableName: "Keywords",
      field: "name",
      translatedValue: "Team Leadership",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "keywords",
          field: "codeName",
          value: "system-architecture",
        },
      },
      tableName: "Keywords",
      field: "name",
      translatedValue: "System Architecture",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "keywords",
          field: "codeName",
          value: "production-monitoring",
        },
      },
      tableName: "Keywords",
      field: "name",
      translatedValue: "Production Monitoring",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "keywords",
          field: "codeName",
          value: "productivity-analysis",
        },
      },
      tableName: "Keywords",
      field: "name",
      translatedValue: "Productivity Analysis",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "keywords",
          field: "codeName",
          value: "local-network",
        },
      },
      tableName: "Keywords",
      field: "name",
      translatedValue: "Local Network",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "keywords",
          field: "codeName",
          value: "web-platform",
        },
      },
      tableName: "Keywords",
      field: "name",
      translatedValue: "Web Platform",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "keywords",
          field: "codeName",
          value: "graduation-project",
        },
      },
      tableName: "Keywords",
      field: "name",
      translatedValue: "Graduation Project",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "keywords",
          field: "codeName",
          value: "technical-challenges",
        },
      },
      tableName: "Keywords",
      field: "name",
      translatedValue: "Technical Challenges",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "keywords",
          field: "codeName",
          value: "project-direction",
        },
      },
      tableName: "Keywords",
      field: "name",
      translatedValue: "Project Direction",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "keywords",
          field: "codeName",
          value: "solution-implementation",
        },
      },
      tableName: "Keywords",
      field: "name",
      translatedValue: "Solution Implementation",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "keywords",
          field: "codeName",
          value: "team-collaboration",
        },
      },
      tableName: "Keywords",
      field: "name",
      translatedValue: "Team Collaboration",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "keywords",
          field: "codeName",
          value: "infrastructure-management",
        },
      },
      tableName: "Keywords",
      field: "name",
      translatedValue: "Infrastructure Management",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "keywords",
          field: "codeName",
          value: "network-architecture",
        },
      },
      tableName: "Keywords",
      field: "name",
      translatedValue: "Network Architecture",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "keywords",
          field: "codeName",
          value: "project-planning",
        },
      },
      tableName: "Keywords",
      field: "name",
      translatedValue: "Project Planning",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "keywords",
          field: "codeName",
          value: "work-management",
        },
      },
      tableName: "Keywords",
      field: "name",
      translatedValue: "Work Management",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "keywords",
          field: "codeName",
          value: "budget-management",
        },
      },
      tableName: "Keywords",
      field: "name",
      translatedValue: "Budget Management",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "keywords",
          field: "codeName",
          value: "medical-records",
        },
      },
      tableName: "Keywords",
      field: "name",
      translatedValue: "Medical Records",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "keywords",
          field: "codeName",
          value: "desktop-application",
        },
      },
      tableName: "Keywords",
      field: "name",
      translatedValue: "Desktop Application",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "keywords",
          field: "codeName",
          value: "object-oriented-programming",
        },
      },
      tableName: "Keywords",
      field: "name",
      translatedValue: "Object-Oriented Programming",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "keywords",
          field: "codeName",
          value: "requirements-gathering",
        },
      },
      tableName: "Keywords",
      field: "name",
      translatedValue: "Requirements Gathering",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "keywords",
          field: "codeName",
          value: "inventory-management",
        },
      },
      tableName: "Keywords",
      field: "name",
      translatedValue: "Inventory Management",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "keywords",
          field: "codeName",
          value: "offline-system",
        },
      },
      tableName: "Keywords",
      field: "name",
      translatedValue: "Offline System",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "keywords",
          field: "codeName",
          value: "asset-management",
        },
      },
      tableName: "Keywords",
      field: "name",
      translatedValue: "Asset Management",
    },
  ],
  interestsTranslations: [
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "interests",
          field: "codeName",
          value: "bot-creation",
        },
      },
      tableName: "Interests",
      field: "name",
      translatedValue: "Creación de Bots",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "interests",
          field: "codeName",
          value: "bot-creation",
        },
      },
      tableName: "Interests",
      field: "name",
      translatedValue: "Bot Creation",
    },
  ],
  worksTranslations: [
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "destacame-architect",
        },
      },
      tableName: "Works",
      field: "position",
      translatedValue: "Frontend Architect and Microservices Developer",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "destacame-architect",
        },
      },
      tableName: "Works",
      field: "responsibilitiesNProjects",
      translatedValue: JSON.stringify([
        "Continuous development and learning in full stack technologies, including Python, Django, and microservices, as well as in the microfrontends model.",
        "Participation in product development in the fintech sector, such as a system to help users pay off debts in Chile and another project in Mexico to offer credits with different levels to users.",
        "Assignment to an optimization team, responsible for developing solutions to improve work in different areas of the company, such as a campaign manager that automates processes that were previously manual.",
      ]),
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "destacame-architect",
        },
      },
      tableName: "Works",
      field: "achievements",
      translatedValue: JSON.stringify([
        "I significantly contributed to the development of financial products, acquiring specific knowledge of the fintech market.",
        "I developed skills in creating automated solutions, improving the efficiency of internal processes in the company.",
        "Adaptation to changes and challenges, including staff reductions, maintaining a focus on delivering technical and strategic solutions in my current role in the platform team.",
      ]),
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "destacame-frontend",
        },
      },
      tableName: "Works",
      field: "position",
      translatedValue: "Frontend Web Developer",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "destacame-frontend",
        },
      },
      tableName: "Works",
      field: "responsibilitiesNProjects",
      translatedValue: JSON.stringify([
        "Initially hired to work in the frontend area due to outstanding skills demonstrated in technical tests.",
        "Implementation of standards and new technologies in frontend development, working with Vue and Nuxt.js to improve the user experience.",
        "Progressive learning and application of backend skills, focusing on Python and Django, to expand my capabilities as a full stack developer.",
      ]),
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "destacame-frontend",
        },
      },
      tableName: "Works",
      field: "achievements",
      translatedValue: JSON.stringify([
        "I significantly improved the quality and efficiency of frontend development through the adoption of new technologies and standards.",
        "I developed skills in Python and Django, overcoming the initial challenges of lack of experience in these technologies.",
        "I contributed to the versatility and flexibility of the development team, adapting to changing needs and learning new skills.",
      ]),
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "appinteli",
        },
      },
      tableName: "Works",
      field: "position",
      translatedValue: "Co-founder and Developer",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "appinteli",
        },
      },
      tableName: "Works",
      field: "responsibilitiesNProjects",
      translatedValue: JSON.stringify([
        "Co-founding and developing an ERP for small stores, focused on inventory, sales, purchases, and automation of processes such as reports and merchandise requests.",
        "Implementation of a simple and accessible e-commerce as part of the system, improving client-store interaction.",
        "Attracting approximately 10 clients, managing both development and the commercial side of the project.",
      ]),
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "appinteli",
        },
      },
      tableName: "Works",
      field: "achievements",
      translatedValue: JSON.stringify([
        "I developed skills in creating and managing a business project from scratch, along with gaining technical and commercial knowledge.",
        "Despite the project not achieving the expected success, I gained valuable experience in development, sales, and business management aspects.",
      ]),
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "goodmeal",
        },
      },
      tableName: "Works",
      field: "position",
      translatedValue: "Full Stack Web Developer",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "goodmeal",
        },
      },
      tableName: "Works",
      field: "responsibilitiesNProjects",
      translatedValue: JSON.stringify([
        "Integration into a growing startup, working under pressure to meet Project Managers' demands and efficiently solve bugs.",
        "Close collaboration with a talented team, adopting Scrum practices, conducting daily meetings, and improving teamwork skills.",
        "Restructuring the frontend of the web application, migrating it to Vue 3 and using cutting-edge technologies to improve efficiency and performance.",
      ]),
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "goodmeal",
        },
      },
      tableName: "Works",
      field: "achievements",
      translatedValue: JSON.stringify([
        "I overcame the challenges of working in a dynamic and fast-growing startup environment, delivering efficient solutions under tight deadlines.",
        "I led the migration and restructuring of the frontend towards more modern technologies, significantly improving user experience and application efficiency.",
      ]),
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "dibal",
        },
      },
      tableName: "Works",
      field: "position",
      translatedValue: "Development Team Leader and Developer",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "dibal",
        },
      },
      tableName: "Works",
      field: "responsibilitiesNProjects",
      translatedValue: JSON.stringify([
        "First developer hired in the startup, contributing to the development of a web system for multiple restaurants using jQuery and Laravel.",
        "Leadership of the development team, organizing and implementing architectures adapted to the changing needs of the business.",
        "Development of an e-commerce in Vue that integrates restaurant management with customer experience, minimizing human interaction.",
        "Responsible for application deployment on AWS, using services such as EC2, RDS, S3, Route 53, SES, AutoScaling, and LoadBalancer.",
      ]),
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "dibal",
        },
      },
      tableName: "Works",
      field: "achievements",
      translatedValue: JSON.stringify([
        "I contributed to the growth of the startup, adapting and responding effectively to client needs.",
        "I successfully led a development team, facilitating the company's growth and the implementation of advanced technological solutions.",
        "I implemented e-commerce solutions that significantly improved the customer experience and operational efficiency of associated restaurants.",
      ]),
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "cofasa",
        },
      },
      tableName: "Works",
      field: "position",
      translatedValue: "Web Systems Developer",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "cofasa",
        },
      },
      tableName: "Works",
      field: "responsibilitiesNProjects",
      translatedValue: JSON.stringify([
        "Development of a web system for monitoring the production process, recording machine stoppages for productivity analysis.",
        "Implementation of the system throughout the company on a local network, with secure access via username and password for each employee.",
        "Working with technologies such as jQuery and Laravel to create an efficient and user-friendly platform.",
      ]),
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "cofasa",
        },
      },
      tableName: "Works",
      field: "achievements",
      translatedValue: JSON.stringify([
        "I contributed to increased productivity through the analysis of data generated by the system, enabling the company to make informed decisions to improve processes.",
        "I understood the true importance of teamwork, resulting in more effective collaboration and a successful project.",
      ]),
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "projects-degrees",
        },
      },
      tableName: "Works",
      field: "position",
      translatedValue: "Leader, Architect, and Developer",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "projects-degrees",
        },
      },
      tableName: "Works",
      field: "responsibilitiesNProjects",
      translatedValue: JSON.stringify([
        "Restructuring and completion of the graduation project for two teams that faced technical difficulties.",
        "Complete direction and implementation of the necessary solutions to meet the project's objectives.",
      ]),
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "projects-degrees",
        },
      },
      tableName: "Works",
      field: "achievements",
      translatedValue: JSON.stringify([
        "I completed the project that two teams could not finish in months within a week, instructing on each implementation and its reasons.",
      ]),
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "iai",
        },
      },
      tableName: "Works",
      field: "position",
      translatedValue: "Software Development Leader and Systems Architecture",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "iai",
        },
      },
      tableName: "Works",
      field: "responsibilitiesNProjects",
      translatedValue: JSON.stringify([
        "Leadership in the development and implementation of a computer system for project management.",
        "Design and development of a network architecture with a PC as a server for centralized data access.",
      ]),
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "iai",
        },
      },
      tableName: "Works",
      field: "achievements",
      translatedValue: JSON.stringify([
        "Successful design and development of the system architecture, ensuring efficient and adapted implementation.",
        "Significant improvement in project and budget management through developed user interfaces.",
      ]),
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "ipasme",
        },
      },
      tableName: "Works",
      field: "position",
      translatedValue: "Software Developer",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "ipasme",
        },
      },
      tableName: "Works",
      field: "responsibilitiesNProjects",
      translatedValue: JSON.stringify([
        "Development and implementation of a medical records management system for patients.",
        "Creation of desktop interfaces in Java for Windows.",
      ]),
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "ipasme",
        },
      },
      tableName: "Works",
      field: "achievements",
      translatedValue: JSON.stringify([
        "Application of OOP concepts and CRUDs in Java, improving my technical skills.",
        "Improvement of communication and requirements gathering skills.",
      ]),
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "corpoelec",
        },
      },
      tableName: "Works",
      field: "position",
      translatedValue: "Web Developer",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "corpoelec",
        },
      },
      tableName: "Works",
      field: "responsibilitiesNProjects",
      translatedValue: JSON.stringify([
        "Implementation and maintenance of an inventory system using PHP and jQuery.",
        "Development of CRUD functionalities and association of equipment to people.",
      ]),
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "corpoelec",
        },
      },
      tableName: "Works",
      field: "achievements",
      translatedValue: JSON.stringify([
        "Successful implementation of the system in three states of the country, operating offline.",
      ]),
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "destacame-architect",
        },
      },
      tableName: "Works",
      field: "position",
      translatedValue: "Arquitecto Frontend y Desarrollador de Microservicios",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "destacame-architect",
        },
      },
      tableName: "Works",
      field: "responsibilitiesNProjects",
      translatedValue: JSON.stringify([
        "Desarrollo y aprendizaje continuo en tecnologías full stack, incluyendo Python, Django y microservices, así como en el modelo de microfrontends.",
        "Participación en el desarrollo de productos en el sector fintech, como un sistema para ayudar a los usuarios a saldar deudas en Chile y otro proyecto en México para ofrecer créditos con diferentes niveles a los usuarios.",
        "Asignación a un equipo de optimización, encargado de desarrollar soluciones para mejorar el trabajo en diferentes áreas de la empresa, como un administrador de campañas que automatiza procesos que antes eran manuales.",
      ]),
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "destacame-architect",
        },
      },
      tableName: "Works",
      field: "achievements",
      translatedValue: JSON.stringify([
        "Contribuí significativamente al desarrollo de productos financieros, adquiriendo conocimientos específicos del mercado fintech.",
        "Desarrollé habilidades en la creación de soluciones automatizadas, mejorando la eficiencia de procesos internos en la empresa.",
        "Adaptación a cambios y desafíos, incluyendo reducciones de personal, manteniendo un enfoque en la entrega de soluciones técnicas y estratégicas en mi actual rol en el equipo de plataforma.",
      ]),
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "destacame-frontend",
        },
      },
      tableName: "Works",
      field: "position",
      translatedValue: "Desarrollador Web Frontend",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "destacame-frontend",
        },
      },
      tableName: "Works",
      field: "responsibilitiesNProjects",
      translatedValue: JSON.stringify([
        "Contratado inicialmente para trabajar en el área de frontend debido a habilidades sobresalientes demostradas en pruebas técnicas.",
        "Implementación de estándares y nuevas tecnologías en el desarrollo frontend, trabajando con Vue y Nuxt.js para mejorar la experiencia del usuario.",
        "Aprendizaje y aplicación progresiva de habilidades en el backend, enfocándome en Python y Django, para expandir mis capacidades como desarrollador full stack.",
      ]),
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "destacame-frontend",
        },
      },
      tableName: "Works",
      field: "achievements",
      translatedValue: JSON.stringify([
        "Mejoré significativamente la calidad y eficiencia del desarrollo frontend mediante la adopción de nuevas tecnologías y estándares.",
        "Desarrollé habilidades en Python y Django, superando los desafíos iniciales de falta de experiencia en estas tecnologías.",
        "Contribuí a la versatilidad y flexibilidad del equipo de desarrollo, adaptándome a necesidades cambiantes y aprendiendo nuevas habilidades.",
      ]),
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "appinteli",
        },
      },
      tableName: "Works",
      field: "position",
      translatedValue: "Co-fundador y Desarrollador",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "appinteli",
        },
      },
      tableName: "Works",
      field: "responsibilitiesNProjects",
      translatedValue: JSON.stringify([
        "Co-fundación y desarrollo de un ERP para tiendas pequeñas, enfocado en inventarios, ventas, compras y automatización de procesos como reportes y solicitudes de mercancía.",
        "Implementación de un e-commerce sencillo y accesible como parte del sistema, mejorando la interacción cliente-tienda.",
        "Atraer aproximadamente 10 clientes, manejando tanto el desarrollo como la parte comercial del proyecto.",
      ]),
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "appinteli",
        },
      },
      tableName: "Works",
      field: "achievements",
      translatedValue: JSON.stringify([
        "Desarrollé habilidades en la creación y gestión de un proyecto empresarial desde cero, junto con la adquisición de conocimientos técnicos y comerciales.",
        "A pesar de que el proyecto no alcanzó el éxito esperado, obtuve experiencia valiosa en aspectos de desarrollo, ventas y gestión de un negocio.",
      ]),
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "goodmeal",
        },
      },
      tableName: "Works",
      field: "position",
      translatedValue: "Desarrollador Web Full Stack",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "goodmeal",
        },
      },
      tableName: "Works",
      field: "responsibilitiesNProjects",
      translatedValue: JSON.stringify([
        "Integración en una startup en crecimiento, trabajando bajo presión para satisfacer las demandas de los Project Managers y resolver bugs de manera eficiente",
        "Colaboración estrecha con un equipo talentoso, adoptando prácticas de Scrum, realizando reuniones diarias y mejorando las habilidades de trabajo en equipo",
        "Restructuración del frontend de la aplicación web, migrándolo a Vue 3 y utilizando tecnologías de vanguardia para mejorar la eficiencia y rendimiento",
      ]),
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "goodmeal",
        },
      },
      tableName: "Works",
      field: "achievements",
      translatedValue: JSON.stringify([
        "Superé los retos de trabajar en un ambiente de startup dinámico y en rápido crecimiento, entregando soluciones eficientes bajo plazos ajustados",
        "Lideré la migración y reestructuración del frontend hacia tecnologías más modernas, mejorando significativamente la experiencia de usuario y la eficiencia de la aplicación",
      ]),
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "dibal",
        },
      },
      tableName: "Works",
      field: "position",
      translatedValue: "Líder de Equipo de Desarrollo y Desarrollador",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "dibal",
        },
      },
      tableName: "Works",
      field: "responsibilitiesNProjects",
      translatedValue: JSON.stringify([
        "Primer desarrollador contratado en la startup, contribuyendo al desarrollo de un sistema web para múltiples restaurantes usando jQuery y Laravel.",
        "Liderazgo del equipo de desarrollo, organizando e implementando arquitecturas adaptadas a las necesidades cambiantes del negocio.",
        "Desarrollo de un e-commerce en Vue que integra la gestión de restaurantes con la experiencia del cliente, minimizando la interacción humana.",
        "Encargado del despliegue de aplicaciones en AWS, utilizando servicios como EC2, RDS, S3, Route 53, SES, AutoScaling y LoadBalancer.",
      ]),
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "dibal",
        },
      },
      tableName: "Works",
      field: "achievements",
      translatedValue: JSON.stringify([
        "Contribuí al crecimiento de la startup, adaptándome y respondiendo eficazmente a las necesidades de los clientes.",
        "Lideré con éxito un equipo de desarrollo, facilitando el crecimiento de la empresa y la implementación de soluciones tecnológicas avanzadas.",
        "Implementé soluciones de comercio electrónico que mejoraron significativamente la experiencia del cliente y la eficiencia operativa de los restaurantes asociados.",
      ]),
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "cofasa",
        },
      },
      tableName: "Works",
      field: "position",
      translatedValue: "Desarrollador de Sistemas Web",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "cofasa",
        },
      },
      tableName: "Works",
      field: "responsibilitiesNProjects",
      translatedValue: JSON.stringify([
        "Desarrollo de un sistema web para el monitoreo del proceso de producción, registrando paradas en las máquinas para análisis de productividad.",
        "Implementación del sistema en toda la empresa en red local, con acceso seguro mediante usuario y contraseña para cada empleado.",
        "Trabajo con tecnologías como jQuery y Laravel para crear una plataforma eficiente y fácil de usar.",
      ]),
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "cofasa",
        },
      },
      tableName: "Works",
      field: "achievements",
      translatedValue: JSON.stringify([
        "Contribuí al aumento de la productividad mediante el análisis de datos generados por el sistema, permitiendo a la empresa tomar decisiones informadas para mejorar procesos.",
        "Entendí la verdadera importancia del trabajo en equipo, lo que resultó en una colaboración más efectiva y un proyecto exitoso.",
      ]),
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "projects-degrees",
        },
      },
      tableName: "Works",
      field: "position",
      translatedValue: "Líder, Arquitecto y Desarrollador",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "projects-degrees",
        },
      },
      tableName: "Works",
      field: "responsibilitiesNProjects",
      translatedValue: JSON.stringify([
        "Reestructuración y finalización del proyecto de grado de dos equipos que enfrentaron dificultades técnicas.",
        "Dirección e implementación completa de las soluciones necesarias para cumplir con los objetivos del proyecto.",
      ]),
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "projects-degrees",
        },
      },
      tableName: "Works",
      field: "achievements",
      translatedValue: JSON.stringify([
        "Completé el proyecto que dos equipos no pudieron en meses en una semana, instruyendo sobre cada implementación y sus razones.",
      ]),
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "iai",
        },
      },
      tableName: "Works",
      field: "position",
      translatedValue:
        "Líder de Desarrollo de software y Arquitectura de Sistemas",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "iai",
        },
      },
      tableName: "Works",
      field: "responsibilitiesNProjects",
      translatedValue: JSON.stringify([
        "Liderazgo en el desarrollo e implementación de un sistema informático para la gestión de obras.",
        "Diseño y desarrollo de una arquitectura de red con una PC como servidor para acceso centralizado a datos.",
      ]),
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "iai",
        },
      },
      tableName: "Works",
      field: "achievements",
      translatedValue: JSON.stringify([
        "Diseño exitoso y desarrollo de la arquitectura del sistema, garantizando una implementación eficiente y adaptada.",
        "Mejora significativa en la gestión de obras y presupuestos a través de interfaces de usuario desarrolladas.",
      ]),
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "ipasme",
        },
      },
      tableName: "Works",
      field: "position",
      translatedValue: "Desarrollador de software",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "ipasme",
        },
      },
      tableName: "Works",
      field: "responsibilitiesNProjects",
      translatedValue: JSON.stringify([
        "Desarrollo e implementación de un sistema de gestión de historias médicas para pacientes.",
        "Creación de interfaces de escritorio en Java para Windows.",
      ]),
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "ipasme",
        },
      },
      tableName: "Works",
      field: "achievements",
      translatedValue: JSON.stringify([
        "Aplicación de conceptos de POO y CRUDs en Java, mejorando mis habilidades técnicas.",
        "Mejora de habilidades de comunicación y levantamiento de requerimientos.",
      ]),
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "corpoelec",
        },
      },
      tableName: "Works",
      field: "position",
      translatedValue: "Desarrollador web",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "corpoelec",
        },
      },
      tableName: "Works",
      field: "responsibilitiesNProjects",
      translatedValue: JSON.stringify([
        "Implementación y mantenimiento de un sistema de inventario usando PHP y jQuery.",
        "Desarrollo de funcionalidades CRUD y asociación de equipos a personas.",
      ]),
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "works",
          field: "codeName",
          value: "corpoelec",
        },
      },
      tableName: "Works",
      field: "achievements",
      translatedValue: JSON.stringify([
        "Implementación exitosa del sistema en tres estados del país, operando de manera offline.",
      ]),
    },
  ],
  skillsTranslations: [
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "docker",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Docker",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "docker",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Container platform for application development.",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "docker",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Docker",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "docker",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue:
        "Plataforma de contenedores para el desarrollo de aplicaciones.",
    },
    // Kubernetes
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "kubernetes" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Kubernetes",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "kubernetes" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Container orchestrator for application deployment.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "kubernetes" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Kubernetes",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "kubernetes" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue:
        "Orquestador de contenedores para el despliegue de aplicaciones.",
    },
    // React
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "react" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "React",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "react" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "JavaScript framework for building user interfaces.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "react" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "React",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "react" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue:
        "Framework JavaScript para la creación de interfaces de usuario.",
    },
    // Node.js
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "node" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Node.js",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "node" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue:
        "JavaScript runtime environment for backend development.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "node" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Node.js",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "node" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue:
        "Entorno de ejecución de JavaScript para el desarrollo de aplicaciones backend.",
    },
    // SQL
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "sql" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "SQL",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "sql" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Structured Query Language for databases.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "sql" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "SQL",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "sql" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Lenguaje de consulta estructurado para bases de datos.",
    },
    // Python
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "python" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Python",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "python" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue:
        "Programming language used in microservices development.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "python" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Python",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "python" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue:
        "Lenguaje de programación utilizado en el desarrollo de microservicios.",
    },
    // Django
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "django" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Django",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "django" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Web framework for Python used in backend development.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "django" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Django",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "django" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue:
        "Framework web para Python utilizado en el desarrollo de backend.",
    },
    // Microservices
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "microservices",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Microservices",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "microservices",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue:
        "Microservices architecture for scalable application development.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "microservices",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Microservicios",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "microservices",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue:
        "Arquitectura de microservicios para el desarrollo de aplicaciones escalables.",
    },
    // AWS
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "aws" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "AWS",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "aws" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue:
        "Cloud services platform used for deployment and hosting.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "aws" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "AWS",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "aws" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue:
        "Plataforma de servicios en la nube utilizada para implementación y despliegue.",
    },
    // Frontend Architecture
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "frontend-architecture",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Frontend Architecture",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "frontend-architecture",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Design of frontend application architecture.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "frontend-architecture",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Arquitectura Frontend",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "frontend-architecture",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Diseño de la arquitectura de la aplicación frontend.",
    },
    // Optimization
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "optimization" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Optimization",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "optimization" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Improvement of system efficiency and performance.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "optimization" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Optimización",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "optimization" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue:
        "Mejora de la eficiencia y el rendimiento de los sistemas.",
    },
    // Automation
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "automation" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Automation",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "automation" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Process automation to improve efficiency.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "automation" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Automatización",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "automation" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Automatización de procesos para mejorar la eficiencia.",
    },
    // Fintech
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "fintech" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Fintech",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "fintech" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Specific knowledge of the financial market.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "fintech" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Fintech",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "fintech" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Conocimiento específico del mercado financiero.",
    },
    // Strategic Planning
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "strategic-planning",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Strategic Planning",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "strategic-planning",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Strategic planning for delivering solutions.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "strategic-planning",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Planificación Estratégica",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "strategic-planning",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue:
        "Planificación estratégica para la entrega de soluciones.",
    },
    // Vue.js
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "vue" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Vue.js",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "vue" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "JavaScript framework for building user interfaces.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "vue" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Vue.js",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "vue" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue:
        "Framework JavaScript para la creación de interfaces de usuario.",
    },
    // Nuxt.js
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "nuxt" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Nuxt.js",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "nuxt" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Web development framework based on Vue.js.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "nuxt" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Nuxt.js",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "nuxt" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Framework de desarrollo web basado en Vue.js.",
    },
    // TypeScript
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "typescript" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "TypeScript",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "typescript" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Typed programming language.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "typescript" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "TypeScript",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "typescript" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Lenguaje de programación tipado.",
    },
    // Frontend Development
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "frontend-development",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Frontend Development",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "frontend-development",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Frontend development to improve user experience.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "frontend-development",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Desarrollo Frontend",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "frontend-development",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue:
        "Desarrollo frontend para mejorar la experiencia del usuario.",
    },
    // Web Development
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "web-development",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Web Development",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "web-development",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Web application development.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "web-development",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Desarrollo Web",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "web-development",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Desarrollo de aplicaciones web.",
    },
    // Quality Improvement
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "quality-improvement",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Quality Improvement",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "quality-improvement",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Improving software development quality.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "quality-improvement",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Mejora de Calidad",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "quality-improvement",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Mejora de la calidad en el desarrollo de software.",
    },
    // Backend Development
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "backend-development",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Backend Development",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "backend-development",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue:
        "Backend application development with Python and Django.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "backend-development",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Desarrollo Backend",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "backend-development",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue:
        "Desarrollo de aplicaciones backend con Python y Django.",
    },
    // Learning Agility
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "learning-agility",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Learning Agility",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "learning-agility",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Ability to learn and apply new technologies.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "learning-agility",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Agilidad de Aprendizaje",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "learning-agility",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Habilidad para aprender y aplicar nuevas tecnologías.",
    },
    // ERP
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "erp" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "ERP",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "erp" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Enterprise resource planning systems development.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "erp" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "ERP",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "erp" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue:
        "Desarrollo de sistemas de planificación de recursos empresariales.",
    },
    // E-commerce
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "ecommerce" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "E-commerce",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "ecommerce" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "E-commerce solutions development.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "ecommerce" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "E-commerce",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "ecommerce" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Desarrollo de soluciones de comercio electrónico.",
    },
    // Startup
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "startup" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Startup",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "startup" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Management and development of startups.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "startup" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Startup",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "startup" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Gestión y desarrollo de startups.",
    },
    // Technical Knowledge
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "technical-knowledge",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Technical Knowledge",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "technical-knowledge",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Technical knowledge in multiple areas.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "technical-knowledge",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Conocimiento Técnico",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "technical-knowledge",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Conocimientos técnicos en múltiples áreas.",
    },
    // Sales
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "sales" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Sales",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "sales" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Handling sales and clients.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "sales" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Ventas",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "sales" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Manejo de ventas y clientes.",
    },
    // Business Management
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "business-management",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Business Management",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "business-management",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Business management.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "business-management",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Gestión Empresarial",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "business-management",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Gestión empresarial.",
    },
    // Customer Relationship
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "customer-relationship",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Customer Relationship",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "customer-relationship",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Customer relationship management.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "customer-relationship",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Relación con el Cliente",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "customer-relationship",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Gestión de relaciones con los clientes.",
    },
    // Self Motivation
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "self-motivation",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Self Motivation",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "self-motivation",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue:
        "Self-motivation and ability to manage personal projects.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "self-motivation",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Auto-motivación",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "self-motivation",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue:
        "Automotivación y capacidad para gestionar proyectos personales.",
    },
    // Full Stack Development
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "full-stack-development",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Full Stack Development",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "full-stack-development",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Frontend and backend development.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "full-stack-development",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Desarrollo Full Stack",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "full-stack-development",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Desarrollo frontend y backend.",
    },
    // JavaScript
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "javascript" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "JavaScript",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "javascript" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Programming language used in web development.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "javascript" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "JavaScript",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "javascript" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue:
        "Lenguaje de programación utilizado en el desarrollo web.",
    },
    // Vue 3
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "vue3" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Vue 3",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "vue3" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "JavaScript framework for building user interfaces.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "vue3" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Vue 3",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "vue3" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue:
        "Framework JavaScript para la creación de interfaces de usuario.",
    },
    // Scrum
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "scrum" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Scrum",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "scrum" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Agile development framework.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "scrum" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Scrum",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "scrum" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Framework de desarrollo ágil.",
    },
    // Bug Fixing
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "bug-fixing" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Bug Fixing",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "bug-fixing" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Software bug fixing.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "bug-fixing" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Corrección de Errores",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "bug-fixing" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Corrección de errores de software.",
    },
    // Web Application
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "web-application",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Web Application",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "web-application",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Web application development.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "web-application",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Aplicación Web",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "web-application",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Desarrollo de aplicaciones web.",
    },
    // Adaptability to Startups
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "adaptability-startups",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Adaptability to Startups",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "adaptability-startups",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Adaptation to changes in startup environments.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "adaptability-startups",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Adaptabilidad a Startups",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "adaptability-startups",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Adaptación a los cambios en entornos de startups.",
    },
    // Problem Solving
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "problem-solving",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Problem Solving",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "problem-solving",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Ability to solve complex technical problems.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "problem-solving",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Resolución de Problemas",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "problem-solving",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue:
        "Habilidad para solucionar problemas técnicos complejos.",
    },
    // Teamwork
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "teamwork" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Teamwork",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "teamwork" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Effective collaboration with a development team.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "teamwork" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Trabajo en Equipo",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "teamwork" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Colaboración efectiva con un equipo de desarrollo.",
    },
    // Team Leadership
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "team-leadership",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Team Leadership",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "team-leadership",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Effective leadership of development teams.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "team-leadership",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Liderazgo de Equipo",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "team-leadership",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Liderazgo efectivo de equipos de desarrollo.",
    },
    // AWS Deployment
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "aws-deployment",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "AWS Deployment",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "aws-deployment",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Application deployment on Amazon Web Services.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "aws-deployment",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Despliegue en AWS",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "aws-deployment",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Despliegue de aplicaciones en Amazon Web Services.",
    },
    // Laravel
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "laravel" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Laravel",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "laravel" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "PHP framework for backend development.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "laravel" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Laravel",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "laravel" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Framework PHP para el desarrollo backend.",
    },
    // System Architecture
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "system-architecture",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "System Architecture",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "system-architecture",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "System architecture design.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "system-architecture",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Arquitectura de Sistemas",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "system-architecture",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Diseño de arquitectura de sistemas.",
    },
    // Microfrontend
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "microfrontend",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Microfrontend",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "microfrontend",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Microfrontend architecture.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "microfrontend",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Microfrontend",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "microfrontend",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Arquitectura de microfrontends.",
    },
    // E-commerce Development
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "ecommerce-development",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "E-commerce Development",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "ecommerce-development",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "E-commerce solutions development.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "ecommerce-development",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Desarrollo de E-commerce",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "ecommerce-development",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Desarrollo de soluciones de comercio electrónico.",
    },
    // Cloud Computing
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "cloud-computing",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Cloud Computing",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "cloud-computing",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue:
        "Use of cloud technologies for development and deployment.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "cloud-computing",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Computación en la Nube",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "cloud-computing",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue:
        "Uso de tecnologías en la nube para el desarrollo y despliegue.",
    },
    // Agile Methodologies
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "agile-methodologies",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Agile Methodologies",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "agile-methodologies",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Agile methodologies for project management.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "agile-methodologies",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Metodologías Ágiles",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "agile-methodologies",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Metodologías ágiles para gestión de proyectos.",
    },
    // Team Management
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "team-management",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Team Management",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "team-management",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Effective team management.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "team-management",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Gestión de Equipos",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "team-management",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Gestión efectiva de equipos.",
    },
    // Customer Oriented
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "customer-oriented",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Customer Oriented",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "customer-oriented",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Focus on customer experience.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "customer-oriented",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Orientado al Cliente",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "customer-oriented",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Enfoque en la experiencia del cliente.",
    },
    // Production Monitoring
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "production-monitoring",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Production Monitoring",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "production-monitoring",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Monitoring production in manufacturing systems.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "production-monitoring",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Monitoreo de Producción",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "production-monitoring",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Monitoreo de la producción en sistemas de manufactura.",
    },
    // Productivity Analysis
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "productivity-analysis",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Productivity Analysis",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "productivity-analysis",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Productivity analysis for continuous improvement.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "productivity-analysis",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Análisis de Productividad",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "productivity-analysis",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Análisis de productividad para la mejora continua.",
    },
    // Local Network
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "local-network",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Local Network",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "local-network",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Local network management.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "local-network",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Red Local",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "local-network",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Gestión de redes locales.",
    },
    // jQuery
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "jquery" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "jQuery",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "jquery" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "JavaScript library for DOM manipulation.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "jquery" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "jQuery",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "jquery" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Biblioteca JavaScript para manipulación de DOM.",
    },
    // Web Platform
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "web-platform" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Web Platform",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "web-platform" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Web platform development.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "web-platform" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Plataforma Web",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "web-platform" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Desarrollo de plataformas web.",
    },
    // Business Analytics
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "business-analytics",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Business Analytics",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "business-analytics",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Business data analysis.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "business-analytics",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Analítica de Negocios",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "business-analytics",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Análisis de datos empresariales.",
    },
    // Security Management
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "security-management",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Security Management",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "security-management",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Enterprise system security management.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "security-management",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Gestión de Seguridad",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "security-management",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Gestión de seguridad en sistemas empresariales.",
    },
    // Data Analysis
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "data-analysis",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Data Analysis",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "data-analysis",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Data analysis for process improvement.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "data-analysis",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Análisis de Datos",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "data-analysis",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Análisis de datos para la mejora de procesos.",
    },
    // Team Collaboration
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "team-collaboration",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Team Collaboration",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "team-collaboration",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Effective team collaboration.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "team-collaboration",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Colaboración de Equipo",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "team-collaboration",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Colaboración efectiva en equipo.",
    },
    // Graduation Project
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "graduation-project",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Graduation Project",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "graduation-project",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Direction and implementation of graduation projects.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "graduation-project",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Proyecto de Grado",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "graduation-project",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Dirección e implementación de proyectos de grado.",
    },
    // Technical Challenges
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "technical-challenges",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Technical Challenges",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "technical-challenges",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Solving complex technical challenges.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "technical-challenges",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Desafíos Técnicos",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "technical-challenges",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Resolución de desafíos técnicos complejos.",
    },
    // Project Direction
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "project-direction",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Project Direction",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "project-direction",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Project management and direction.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "project-direction",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Dirección de Proyecto",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "project-direction",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Dirección y gestión de proyectos.",
    },
    // Solution Implementation
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "solution-implementation",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Solution Implementation",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "solution-implementation",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Implementation of technical solutions.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "solution-implementation",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Implementación de Soluciones",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "solution-implementation",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Implementación de soluciones técnicas.",
    },
    // Technical Consulting
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "technical-consulting",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Technical Consulting",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "technical-consulting",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Technical consulting for graduation projects.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "technical-consulting",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Consultoría Técnica",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "technical-consulting",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Asesoramiento técnico para proyectos de grado.",
    },
    // Technical Writing
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "technical-writing",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Technical Writing",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "technical-writing",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Technical writing for project documentation.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "technical-writing",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Redacción Técnica",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "technical-writing",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Redacción técnica para documentación de proyectos.",
    },
    // Time Management
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "time-management",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Time Management",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "time-management",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Effective time management to meet deadlines.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "time-management",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Gestión del Tiempo",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "time-management",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue:
        "Gestión efectiva del tiempo para cumplir con los plazos.",
    },
    // Infrastructure Management
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "infrastructure-management",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Infrastructure Management",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "infrastructure-management",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Management of system infrastructures.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "infrastructure-management",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Gestión de Infraestructura",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "infrastructure-management",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Gestión de infraestructuras de sistemas.",
    },
    // Network Architecture
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "network-architecture",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Network Architecture",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "network-architecture",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Network architecture design.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "network-architecture",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Arquitectura de Redes",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "network-architecture",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Diseño de arquitecturas de redes.",
    },
    // Project Planning
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "project-planning",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Project Planning",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "project-planning",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Effective project planning.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "project-planning",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Planificación de Proyecto",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "project-planning",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Planificación efectiva de proyectos.",
    },
    // Work Management
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "work-management",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Work Management",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "work-management",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Management of projects and tasks.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "work-management",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Gestión del Trabajo",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "work-management",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Gestión de proyectos y tareas.",
    },
    // Budget Management
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "budget-management",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Budget Management",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "budget-management",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Project budget management.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "budget-management",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Gestión del Presupuesto",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "budget-management",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Gestión de presupuestos de proyectos.",
    },
    // System Design
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "system-design",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "System Design",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "system-design",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Design of computer systems.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "system-design",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Diseño de Sistemas",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "system-design",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Diseño de sistemas informáticos.",
    },
    // Software Development
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "software-development",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Software Development",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "software-development",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Software application development.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "software-development",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Desarrollo de Software",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "software-development",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Desarrollo de aplicaciones de software.",
    },
    // Data Management
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "data-management",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Data Management",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "data-management",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Data management for business applications.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "data-management",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Gestión de Datos",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "data-management",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Gestión de datos para aplicaciones empresariales.",
    },
    // Project Management
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "project-management",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Project Management",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "project-management",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Technical project management.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "project-management",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Gestión de Proyectos",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "project-management",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Gestión de proyectos técnicos.",
    },
    // Collaborative Work
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "collaborative-work",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Collaborative Work",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "collaborative-work",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Collaborative work for project development.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "collaborative-work",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Trabajo Colaborativo",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "collaborative-work",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Trabajo colaborativo para el desarrollo de proyectos.",
    },
    // Medical Records
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "medical-records",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Medical Records",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "medical-records",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Management of electronic medical records.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "medical-records",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Historias Médicas",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "medical-records",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Gestión de historias médicas electrónicas.",
    },
    // Desktop Application
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "desktop-application",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Desktop Application",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "desktop-application",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Desktop application development.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "desktop-application",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Aplicación de Escritorio",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "desktop-application",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Desarrollo de aplicaciones de escritorio.",
    },
    // Java
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "java" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Java",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "java" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Programming language for application development.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "java" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Java",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "java" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue:
        "Lenguaje de programación para desarrollo de aplicaciones.",
    },
    // Object Oriented Programming
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "object-oriented-programming",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Object Oriented Programming",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "object-oriented-programming",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Object-oriented programming.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "object-oriented-programming",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Programación Orientada a Objetos",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "object-oriented-programming",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Programación orientada a objetos.",
    },
    // Requirements Gathering
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "requirements-gathering",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Requirements Gathering",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "requirements-gathering",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Technical requirements gathering.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "requirements-gathering",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Levantamiento de Requerimientos",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "requirements-gathering",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Levantamiento de requerimientos técnicos.",
    },
    // Software Design
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "software-design",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Software Design",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "software-design",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Software design.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "software-design",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Diseño de Software",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "software-design",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Diseño de aplicaciones de software.",
    },
    // Technical Communication
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "technical-communication",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Technical Communication",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "technical-communication",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Effective communication for technical development.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "technical-communication",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Comunicación Técnica",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "technical-communication",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Comunicación efectiva para el desarrollo técnico.",
    },
    // Analytical Thinking
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "analytical-thinking",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Analytical Thinking",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "analytical-thinking",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Analytical thinking for technical solutions.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "analytical-thinking",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Pensamiento Analítico",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "analytical-thinking",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Pensamiento analítico para soluciones técnicas.",
    },
    // Adaptability
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "adaptability" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Adaptability",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "adaptability" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Adaptation to new technologies and challenges.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "adaptability" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Adaptabilidad",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "adaptability" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Adaptación a tecnologías y desafíos nuevos.",
    },
    // Inventory Management
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "inventory-management",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Inventory Management",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "inventory-management",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Inventory management for business applications.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "inventory-management",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Gestión de Inventarios",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "inventory-management",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue:
        "Gestión de inventarios para aplicaciones empresariales.",
    },
    // PHP
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "php" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "PHP",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "php" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Programming language for web development.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "php" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "PHP",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "php" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Lenguaje de programación para desarrollo web.",
    },
    // CRUD
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "crud" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "CRUD",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "crud" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "CRUD operations for databases.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "crud" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "CRUD",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "crud" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Operaciones CRUD para bases de datos.",
    },
    // Offline System
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "offline-system",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Offline System",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "offline-system",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Development of systems to operate offline.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "offline-system",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Sistema Offline",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "offline-system",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Desarrollo de sistemas para operar sin conexión.",
    },
    // Asset Management
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "asset-management",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Asset Management",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "asset-management",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Asset management for business applications.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "asset-management",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Gestión de Activos",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "asset-management",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Gestión de activos para aplicaciones empresariales.",
    },
    // Data Entry
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "data-entry" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Data Entry",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: { table: "skills", field: "codeName", value: "data-entry" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Data entry and manipulation.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "data-entry" },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Entrada de Datos",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: { table: "skills", field: "codeName", value: "data-entry" },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Entrada y manipulación de datos.",
    },
    // Database Management
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "database-management",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Database Management",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "database-management",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Database management.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "database-management",
        },
      },
      tableName: "Skills",
      field: "name",
      translatedValue: "Gestión de Base de Datos",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "skills",
          field: "codeName",
          value: "database-management",
        },
      },
      tableName: "Skills",
      field: "description",
      translatedValue: "Gestión de bases de datos.",
    },
  ],
  educationsTranslations: [
    // Udemy - Web Development
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "educations",
          field: "codeName",
          value: "udemy-web-development-bypabloc",
        },
      },
      tableName: "Educations",
      field: "learn",
      translatedValue:
        "In Udemy I have taken several web development courses, including: JavaScript, React, Vue, Node, SQL, among others. With the same philosophy of learning at my own pace and in my own time but always learning.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "educations",
          field: "codeName",
          value: "udemy-web-development-bypabloc",
        },
      },
      tableName: "Educations",
      field: "area",
      translatedValue: "Web Development",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "educations",
          field: "codeName",
          value: "udemy-web-development-bypabloc",
        },
      },
      tableName: "Educations",
      field: "learn",
      translatedValue:
        "En Udemy he tomado varios cursos de desarrollo web, entre ellos: JavaScript, React, Vue, Node, SQL, entre otros. Con la misma filosofía de aprender a mi ritmo y a mi tiempo pero siempre aprendiendo.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "educations",
          field: "codeName",
          value: "udemy-web-development-bypabloc",
        },
      },
      tableName: "Educations",
      field: "area",
      translatedValue: "Desarrollo Web",
    },
    // YouTube - Web Development
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "educations",
          field: "codeName",
          value: "youtube-web-development-bypabloc",
        },
      },
      tableName: "Educations",
      field: "learn",
      translatedValue:
        "When I started getting into programming courses in 2013, I accessed free and paid material available online at that time, and to this day I continue to learn.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "educations",
          field: "codeName",
          value: "youtube-web-development-bypabloc",
        },
      },
      tableName: "Educations",
      field: "area",
      translatedValue: "Web Development",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "educations",
          field: "codeName",
          value: "youtube-web-development-bypabloc",
        },
      },
      tableName: "Educations",
      field: "learn",
      translatedValue:
        "Cuando comencé a introducirme en el curso de programación en 2013, accedí a material gratuito y de paga que existía en ese momento en linea, hasta el día de hoy no paro de aprender",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "educations",
          field: "codeName",
          value: "youtube-web-development-bypabloc",
        },
      },
      tableName: "Educations",
      field: "area",
      translatedValue: "Desarrollo Web",
    },
    // UPTYAB - Informática
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "educations",
          field: "codeName",
          value: "uptyab-informatics-engineering-bypabloc",
        },
      },
      tableName: "Educations",
      field: "learn",
      translatedValue:
        "I studied Informatics Engineering at UPTYAB, where I gained knowledge in programming, databases, networks, operating systems, among others.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "en" },
        recordId: {
          table: "educations",
          field: "codeName",
          value: "uptyab-informatics-engineering-bypabloc",
        },
      },
      tableName: "Educations",
      field: "area",
      translatedValue: "Informatics Engineering",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "educations",
          field: "codeName",
          value: "uptyab-informatics-engineering-bypabloc",
        },
      },
      tableName: "Educations",
      field: "learn",
      translatedValue:
        "Estudié Ingeniería Informática en la UPTYAB, donde adquirí conocimientos en programación, bases de datos, redes, sistemas operativos, entre otros.",
    },
    {
      relationship: {
        languageId: { table: "languages", field: "codeName", value: "es" },
        recordId: {
          table: "educations",
          field: "codeName",
          value: "uptyab-informatics-engineering-bypabloc",
        },
      },
      tableName: "Educations",
      field: "area",
      translatedValue: "Ingeniería Informática",
    },
  ],
  awardsTranslations: [
    // Innovator Award - Destacame 2023
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "awards",
          field: "codeName",
          value: "innovator-destacame-2023",
        },
      },
      tableName: "Awards",
      field: "title",
      translatedValue: "Innovator of the year 2023 at Destacame",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "awards",
          field: "codeName",
          value: "innovator-destacame-2023",
        },
      },
      tableName: "Awards",
      field: "summary",
      translatedValue:
        "For leading the implementation of innovative technological solutions in the company, significantly improving operational efficiency and user experience.",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "awards",
          field: "codeName",
          value: "innovator-destacame-2023",
        },
      },
      tableName: "Awards",
      field: "title",
      translatedValue: "Innovador del año 2023 en Destacame",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "awards",
          field: "codeName",
          value: "innovator-destacame-2023",
        },
      },
      tableName: "Awards",
      field: "summary",
      translatedValue:
        "Por liderar la implementación de soluciones tecnológicas innovadoras en la empresa, mejorando significativamente la eficiencia operativa y la experiencia del usuario.",
    },
    // Triple Alianza Award - Lima 2020
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "awards",
          field: "codeName",
          value: "triple-alianza-lima-2020",
        },
      },
      tableName: "Awards",
      field: "title",
      translatedValue: "Triple Alliance Challenge Lima",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "awards",
          field: "codeName",
          value: "triple-alianza-lima-2020",
        },
      },
      tableName: "Awards",
      field: "summary",
      translatedValue:
        "For having obtained 1st place in the Commerce sector of the 'Triple Alliance COVID-19 Challenge', this happened during my experience at DIBAL.",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "awards",
          field: "codeName",
          value: "triple-alianza-lima-2020",
        },
      },
      tableName: "Awards",
      field: "title",
      translatedValue: "Desafío Triple Alianza Lima",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "awards",
          field: "codeName",
          value: "triple-alianza-lima-2020",
        },
      },
      tableName: "Awards",
      field: "summary",
      translatedValue:
        "Por haber obtenido el 1er lugar en el sector Comercio del 'Desafío Triple Alianza COVID-19', esto sucedió en mi experiencia en DIBAL.",
    },
  ],
  languagesUsersTranslations: [
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "languagesUsers",
          field: "codeName",
          value: "es-bypabloc",
        },
      },
      tableName: "LanguagesUsers",
      field: "fluency",
      translatedValue: "Nativo",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "languagesUsers",
          field: "codeName",
          value: "es-bypabloc",
        },
      },
      tableName: "LanguagesUsers",
      field: "fluency",
      translatedValue: "Native",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "languagesUsers",
          field: "codeName",
          value: "en-bypabloc",
        },
      },
      tableName: "LanguagesUsers",
      field: "fluency",
      translatedValue: "Intermedio en lectura y básico en escritura y habla",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "languagesUsers",
          field: "codeName",
          value: "en-bypabloc",
        },
      },
      tableName: "LanguagesUsers",
      field: "fluency",
      translatedValue:
        "Intermediate in reading and basic in writing and speaking",
    },
  ],
  referencesTranslations: [
    // Alan Vergara Bravo
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "references",
          field: "codeName",
          value: "alan-vergara-bravo",
        },
      },
      tableName: "References",
      field: "reference",
      translatedValue: "Team Member",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "references",
          field: "codeName",
          value: "alan-vergara-bravo",
        },
      },
      tableName: "References",
      field: "position",
      translatedValue: "Software Architect Developer",
    },
    // Alejandra Medina Briceño
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "references",
          field: "codeName",
          value: "alejandra-medina-briceno",
        },
      },
      tableName: "References",
      field: "reference",
      translatedValue: "Team Member",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "references",
          field: "codeName",
          value: "alejandra-medina-briceno",
        },
      },
      tableName: "References",
      field: "position",
      translatedValue: "UX/UI Designer",
    },
    // Baldomero Águila
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "references",
          field: "codeName",
          value: "baldomero-aguila",
        },
      },
      tableName: "References",
      field: "reference",
      translatedValue: "Team Member",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "references",
          field: "codeName",
          value: "baldomero-aguila",
        },
      },
      tableName: "References",
      field: "position",
      translatedValue: "Mobile Developer",
    },
    // Cristian Fuentes
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "references",
          field: "codeName",
          value: "cristian-fuentes",
        },
      },
      tableName: "References",
      field: "reference",
      translatedValue: "Team Member",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "references",
          field: "codeName",
          value: "cristian-fuentes",
        },
      },
      tableName: "References",
      field: "position",
      translatedValue: "Full Stack Developer",
    },
    // Helis Montes
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "references",
          field: "codeName",
          value: "helis-montes",
        },
      },
      tableName: "References",
      field: "reference",
      translatedValue: "Team Member",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "references",
          field: "codeName",
          value: "helis-montes",
        },
      },
      tableName: "References",
      field: "position",
      translatedValue: "Full Stack Developer",
    },
    // Edder Ramírez
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "references",
          field: "codeName",
          value: "edder-ramirez",
        },
      },
      tableName: "References",
      field: "reference",
      translatedValue: "Team Member",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "references",
          field: "codeName",
          value: "edder-ramirez",
        },
      },
      tableName: "References",
      field: "position",
      translatedValue: "Full Stack Developer",
    },
    // José Namoc
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "references",
          field: "codeName",
          value: "jose-namoc",
        },
      },
      tableName: "References",
      field: "reference",
      translatedValue: "Team Member",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "references",
          field: "codeName",
          value: "jose-namoc",
        },
      },
      tableName: "References",
      field: "position",
      translatedValue: "Full Stack Developer",
    },
    // Jacnelly Colmenarez
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "references",
          field: "codeName",
          value: "jacnelly-colmenarez",
        },
      },
      tableName: "References",
      field: "reference",
      translatedValue: "Team Member",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "references",
          field: "codeName",
          value: "jacnelly-colmenarez",
        },
      },
      tableName: "References",
      field: "position",
      translatedValue: "UI/UX Designer",
    },
    // Felipe Rivera
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "references",
          field: "codeName",
          value: "felipe-rivera",
        },
      },
      tableName: "References",
      field: "reference",
      translatedValue: "Worked at the same company",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "references",
          field: "codeName",
          value: "felipe-rivera",
        },
      },
      tableName: "References",
      field: "position",
      translatedValue: "Talent Acquisition Lead",
    },
    // Samuel Esponiza
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "references",
          field: "codeName",
          value: "samuel-esponiza",
        },
      },
      tableName: "References",
      field: "reference",
      translatedValue:
        "Studied at the same university and worked on projects together",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "references",
          field: "codeName",
          value: "samuel-esponiza",
        },
      },
      tableName: "References",
      field: "position",
      translatedValue: "Full Stack Developer",
    },
  ],
  projectsTranslations: [
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "projects",
          field: "codeName",
          value: "cv-bypabloc",
        },
      },
      tableName: "Projects",
      field: "description",
      translatedValue:
        "Desarrollo de un currículum vitae en Astro para mostrar mis habilidades y experiencia laboral.",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "projects",
          field: "codeName",
          value: "cv-bypabloc",
        },
      },
      tableName: "Projects",
      field: "highlights",
      translatedValue: JSON.stringify([
        "Practicar mis habilidades de desarrollo web con Astro",
        "Mostrar mi experiencia laboral de forma clara y concisa",
      ]),
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "projects",
          field: "codeName",
          value: "cv-bypabloc",
        },
      },
      tableName: "Projects",
      field: "highlights",
      translatedValue: JSON.stringify([
        "Practicing my web development skills with Astro",
        "Show my work experience clearly and concisely",
      ]),
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "projects",
          field: "codeName",
          value: "extension-faststruct",
        },
      },
      tableName: "Projects",
      field: "highlights",
      translatedValue: JSON.stringify([
        "Just for fun, I wanted to learn how to make an extension for VS Code that would simplify a process that I had to do manually when interacting with AI.",
      ]),
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "projects",
          field: "codeName",
          value: "extension-faststruct",
        },
      },
      tableName: "Projects",
      field: "description",
      translatedValue:
        "A VS Code extension to quickly visualize and document your project's file structure. FastStruct helps you create clear, well-formatted documentation of your project's directory structure, including file contents when needed.",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "projects",
          field: "codeName",
          value: "cv-bypabloc",
        },
      },
      tableName: "Projects",
      field: "description",
      translatedValue:
        "Development of a resume in Astro to show my skills and work experience.",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "projects",
          field: "codeName",
          value: "cv-bypabloc",
        },
      },
      tableName: "Projects",
      field: "highlights",
      translatedValue: JSON.stringify([
        "Practice my web development skills with Astro",
        "Show my work experience clearly and concisely",
      ]),
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "projects",
          field: "codeName",
          value: "appinteli-bypabloc",
        },
      },
      tableName: "Projects",
      field: "description",
      translatedValue:
        "Co-fundador y desarrollador de un ERP enfocado en la automatización de procesos de inventario, ventas y compras para pequeñas tiendas.",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "projects",
          field: "codeName",
          value: "appinteli-bypabloc",
        },
      },
      tableName: "Projects",
      field: "highlights",
      translatedValue: JSON.stringify([
        "Desarrollo de una plataforma de comercio electrónico integrada",
        "Gestión de cliente y proyecto desde cero",
      ]),
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "projects",
          field: "codeName",
          value: "appinteli-bypabloc",
        },
      },
      tableName: "Projects",
      field: "description",
      translatedValue:
        "Co-founder and developer of an ERP focused on automating inventory, sales, and purchasing processes for small stores.",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "projects",
          field: "codeName",
          value: "extension-faststruct",
        },
      },
      tableName: "Projects",
      field: "description",
      translatedValue:
        "Just for fun, I wanted to learn how to make an extension for VS Code that would simplify a process that I had to do manually when interacting with AI.",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "projects",
          field: "codeName",
          value: "appinteli-bypabloc",
        },
      },
      tableName: "Projects",
      field: "highlights",
      translatedValue: JSON.stringify([
        "Development of an integrated e-commerce platform",
        "Customer and project management from scratch",
      ]),
    },
  ],
  usersAttributesTranslations: [
    // Traducciones para el atributo "label"
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "usersAttributes",
          field: "codeName",
          value: "label-bypabloc",
        },
      },
      tableName: "UsersAttributes",
      field: "attributeValue",
      translatedValue: "Software engineer with over 8 years of experience",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "usersAttributes",
          field: "codeName",
          value: "label-bypabloc",
        },
      },
      tableName: "UsersAttributes",
      field: "attributeValue",
      translatedValue: "Ingeniero de software con más de 8 años de experiencia",
    },
    // Traducciones para el atributo "summary"
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "usersAttributes",
          field: "codeName",
          value: "summary-bypabloc",
        },
      },
      tableName: "UsersAttributes",
      field: "attributeValue",
      translatedValue:
        "Software engineer with over 8 years of experience, specialized in Full Stack development with Python and JavaScript. Expert in creating technological solutions with Vue, Django, microservices, and AWS, I have successfully developed and led the implementation of ERP systems and fintech platforms, significantly improving operational efficiency and user experience. Skilled in coordinating and motivating teams, I easily adapt to dynamic and challenging environments, always focused on quality and innovation.",
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "usersAttributes",
          field: "codeName",
          value: "summary-bypabloc",
        },
      },
      tableName: "UsersAttributes",
      field: "attributeValue",
      translatedValue:
        "Ingeniero de software con más de 8 años de experiencia, especializado en desarrollo Full Stack con Python y JavaScript. Experto en crear soluciones tecnológicas con Vue, Django, microservicios y AWS, he desarrollado con éxito y liderado la implementación de sistemas ERP y plataformas fintech, mejorando significativamente la eficiencia operativa y la experiencia del usuario. Habilidoso en la coordinación y motivación de equipos, me adapto fácilmente a entornos dinámicos y desafiantes, siempre enfocado en la calidad y la innovación.",
    },
    // Traducciones para el atributo "location"
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "en",
        },
        recordId: {
          table: "usersAttributes",
          field: "codeName",
          value: "location-bypabloc",
        },
      },
      tableName: "UsersAttributes",
      field: "attributeValue",
      translatedValue: JSON.stringify({
        address: "",
        postalCode: "15009",
        city: "Lima",
        countryCode: "PE",
        region: "Peru",
      }),
    },
    {
      relationship: {
        languageId: {
          table: "languages",
          field: "codeName",
          value: "es",
        },
        recordId: {
          table: "usersAttributes",
          field: "codeName",
          value: "location-bypabloc",
        },
      },
      tableName: "UsersAttributes",
      field: "attributeValue",
      translatedValue: JSON.stringify({
        address: "",
        postalCode: "15009",
        city: "Lima",
        countryCode: "PE",
        region: "Perú",
      }),
    },
  ],
  projectUrlTypes: [
    {
      codeName: "github",
      name: "GitHub",
      icons: {
        default: "i-ant-design-github-outlined",
        dark: "i-ant-design-github-filled",
      },
    },
    {
      codeName: "website",
      name: "Website",
      icons: {
        default: "i-clarity-world-line",
        dark: "i-clarity-world-solid",
      },
    },
  ],
  projectUrls: [
    {
      relationship: {
        projectId: {
          table: "projects",
          field: "codeName",
          value: "cv-bypabloc",
        },
        urlTypeId: {
          table: "projectUrlTypes",
          field: "codeName",
          value: "github",
        },
      },
      url: "https://github.com/bypabloc/cv",
    },
    {
      relationship: {
        projectId: {
          table: "projects",
          field: "codeName",
          value: "extension-faststruct",
        },
        urlTypeId: {
          table: "projectUrlTypes",
          field: "codeName",
          value: "github",
        },
      },
      url: "https://github.com/bypabloc/faststruct",
    },
    {
      relationship: {
        projectId: {
          table: "projects",
          field: "codeName",
          value: "extension-faststruct",
        },
        urlTypeId: {
          table: "projectUrlTypes",
          field: "codeName",
          value: "website",
        },
      },
      url: "https://marketplace.visualstudio.com/items?itemName=the-full-stack.faststruct",
    },
    {
      relationship: {
        projectId: {
          table: "projects",
          field: "codeName",
          value: "cv-bypabloc",
        },
        urlTypeId: {
          table: "projectUrlTypes",
          field: "codeName",
          value: "website",
        },
      },
      url: "https://pablocodes.com",
    },
  ],
};
