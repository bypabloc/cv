// Path: scripts/utils/baseClass.js

import appConfig from "../settings/appConfig.js";


export class BaseClass {
  constructor() {
    this.appConfig = appConfig;
    console.log('BaseClass', this.appConfig)
    this.initialized = this.init();
  }

  async init() {
    this.appConfig = appConfig;
  }

  // Método para verificar los requisitos previos
  async preRequirements() {
    // Verifica si existe la variable de entorno "ENV"
    const errors = []

    if (errors.length) {
      return {
        isValid: false,
        errors,
      }
    }

    return {
      isValid: true,
    }
  }
}
