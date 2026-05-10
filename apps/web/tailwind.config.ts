import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#07100f",
        panel: "#101918",
        line: "#263836",
        mint: "#7ee6b8",
        amber: "#f0bd5b",
        signal: "#e86452"
      },
      boxShadow: {
        glow: "0 0 0 1px rgba(126,230,184,0.24), 0 22px 80px rgba(0,0,0,0.42)"
      }
    }
  },
  plugins: []
};

export default config;

