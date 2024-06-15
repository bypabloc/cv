export const toKebabCase = (str) => {
  return str
    .replace(/([a-z])([A-Z])/g, '$1-$2') // Coloca un guion entre letras minúsculas seguidas de mayúsculas
    .replace(/[\s_]+/g, '-') // Reemplaza espacios y guiones bajos por guiones
    .toLowerCase(); // Convierte todo a minúsculas
}
