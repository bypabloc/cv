import { defineConfig } from "unlighthouse";

export default defineConfig({
  site: "http://localhost:3000",
  debug: true,
  puppeteerOptions: {
    executablePath: "/usr/bin/google-chrome", // Especifica la ruta correcta a google-chrome
    // headless: true,
    // ignoreHTTPSErrors: true,
    // timeout: 0,
    // protocolTimeout: 0,
    // defaultViewport: {
    //   mobile: true,
    //   width: 412,
    //   height: 823,
    //   deviceScaleFactor: 1.75,
    //   disabled: false,
    // },
  },
  // otras configuraciones...
});
