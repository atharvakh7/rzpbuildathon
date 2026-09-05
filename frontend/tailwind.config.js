/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          500: '#0D94FB', // Razorpay action blue
          600: '#0284c7',
          700: '#0369a1',
        },
        rzp: {
          blue: '#0D94FB', // Razorpay Core Blue
          blueDark: '#0B72C7',
          prussian: '#072654', // Razorpay Dark Prussian Blue
          deep: '#0B1528', // Background deep navy
          surface: '#111D33', // Card surface
          surfaceLighter: '#172744',
          border: '#1E3256',
          borderLight: '#2A436E',
          textMuted: '#879BBB',
          success: '#10B981',
          warning: '#F59E0B',
          danger: '#EF4444',
        },
        fintech: {
          dark: '#0B1528',
          card: '#111D33',
          border: '#1E3256',
          muted: '#879BBB',
          accent: '#0D94FB',
          danger: '#EF4444',
          warning: '#F59E0B',
          success: '#10B981',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Menlo', 'monospace'],
      }
    },
  },
  plugins: [],
}
