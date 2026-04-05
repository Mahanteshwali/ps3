/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        dark: {
          900: '#0a0a0a',
          800: '#111111',
          700: '#1a1a1a',
        },
        red: {
          500: '#ff3333',
          400: '#ff4d4d',
        },
        neon: {
          green: '#00ff41',
        }
      },
      fontFamily: {
        mono: ['"Fira Code"', '"JetBrains Mono"', 'monospace'],
      }
    },
  },
  plugins: [],
}
