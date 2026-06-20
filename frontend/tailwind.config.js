/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          light: '#818cf8',
          DEFAULT: '#6366f1',
          dark: '#4f46e5',
        },
        secondary: {
          light: '#f472b6',
          DEFAULT: '#ec4899',
          dark: '#db2777',
        },
        dark: {
          900: '#0f172a',
          800: '#1e293b',
          700: '#334155',
        }
      },
      backdropBlur: {
        xs: '2px',
      }
    },
  },
  plugins: [],
}
