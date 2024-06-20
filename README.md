# Minimalist Portfolio

Este es un proyecto desarrollado con Astro que permite la creación y visualización de un portafolio minimalista. A continuación se detallan los requisitos, la instalación, y el uso del proyecto.

## Requisitos

Para ejecutar este proyecto, necesitas tener instalados los siguientes programas:

- Node.js (versión 20 o superior)
- PNPM (gestor de paquetes preferido)

## Instalación

Sigue estos pasos para clonar el repositorio, instalar las dependencias y ejecutar el proyecto en un entorno local:

1. Clona el repositorio:

   ```bash
   git clone https://github.com/bypabloc/cv
   cd minimalist-portfolio-json
   ```

2. Instala las dependencias usando PNPM:

   ```bash
   pnpm install
   ```

3. Copia el archivo `env.example` a `.env` y ajusta las configuraciones según sea necesario:

   ```bash
   cp .env.example .env
   ```

4. Inicia el servidor de desarrollo:

   ```bash
   pnpm run dev
   ```

   Esto iniciará el servidor en `http://localhost:4321` o el puerto que indiques en el archivo `.env`.

## Uso

### Estructura del Proyecto

El proyecto tiene la siguiente estructura de directorios:

```plaintext
minimalist-portfolio-json/
├── src/
│   ├── components/       # Componentes reutilizables de la UI
│   ├── db/               # Utilidades y configuraciones de la base de datos
│   ├── layouts/          # Layouts para las páginas
│   ├── pages/            # Páginas principales del sitio
│   ├── presets/          # Configuraciones de estilo y temas
│   ├── stores/           # Estados y configuraciones globales
│   ├── types/            # Definiciones de tipos TypeScript
│   ├── utils/            # Utilidades varias
│   └── i18n/             # Configuración y utilidades para internacionalización
├── public/               # Archivos públicos estáticos
├── scripts/              # Scripts adicionales para la configuración y despliegue
├── astro.config.mjs      # Configuración de Astro
├── package.json          # Configuración de dependencias y scripts
├── README.md             # Documentación del proyecto
└── tsconfig.json         # Configuración de TypeScript
```

### Internacionalización (i18n)

El proyecto soporta múltiples idiomas. Los archivos de configuración de idiomas se encuentran en el directorio `src/i18n`. Puedes agregar o modificar traducciones según sea necesario.

### Temas y Estilos

El proyecto utiliza Unocss para la gestión de estilos y temas. Las configuraciones de colores y tipografías están definidas en `src/presets/color.ts` y `src/presets/typography.ts` respectivamente.

### API y Base de Datos

Las utilidades de la base de datos están en `src/utils/db`. Aquí encontrarás funciones para obtener trabajos, certificados, redes de usuario, etc. Puedes extender estas utilidades según sea necesario.

### AstroDB

El proyecto utiliza AstroDB para la gestión de datos. Puedes modificar los archivos JSON en `db/data` para añadir o modificar datos de tu portafolio o hacerlo directamente desde la web [aquí](https://studio.astro.build/).

## Despliegue

Para desplegar el proyecto, puedes utilizar cualquier plataforma que soporte aplicaciones Node.js. A continuación se muestra un ejemplo usando Vercel:

1. Instala Vercel CLI si no lo tienes:

   ```bash
   npm install -g vercel
   ```

2. Conéctate a tu cuenta de Vercel:

   ```bash
   vercel login
   ```

3. Despliega el proyecto:

   ```bash
   vercel
   ```

   Sigue las instrucciones en pantalla para configurar el despliegue.

## Contribución

Si deseas contribuir al proyecto, por favor sigue estos pasos:

1. Haz un fork del repositorio.
2. Crea una nueva rama (`git checkout -b feature/nueva-funcionalidad`).
3. Realiza tus cambios y haz commits descriptivos (`git commit -m 'Agrega nueva funcionalidad'`).
4. Sube tus cambios (`git push origin feature/nueva-funcionalidad`).
5. Abre un Pull Request.

---

Si tienes alguna duda o problema, por favor abre un issue en el repositorio.

---
