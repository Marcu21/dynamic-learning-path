/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
    "./lib/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    container: {
      center: true,
      padding: "32px",
    },
    extend: {
      fontFamily: {
        display: ["Mitr", "sans-serif"],
        sans: ["Inter", "sans-serif"],
      },
      fontSize: {
        'md': '15px',
      },
      colors: {
        /* --- Brand Colors --- */
        primary: "#811CDD",
        "primary-light": "#ECD8FE",
        "primary-dark": "#380A63",
        secondary: "#CE1C5B",
        "secondary-light": "#F8DAE5",
        "secondary-dark": "#770F34",
        accent: "#23CCBE",
        "accent-light": "#D2F8F5",
        "accent-dark": "#00564F",
        /* --- Neutrals --- */
        black: "#0A0A0A",
        neutral: {
          DEFAULT: "#585858",
          dark: "#383838",
          "secondary-light": "#585858",
          secondary: "#C0C0C0",
          "secondary-dark": "#E1E1E1",
          "accent-light": "#F1F1F1",
          accent: "#F8F8F8",
          "accent-dark": "#FEFEFE",
        },
        /* --- Semantic --- */
        alert: { light: "#F9DCDD", DEFAULT: "#CD2027", dark: "#90161B" },
        warning: { light: "#FFF4DD", DEFAULT: "#FDB81E", dark: "#A16207" },
        success: { light: "#DAF2DF", DEFAULT: "#248437", dark: "#14532D" },
        info:    { light: "#D7F5FF", DEFAULT: "#0EA5E9", dark: "#035C8C" },
      },
      spacing: {
        gutter: "32px",
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
  ],
};
