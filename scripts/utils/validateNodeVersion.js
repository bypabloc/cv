import { versionInRange } from "../utils/versionInRange.js";


export const validateNodeVersion = () => {
  const response = {
    isValid: true,
    errors: [],
  };

  const minVersion = [21, 7, 1];
  const maxVersion = [21, 999, 0];
  const nodeVersion = process.version.slice(1).split('.').map(Number);

  const versionInRangeResult = versionInRange({
    current: nodeVersion,
    min: minVersion,
    max: maxVersion,
  });
  if (!versionInRangeResult.isValid) {
    response.isValid = false;
    response.errors.push('Versión de Node.js no soportada.');
    response.errors.push(versionInRangeResult.errors);
  }

  return {
    ...response,
    data: {
      version: process.version,
    },
  };
}
