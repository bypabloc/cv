/**
 * Función para verificar claves duplicadas en un array de objetos.
 *
 * @param {Array} recordsArray - Array de registros para verificar duplicados.
 * @param {String} keyField - Nombre del campo que se va a verificar.
 * @returns {Object} - Objeto con las claves duplicadas y la cantidad de veces que se repiten.
 */
export const checkDuplicateKeys = (
  recordsArray: Record<string, any>[],
  keyField: string
) => {
  const keyCount = {};

  // Recorrer los registros y contar las apariciones de cada clave
  for (const record of recordsArray) {
    const key = record[keyField];
    if (keyCount[key]) {
      keyCount[key]++;
    } else {
      keyCount[key] = 1;
    }
  }

  // Filtrar las claves que se repiten más de una vez
  const duplicates = Object.entries(keyCount)
    .filter(([key, count]) => count > 1)
    .reduce((acc, [key, count]) => {
      acc[key] = count;
      return acc;
    }, {} as Record<string, any>);

  return duplicates;
};
