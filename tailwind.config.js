
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0b0f14",
        card: "#101722",
        ink: "#e6edf3",
        muted: "#8aa0b2",
        brand: {
          DEFAULT: "#4ea2ff",
          600: "#3182ce"
        },
        ok: "#18b26b",
        err: "#e85d75"
      },
      boxShadow: {
        soft: "0 10px 30px rgba(0,0,0,.25)"
      },
      borderRadius: {
        xl2: "1.25rem"
      }
    },
  },
  plugins: [],
}
