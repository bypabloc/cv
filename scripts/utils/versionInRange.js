export const versionInRange = ({ current, min, max }) => {
  if (!Array.isArray(current) || !Array.isArray(min) || !Array.isArray(max)) {
    return {
      isValid: false,
      errors: "Los valores deben ser arreglos.",
    };
  }

  if (current.length !== 3 || min.length !== 3 || max.length !== 3) {
    return {
      isValid: false,
      errors: "Los arreglos deben tener 3 elementos.",
    };
  }

  if (
    current.some((v) => typeof v !== "number") ||
    min.some((v) => typeof v !== "number") ||
    max.some((v) => typeof v !== "number")
  ) {
    return {
      isValid: false,
      errors: "Los elementos de los arreglos deben ser números.",
    };
  }

  const compareVersions = (v1, v2) => {
    for (let i = 0; i < 3; i++) {
      if (v1[i] < v2[i]) return -1;
      if (v1[i] > v2[i]) return 1;
    }
    return 0;
  };

  if (compareVersions(current, min) < 0) {
    return {
      isValid: false,
      errors: `La versión debe ser al menos v${min.join(".")}. Versión actual: v${current.join(".")}`,
    };
  }

  if (compareVersions(current, max) > 0) {
    return {
      isValid: false,
      errors: `La versión debe ser como máximo v${max.join(".")}. Versión actual: v${current.join(".")}`,
    };
  }

  return {
    isValid: true,
  };
}
