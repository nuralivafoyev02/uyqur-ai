import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0f172a",
        steel: "#1e293b",
        line: "#d7dee8",
        mist: "#f5f7fb",
        accent: "#0f766e",
        warn: "#b45309",
        danger: "#b91c1c"
      },
      boxShadow: {
        panel: "0 14px 40px rgba(15, 23, 42, 0.08)"
      }
    }
  },
  plugins: []
} satisfies Config;
