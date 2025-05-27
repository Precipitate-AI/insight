import type { Config } from 'tailwindcss'

const config: Config = { // Added type Config for TS
  content: ["./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        'precipitate-blue': '#1A66FF',
        'precipitate-dark': '#0A101D',
        'precipitate-light': '#F5F6FA'
      },
    },
  },
  plugins: [],
}
export default config; // Use ES6 export for .ts files
