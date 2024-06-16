// index.js
import fs from "fs";
import { resolve as pathResolve } from "path";
import { join as pathJoin } from "path";
import { validateNodeVersion } from "./utils/validateNodeVersion.js";
import { validatePnpmVersion } from "./utils/validatePnpmVersion.js";
import { validatePackagesInstalled } from "./utils/validatePackagesInstalled.js";
import appConfig from "./settings/appConfig.js";

const toPascalCase = (str) =>
  str.replace(/(^\w|-\w)/g, (m) => m.replace("-", "").toUpperCase());

const runScript = async ({ scriptName }) => {
  const className = toPascalCase(scriptName);
  const pathFile = pathJoin(appConfig.rootPath, 'scripts', `${scriptName}.js`)
  const scriptPath = pathResolve(pathFile);

  // Verifica si el script existe
  if (!fs.existsSync(scriptPath)) {
    console.log("La operación solicitada no está disponible.");
    return;
  }

  console.log(
    `Importando y ejecutando el método 'execute' de la clase: ${className}`
  );

  if (!process.env.ENV) {
    console.error("La variable de entorno 'ENV' no está definida.");
    return
  }

  console.log(`Entorno de ejecución: ${process.env.ENV}`);

  // Verifica la versión de Node.js
  const nodeVersionValidation = validateNodeVersion();
  if (!nodeVersionValidation.isValid) {
    console.error(nodeVersionValidation.errors)
    return;
  }

  console.log(`Versión de Node.js: ${nodeVersionValidation.data.version}`);

  // Verifica la versión de pnpm
  const pnpmVersionValidation = validatePnpmVersion();
  if (!pnpmVersionValidation.isValid) {
    console.error(pnpmVersionValidation.errors)
    return;
  }

  console.log(`Versión de pnpm: ${pnpmVersionValidation.data.version}`);

  // Verifica las dependencias del proyecto
  const packagesValidation = await validatePackagesInstalled();
  if (!packagesValidation.isValid) {
    console.error(packagesValidation.errors)
    return;
  }

  console.log("Todas las dependencias están instaladas correctamente.");

  try {
    const module = await import(scriptPath);
    console.log(`Importando la clase ${className}...`)

    const Class = module[className];
    console.log(`Clase ${className} importada correctamente.`)

    if (!Class) {
      console.log(`No se encontró una clase con el nombre ${className}.`);
      return;
    }

    if (typeof Class !== "function") {
      console.log(`La clase ${className} no es una función.`);
      return;
    }

    const instance = new Class();
    if (typeof instance.execute !== "function") {
      console.log(`La clase ${className} no tiene un método 'execute'.`);
      return;
    }

    console.log(`Ejecutando el script ${className}...`)

    if (typeof instance.preRequirements === "function") {
      console.log("Verificando los requisitos previos...")
      const { isValid, errors } = await instance.preRequirements();
      if (!isValid) {
        console.error("Se encontraron los siguientes errores:", errors);
        errors.forEach((error) => console.error(`- ${error}`));
        return;
      }
    }

    await instance.initialized;
    const result = await instance.execute();

    console.log(`Script ${className} ejecutado exitosamente.`);

    if (!result.isValid) {
      throw new Error("El script no se ejecutó correctamente.", result.errors);
    }
  } catch (error) {
    console.error(error);
    return;
  }
}

// Obteniendo el nombre del script de los argumentos de la línea de comandos
const [scriptName] = process.argv.slice(2);

// Ejecutando el script correspondiente o mostrando un mensaje de error
runScript({ scriptName });
