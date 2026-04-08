module.exports = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        beige: {
          50:  '#FDFAF4',
          100: '#F5F0E8',
          200: '#EDE5D5',
          300: '#DDD3BC',
        },
        forest: {
          50:  '#EBF3EE',
          100: '#C9DFD0',
          200: '#8DB596',
          300: '#5C9A6A',
          400: '#4A7C59',
          500: '#2D5A3D',
          600: '#1E3D29',
        },
        sage: '#8DB596',
        bark:  '#6B5744',
      },
      fontFamily: {
        display: ['"Playfair Display"', 'serif'],
        body:    ['"DM Sans"', 'sans-serif'],
      },
      borderRadius: {
        xl2: '1.25rem',
        xl3: '1.5rem',
      },
      boxShadow: {
        card: '0 2px 16px 0 rgba(74,124,89,0.08)',
        hover: '0 4px 24px 0 rgba(74,124,89,0.15)',
      }
    },
  },
  plugins: [],
}
