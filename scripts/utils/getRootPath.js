// Path: utils/getRootPath.js
import { dirname } from 'path';
import { fileURLToPath } from 'url';

// __dirname no está disponible directamente en módulos ES, así que usamos una aproximación
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Asumiendo que tu estructura de carpetas mantiene 'utils' dentro del directorio raíz del proyecto
// y quieres obtener el path del directorio raíz
const getRootPath = () => {
    return dirname(dirname(__dirname));
};

export default getRootPath;
