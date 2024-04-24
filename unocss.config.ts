// unocss.config.ts
import { defineConfig } from "unocss";
import Styles from "./src/presets/styles";

export default defineConfig({
  presets: [
    Styles({
      // Options
      name: "cv-styles",
      options: {
        factor: 4,
      },
    }),
  ],
});
