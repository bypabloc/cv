import { BaseSettings } from "../utils/baseSetting.js";
import getRootPath from "../utils/getRootPath.js";
import loadEnvFile from "../utils/loadEnvFile.js";
import { getLastPathSegmentInKebabCase } from "../utils/getLastPathSegmentInKebabCase.js";

class AppConfig extends BaseSettings {
  static instance = null; // Variable estática para almacenar la instancia
  rootPath = null;
  vars = {};

  constructor() {
    super();
    if (AppConfig.instance) {
      return AppConfig.instance; // Devuelve la instancia existente si ya se creó
    }
    this.initialize();
    AppConfig.instance = this; // Guarda esta instancia en la variable estática
  }

  async initialize() {
    const rootPath = getRootPath();
    this.rootPath = rootPath;
    this.appName = getLastPathSegmentInKebabCase(rootPath);
    this.vars = await loadEnvFile({
      path: this.rootPath,
    });
    this.UID = process.getuid()
    this.GID = process.getgid()
  }
}

// Creando la instancia de forma que se asegure su inicialización completa
const appConfig = new AppConfig();

export default appConfig;
