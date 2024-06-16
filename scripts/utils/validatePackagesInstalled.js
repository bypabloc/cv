import fs from 'fs';
import { execSync } from 'child_process';
import readline from 'readline';

import appConfig from "../settings/appConfig.js";


const readPackageJson = (path) => {
  const response = {
    isValid: true,
    errors: [],
    data: {},
  };
  try {
    const fileData = fs.readFileSync(path, 'utf8');
    const { dependencies, devDependencies } = JSON.parse(fileData);
    if (!dependencies && !devDependencies) {
      response.isValid = false;
      response.errors.push("No se encontraron dependencias en el archivo package.json.");
      return response;
    }
    response.data['dependencies'] = dependencies || {};
    response.data['devDependencies'] = devDependencies || {};
    return response;
  } catch (error) {
    return {
      isValid: false,
      errors: ["Error al leer el archivo package.json.", error.message],
    };
  }
};


const userConfirmation = async (message) => {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });

  return new Promise((resolve) => {
    rl.question(`${message} (Y/n) `, (answer) => {
      rl.close();
      resolve(answer.toLowerCase() === 'y' || answer.toLowerCase() === '');
    });
  });
};


const performPnpmInstall = () => {
  try {
    console.log("Instalando paquetes...");
    execSync('pnpm install', { stdio: 'inherit' });
    console.log("Paquetes instalados exitosamente.");
  } catch (error) {
    console.error("Error al instalar los paquetes:", error.message);
  }
};


const getInstalledPackages = () => {
  const response = {
    isValid: true,
    errors: [],
    data: {},
  };
  try {
    const result = execSync('pnpm list --depth=0 --json', { stdio: 'pipe' }).toString();
    const resultToJson = JSON.parse(result) ? JSON.parse(result)[0] : {};
    const { dependencies } = resultToJson;
    if (!dependencies) {
      response.isValid = false;
      response.errors.push("No se encontraron dependencias instaladas con pnpm.");
      response['code'] = 'suggestInstall';
      return response;
    }
    response.data['dependencies'] = dependencies;
    return response;
  } catch (error) {
    response.isValid = false;
    response.errors.push("Error obteniendo la lista de paquetes instalados.");
    response.errors.push(error.message);
    return response;
  }
};


const versionCompare = (installed, required) => {
  const response = {
    isValid: true,
    errors: [],
    data: {},
  };

  const instParts = installed.split('.').map(x => parseInt(x));
  const reqParts = required.split('.').map(x => parseInt(x));

  for (let i = 0; i < reqParts.length; i++) {
    if (reqParts[i] < instParts[i]) {
      continue
    }
    else if (reqParts[i] > instParts[i]) {
      response.errors.push("La versión instalada es menor que la requerida.");
    }
  }

  if (!response.errors) {
    response.isValid = false;
    return response;
  }

  return response;
};


export const validatePackagesInstalled = async () => {
  const response = {
    isValid: true,
    errors: [],
    data: {},
  };

  const { rootPath } = appConfig;
  const packagePath = `${rootPath}/package.json`;

  const packageJson = readPackageJson(packagePath);
  if (!packageJson.isValid) {
    response.isValid = false;
    response.errors.push("No se pudo leer el archivo package.json.");
    return response;
  }

  const requiredDependencies = {...packageJson.data.dependencies, ...packageJson.data.devDependencies};
  const installedDependencies = getInstalledPackages();
  if (!installedDependencies.isValid) {
    const { code } = installedDependencies;
    if (code && installedDependencies.code === 'suggestInstall') {
      const confirm = await userConfirmation("¿Deseas ejecutar 'pnpm install' para instalar los paquetes faltantes?");
      if (!confirm) {
        response.isValid = false;
        response.errors.push("Instalación de paquetes cancelada por el usuario.");
        return response;
      }
      performPnpmInstall();
      return await validatePackagesInstalled();
    }
    response.isValid = false;
    response.errors.push([...installedDependencies.errors]);
    return response;
  }

  for (const dep in requiredDependencies) {
    const requiredVersion = requiredDependencies[dep].replace('^', '').replace('~', '');
    const installedVersion = installedDependencies[dep]?.version;

    if (!installedVersion) {
      response.errors.push(`El paquete ${dep} no está instalado.`);
      continue
    }
    const compared = versionCompare(installedVersion, requiredVersion)
    if (!compared.isValid) {
      response.errors.push([...compared.errors]);
    }
  };

  if (!response.errors) {
    response.isValid = false;
    return response;
  }

  // console.log("Todas las dependencias están correctamente instaladas y con las versiones adecuadas.");

  response.data = {
    requiredDependencies,
    installedDependencies,
  };
  return response;
}
