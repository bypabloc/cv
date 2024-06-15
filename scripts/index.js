// Path: scripts/index.ts

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

  // Verifica la versión de Node.js
  const nodeVersionValidation = validateNodeVersion();
  if (!nodeVersionValidation.isValid) {
    console.error(nodeVersionValidation.errors)
    return;
  }

  // Verifica la versión de pnpm
  const pnpmVersionValidation = validatePnpmVersion();
  if (!pnpmVersionValidation.isValid) {
    console.error(pnpmVersionValidation.errors)
    return;
  }

  // Verifica las dependencias del proyecto
  const packagesValidation = await validatePackagesInstalled();
  if (!packagesValidation.isValid) {
    console.error(packagesValidation.errors)
    return;
  }

  try {
    const module = await import(scriptPath);
    const Class = module[className];

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
    await instance.execute();
  } catch (error) {
    console.error(`Error al importar o ejecutar la clase ${className}:`, error);
    return;
  }
}

// Obteniendo el nombre del script de los argumentos de la línea de comandos
const [scriptName] = process.argv.slice(2);

// Ejecutando el script correspondiente o mostrando un mensaje de error
runScript({ scriptName });
