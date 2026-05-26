/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ['"Clash Display"', 'Syne', 'Poppins', 'sans-serif'],
        body: ['Inter', 'Geist', 'sans-serif'],
      },
      colors: {
        accent: {
          DEFAULT: '#FF5A0A',
          hover: '#E04D00',
          light: '#FFF4ED',
        },
        surface: {
          DEFAULT: '#FFFFFF',
          muted: '#FAFAFA',
          border: '#E5E5E5',
        },
      },
      boxShadow: {
        'float': '0 8px 32px rgba(0,0,0,0.12)',
        'float-lg': '0 16px 48px rgba(0,0,0,0.16)',
        'float-xl': '0 24px 64px rgba(0,0,0,0.20)',
        'button': '0 6px 24px rgba(255,90,10,0.35)',
        'button-hover': '0 12px 36px rgba(255,90,10,0.50)',
        'card': '0 4px 20px rgba(0,0,0,0.08)',
        'card-hover': '0 12px 40px rgba(0,0,0,0.15)',
        'badge': '0 4px 12px rgba(0,0,0,0.10)',
      },
    },
  },
  plugins: [],
};