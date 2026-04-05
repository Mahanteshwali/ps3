/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        dark: '#080809',
        surface: '#0e0e10',
        cyan: '#00d4c8',
        red: '#e03535',
        amber: '#d4921a',
      },
      fontFamily: {
        display: ['Syne', 'sans-serif'],
        mono: ['"Space Mono"', 'monospace'],
      }
    },
  },
  plugins: [],
}
