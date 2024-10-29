import { defineConfig } from "unocss";
import { presetMini } from "unocss";
import { presetAttributify } from "unocss";
import { presetIcons } from "unocss";
import { presetWebFonts } from "unocss";
import { presetUno } from "unocss";

import Styles from "./src/presets/styles";
import { typography, color } from "./src/presets";
import { themes, variables } from "./src/presets/colors";

export default defineConfig({
  presets: [
    presetAttributify({}),
    presetUno({}),
    presetMini({}),
    presetWebFonts({
      // provider: "google",
      fonts: {
        sans: [
          {
            name: "Source Sans Pro",
            weights: [
              "100",
              "200",
              "300",
              "400",
              "500",
              "600",
              "700",
              "800",
              "900",
            ],
            italic: true,
          },
        ],
      },
    }),

    Styles({
      // Options
      name: "cv-styles",
      options: {
        factor: 4,
      },
    }),
    presetIcons({
      scale: 1.2,
      warn: true,
      collections: {
        // https://icon-sets.iconify.design/
        mdi: () =>
          import("@iconify-json/mdi/icons.json").then((i) => i.default),
      },
      extraProperties: {
        "font-size": "1.2em",
        display: "inline-block",
        "vertical-align": "middle",
      },
    }),
    typography({
      selectorName: "nyx-text",
      options: {
        test: "test",
      },
    }),
    color({
      selectorName: "nyx-color2",
      options: {
        themes,
        variables,
      },
    }),
  ],
  safelist: [
    "i-mdi-whatsapp",
    "dark:i-mdi-whatsapp",
    "i-material-symbols-phone-enabled-outline",
    "dark:i-material-symbols-phone-enabled",
    "i-material-symbols-mail-outline",
    "dark:i-material-symbols-mail",
    "i-ant-design-linkedin-outlined",
    "dark:i-ant-design-linkedin-filled",
    "i-ant-design-github-outlined",
    "dark:i-ant-design-github-filled",
    "i-clarity-world-line",
    "dark:i-clarity-world-solid",
  ],
});
