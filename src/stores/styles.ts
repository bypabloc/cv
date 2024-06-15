import { atom } from "nanostores";

const getInitial = () => {
  if (typeof window !== "undefined") {
    const styles = localStorage.getItem("styles");
    const isDarkMode =
      window.matchMedia &&
      window.matchMedia("(prefers-color-scheme: dark)").matches;
    let stylesObj = {
      isDarkMode,
    };
    if (styles) {
      try {
        stylesObj = JSON.parse(styles) || {
          isDarkMode,
        };
      } catch (e) {
        stylesObj = {
          isDarkMode,
        };
      }
    }

    if (stylesObj.isDarkMode) {
      document.body.classList.add("dark");
      document.body.classList.remove("light");
    } else {
      document.body.classList.remove("dark");
      document.body.classList.add("light");
    }

    return stylesObj;
  }
  return {};
};

export const styles = atom(getInitial());

const setValueLocalStorage = (key, value) => {
  if (typeof window !== "undefined") {
    const styles = localStorage.getItem("styles");
    let stylesObj = {};
    if (styles) {
      try {
        stylesObj = JSON.parse(styles) || {};
      } catch (e) {
        stylesObj = {};
      }
    }
    stylesObj[key] = value;
    localStorage.setItem("styles", JSON.stringify(stylesObj));
  }
};

export const toggleMode = () => {
  const currentStyles = styles.get();
  const isDarkMode = !currentStyles.isDarkMode;
  styles.set({
    ...currentStyles,
    isDarkMode,
  });
  if (typeof window !== "undefined") {
    if (isDarkMode) {
      document.body.classList.add("dark");
      document.body.classList.remove("light");
    } else {
      document.body.classList.remove("dark");
      document.body.classList.add("light");
    }
    setValueLocalStorage("isDarkMode", isDarkMode);
  }
};

export const setMode = (mode) => {
  styles.set({
    ...styles.get(),
    isDarkMode: mode,
  });
  if (typeof window !== "undefined") {
    if (mode) {
      document.body.classList.add("dark");
      document.body.classList.remove("light");
    } else {
      document.body.classList.remove("dark");
      document.body.classList.add("light");
    }
    setValueLocalStorage("isDarkMode", mode);
  }
};

export const getMode = () => {
  return !!styles.get().isDarkMode;
};
