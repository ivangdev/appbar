/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: [
    "./src/**/*.{js,ts,jsx,tsx}",
    "./app/**/*.{js,ts,jsx,tsx}",
    "./pages/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Tu paleta neutral-retro diseñada juntos
        background: "#F8F9FA",
        foreground: "#1A1A2E",
        card: "#FFFFFF",
        primary: "#6B7280",
        muted: "#4A4A5A",
        accent: "#D4A853",
        success: "#65A30D",
        error: "#B91C1C",
        // Colores de mesa neutral-retro
        free: "#3F51B5",
        occupied: "#E67E22",
        paid: "#7CB340",
        closed: "#9CA3AF",
      },
      fontFamily: {
        display: ["Inter", "system-ui", "sans-serif"],
        mono: ["Roboto Mono", "SF Mono", "ui-monospace", "sans-serif"],
      },
      borderRadius: {
        sm: "calc(var(--radius) - 2px)",
        md: "calc(var(--radius))",
        lg: "calc(var(--radius) + 2px)",
        xl: "calc(var(--radius) + 4px)",
      },
    },
  },
}
