import { toKebabCase } from './toKebabCase.js';

// Función para obtener el último segmento del path y convertirlo a kebab-case
export const getLastPathSegmentInKebabCase = (path) => {
  const segments = path.split('/'); // Divide el path en segmentos
  const lastSegment = segments.pop(); // Obtiene el último segmento

  return toKebabCase(lastSegment); // Convierte el último segmento a kebab-case
}
