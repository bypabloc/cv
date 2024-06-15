import { versionInRange } from "../utils/versionInRange.js";
import { execSync } from 'child_process';


export const getPnpmVersion = () => {
  const response = {
    isValid: true,
    data: { version: null },
    errors: [],
  };
  try {
    const versionOutput = execSync('pnpm --version').toString().trim();
    response.data.version = versionOutput;
    return response
  } catch (error) {
    return {
      ...response,
      isValid: false,
      errors: ['Error obteniendo la versión de pnpm.'],
    };
  }
}


export const validatePnpmVersion = () => {
  const response = {
    isValid: true,
    errors: [],
  };

  const minVersion = [9, 3, 0];
  const maxVersion = [9, 3, 0];
  const pnpmVersion = getPnpmVersion();

  if (!pnpmVersion.isValid) {
    response.isValid = false;
    response.errors.push(pnpmVersion.errors);
    return response;
  }

  const versionComponents = pnpmVersion.data.version.split('.').map(Number);

  const versionInRangeResult = versionInRange({
    current: versionComponents,
    min: minVersion,
    max: maxVersion,
  });
  if (!versionInRangeResult.isValid) {
    response.isValid = false;
    response.errors.push('Versión de Pnpm no soportada.');
    response.errors.push(versionInRangeResult.errors);
  }

  return {
    ...response,
    data: {
      version: pnpmVersion.data.version,
    },
  };
}
