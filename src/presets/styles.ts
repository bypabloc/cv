import { definePreset } from "unocss";
import type { Preset } from "unocss";

/**
 * Convierte un valor dado a un número entero.
 * Retorna 0 si el valor no puede ser convertido a un entero válido.
 *
 * @param {string | number} value El valor a convertir.
 * @return {number} El valor entero convertido o 0 si la conversión falla.
 */
function toValidInt(value: string | number): number {
  const valueStr = value.toString();
  const result = parseInt(valueStr, 10);
  return isNaN(result) ? 0 : result;
}

export default definePreset((params?: Preset) => {
  const { options } = params || {};
  const { factor = 4 } = options || {};

  return {
    name: "styles",
    rules: [
      // Regla para margin
      [/^m-(\d+)$/, ([, d]) => ({ margin: `${toValidInt(d) * factor}px` })],
      [
        /^mx-(\d+)$/,
        ([, d]) => ({
          "margin-left": `${toValidInt(d) * factor}px`,
          "margin-right": `${toValidInt(d) * factor}px`,
        }),
      ],
      [
        /^mt-(\d+)$/,
        ([, d]) => ({
          "margin-top": `${toValidInt(d) * factor}px`,
        }),
      ],
      [
        /^mb-(\d+)$/,
        ([, d]) => ({
          "margin-bottom": `${toValidInt(d) * factor}px`,
        }),
      ],
      [
        /^ml-(\d+)$/,
        ([, d]) => ({
          "margin-left": `${toValidInt(d) * factor}px`,
        }),
      ],
      [
        /^mr-(\d+)$/,
        ([, d]) => ({
          "margin-right": `${toValidInt(d) * factor}px`,
        }),
      ],
      [
        /^my-(\d+)$/,
        ([, d]) => ({
          "margin-top": `${toValidInt(d) * factor}px`,
          "margin-bottom": `${toValidInt(d) * factor}px`,
        }),
      ],

      // Regla para padding
      [/^p-(\d+)$/, ([, d]) => ({ padding: `${toValidInt(d) * factor}px` })],
      [
        /^px-(\d+)$/,
        ([, d]) => ({
          "padding-left": `${toValidInt(d) * factor}px`,
          "padding-right": `${toValidInt(d) * factor}px`,
        }),
      ],
      [
        /^py-(\d+)$/,
        ([, d]) => ({
          "padding-top": `${toValidInt(d) * factor}px`,
          "padding-bottom": `${toValidInt(d) * factor}px`,
        }),
      ],

      // Regla para gap
      [/^gap-(\d+)$/, ([, d]) => ({ gap: `${toValidInt(d) * factor}px` })],

      // fxb fxb-column
      [
        /^d-flex$/,
        () => {
          return {
            display: "flex",
          };
        },
      ],
      [
        /^flex-(\w+)$/,
        ([, d]) => {
          return {
            "flex-direction": d === "column" ? "column" : "row",
          };
        },
      ],
    ],
    variants: [
      /* ... */
    ],
    shortcuts: [
      /* ... */
    ],
  };
});
