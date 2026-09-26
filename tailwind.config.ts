import type { Config } from "tailwindcss";

export default {
  content: ["./desktop/index.html", "./desktop/src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "#080b10",
        panel: "#10161f",
        accent: "#67e8f9",
      },
    },
  },
  plugins: [],
} satisfies Config;
