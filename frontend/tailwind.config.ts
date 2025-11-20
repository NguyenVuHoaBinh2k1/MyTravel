import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Vietnamese theme colors
        primary: {
          50: "#fef3f2",
          100: "#fee4e2",
          200: "#fececa",
          300: "#fcaba4",
          400: "#f87a6f",
          500: "#ef5042",
          600: "#dc3324",
          700: "#b9271a",
          800: "#992419",
          900: "#7f241c",
          950: "#450e09",
        },
        secondary: {
          50: "#f7f8f8",
          100: "#eeeef0",
          200: "#d9dade",
          300: "#b8bac1",
          400: "#91949f",
          500: "#737683",
          600: "#5d5f6a",
          700: "#4c4d57",
          800: "#41424a",
          900: "#393a40",
          950: "#26262a",
        },
        accent: {
          50: "#fefce8",
          100: "#fffac2",
          200: "#fff289",
          300: "#ffe445",
          400: "#fdd013",
          500: "#ecb806",
          600: "#cc8e02",
          700: "#a36405",
          800: "#864e0d",
          900: "#724011",
          950: "#432105",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
