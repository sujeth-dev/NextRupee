import type { Config } from "tailwindcss";

// Design tokens from design-guide/NextRupee-Design-System.html — single source of truth.
const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        indigo: {
          100: "#EEECFB",
          300: "#B7B0F0",
          600: "#4338CA",
          700: "#372FA6",
        },
        gold: { signal: "#9C7A2E" }, // gold-engine context ONLY
        ink: {
          DEFAULT: "#0B0D12",
          2: "#4B5163",
          3: "#8A8F9C",
        },
        border: {
          DEFAULT: "#E4E6EB",
          strong: "#D3D6DD",
        },
        surface: { 2: "#F5F6F8" },
        success: { DEFAULT: "#15803D", bg: "#E7F6EC" },
        warning: { DEFAULT: "#B45309", bg: "#FDF0DE" },
        error: { DEFAULT: "#B42318", bg: "#FCEAE8" },
      },
      fontFamily: {
        display: ["Space Grotesk", "system-ui", "sans-serif"],
        sans: ["IBM Plex Sans", "system-ui", "sans-serif"],
        mono: ["IBM Plex Mono", "ui-monospace", "monospace"],
      },
      borderRadius: {
        chip: "8px",
        card: "12px",
        panel: "16px",
        modal: "24px",
      },
      boxShadow: {
        sm: "0 1px 2px rgba(11,13,18,.06)",
        md: "0 4px 16px rgba(11,13,18,.08)",
        lg: "0 12px 32px rgba(11,13,18,.10)",
      },
      maxWidth: { grid: "1280px" },
    },
  },
  plugins: [],
};

export default config;
