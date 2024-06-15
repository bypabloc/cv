import { readFileSync } from "fs";

class Validator {
  static validators = {};

  static addValidator(field, validator, pre) {
    if (!this.validators[field]) {
      this.validators[field] = [];
    }
    this.validators[field].push([validator, pre]);
  }

  static validate(instance) {
    for (const [field, validators] of Object.entries(this.validators)) {
      if (field in instance) {
        let value = instance[field];
        for (const [validator, pre] of validators) {
          if (pre) {
            value = validator(value, instance);
            instance[field] = value;
          }
        }
      }
    }
  }
}

function validator(field, pre = false) {
  return function (target, propertyName, validatorFunction) {
    Validator.addValidator(field, validatorFunction, pre);
  };
}

export class BaseSettings {
  constructor() {
    this.loadEnvVariables();
    Validator.validate(this);
  }

  loadEnvVariables() {
    // En JavaScript puro, no se puede acceder a los metadatos de tipos como en TypeScript,
    // por lo que se puede optar por una solución manual o diferente según el caso de uso.
    Object.keys(this).forEach((field) => {
      const envValue = process.env[field.toUpperCase()];
      if (envValue !== undefined) {
        // Aquí, deberías tener una forma de determinar el tipo deseado para cada campo,
        // ya que JavaScript por sí solo no provee metadatos de tipo.
        this[field] = envValue; // Esto asume que todos los valores son cadenas por defecto.
        // Para manejar arrays u otros tipos, necesitarás implementar lógica específica.
      }
    });
  }

  toJSON() {
    const data = {};
    for (const [key, value] of Object.entries(this)) {
      if (!key.startsWith("_")) {
        data[key] = value;
      }
    }
    return JSON.stringify(data);
  }
}
